"""
HealthLang AI Workflow

English-first medical reasoning with optional MCP and RAG context.
Translation endpoints remain available but are not used by the chatbot.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, TypedDict, Tuple

import httpx
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.utils.logger import get_logger
from app.core.exceptions import MCPClientError


from app.services.mcp_client_http import (
    fda_drug_lookup,
    pubmed_search,
    health_topics,
    clinical_trials_search,
    medical_terminology_lookup,
    medrxiv_search,
    calculate_bmi,
    ncbi_bookshelf_search,
    extract_dicom_metadata,
    usage_analytics,
)

# Optional RAG imports (fail-safe if dependencies not available)
try:
    from app.services.rag.embeddings import EmbeddingService
    from app.services.rag.vector_store import VectorStore
    from app.services.rag.document_processor import DocumentProcessor
    from app.services.rag.retriever import RAGRetriever, RetrievalRequest
    from app.services.rag.tavily_knowledge import TavilyKnowledgeService
    RAG_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    RAG_AVAILABLE = False

logger = get_logger(__name__)

# State definition for the workflow


class WorkflowState(TypedDict):
    """State for the HealthLang workflow"""
    messages: List[Any]
    original_query: str
    detected_language: str
    translated_query: Optional[str]
    medical_response: Optional[str]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class HealthLangWorkflow:
    """Main workflow orchestrator for HealthLang AI"""

    def __init__(self):
        # No MCP client instance needed for HTTP mode
        # RAG components are initialized lazily and reused for performance
        self._rag_initialized: bool = False
        self._embedding_service = None
        self._vector_store = None
        self._document_processor = None
        self._retriever = None
        self._general_knowledge_rag = None
        
    async def _detect_language(self, _query: str) -> str:
        """Language detection is disabled; always use English."""
        return "en"
    
    def _should_translate(self, _detected_language: str) -> bool:
        """Translation is disabled in the chatbot flow."""
        return False
    
    async def _translate_to_english(self, query: str) -> str:
        """No-op: Chatbot does not auto-translate now."""
        return query
    
    async def _medical_reasoning(
        self,
        query: str,
        mcp_tools: List[Dict],
        context_text: str = "",
    ) -> str:
        """
        Perform medical reasoning on the query using provided tools and
        optional context.
        """
        # Call medical reasoning service
        try:
            response = await self._call_medical_reasoning(
                query,
                mcp_tools,
                context_text,
            )
            logger.info("Medical reasoning completed.")
            return response
        except Exception as e:
            logger.error(f"Medical reasoning failed: {e}")
            return (
                "Sorry, I encountered an error while processing your medical "
                f"query: {str(e)}"
            )

    async def _translate_response(
        self,
        response: str,
        _target_language: str,
    ) -> str:
        """No-op: Responses remain in English."""
        return response
    
    def _is_medical_query(self, query: str) -> bool:
        """Detect if a query is medical based ONLY on the original query."""
        query_lower = query.lower().strip()
        
        # Non-medical query patterns (explicit exclusions)
        non_medical_patterns = [
            # Greetings and social
            "hi", "hello", "hey", "hi there", "hello there",
            "good morning", "good afternoon", "good evening",
            "how are you", "how's it going", "what's up",
            "my name is", "i am", "i'm", "nice to meet",
            "thanks", "thank you", "goodbye", "bye", "see you",
            # Entertainment requests
            "tell me a joke", "joke", "funny", "laugh", "humor",
            "story", "tell me about", "what do you think",
            "can you help me", "can you tell me",
            # General conversation
            "how old are you", "what are you", "who are you",
            "what can you do", "how do you work"
        ]
        
        # If query matches non-medical patterns, definitely not medical
        for pattern in non_medical_patterns:
            if pattern in query_lower:
                return False
        
        # Medical keywords that indicate health-related intent
        medical_indicators = [
            # Conditions/diseases
            "diabetes", "hypertension", "asthma", "depression", "anxiety",
            "cholesterol", "obesity", "malaria", "tuberculosis", "anemia",
            "covid", "coronavirus", "ulcer", "cancer", "disease", "condition",
            "syndrome", "infection", "virus", "bacteria",
            # Symptoms
            "symptom", "pain", "ache", "fever", "nausea", "dizzy", "tired",
            "headache", "cough", "rash", "swelling", "bleeding", "vomiting",
            "diarrhea", "constipation", "shortness of breath",
            # Medical terms
            "diagnos", "treatment", "medication", "medicine", "drug", "dose",
            "prescription", "doctor", "physician", "hospital", "clinic",
            "blood pressure", "blood sugar", "cholesterol", "a1c", "lab",
            "test", "screening", "biopsy", "surgery", "therapy",
            # Health-related questions
            "medical advice", "sick", "illness", "injury", "hurt",
            "what should i do about", "health problem", "feel unwell",
            "not feeling well", "something wrong with"
        ]
                
        # Check ONLY the original query for medical indicators
        return any(
            indicator in query_lower for indicator in medical_indicators
        )

    def _build_contextual_followup(
        self,
        original_query: str,
        response: str,
    ) -> str:
        """Generate a context-aware follow-up prompt.

        Rules:
        - Only generate medical follow-ups for medical queries
        - One concise question that advances the conversation.
        - Tailor to detected condition/intent (symptoms, diagnosis,
          lifestyle, meds, labs, region).
        - Offer Pidgin ONLY if the user asked for it (contains 'pidgin').
        """
        # First check if this is actually a medical query
        if not self._is_medical_query(original_query):
            # For non-medical queries, provide general assistance follow-up
            return "How else can I help you today?"
            
        oq = (original_query or "").lower()
        rsp = (response or "").lower()

        # Simple topic extraction from query or response
        topics = [
            "diabetes", "hypertension", "asthma", "depression",
            "anxiety", "cholesterol", "obesity", "malaria",
            "tuberculosis", "anemia", "covid", "ulcer",
        ]
        topic = next((t for t in topics if t in oq or t in rsp), None)

        # Intent detection via keywords
        def has(words):
            return (
                any(w in oq for w in words)
                or any(w in rsp for w in words)
            )

        is_symptoms = has(["symptom", "sign", "how do i know", "feel"])
        is_diagnosis = has([
            "diagnos", "test", "screen", "a1c", "bp",
            "blood pressure", "fasting glucose", "reading",
        ])
        is_lifestyle = has([
            "diet", "exercise", "lifestyle", "food", "meal",
            "weight", "sleep", "salt", "sodium",
        ])
        is_medication = has([
            "drug", "med", "dose", "dosing", "insulin",
            "metformin", "statin", "ace inhibitor",
            "side effect", "interaction",
        ])
        is_lab = has([
            "lab", "result", "range", "units", "normal",
            "abnormal",
        ])
        is_preg_child = has([
            "pregnan", "child", "kid", "baby", "pediatric",
            "breastfeed",
        ])
        wants_region = has([
            "nigeria", "lagos", "abuja", "africa", "west africa",
            "ghana", "kenya", "europe", "uk", "united kingdom",
            "germany", "france", "spain",
        ])
        asked_pidgin = "pidgin" in oq

        # Build a tailored follow-up
        if is_symptoms:
            return (
                f"Would you like a quick checklist of key "
                f"{topic or 'condition'} symptoms and red flags, "
                "plus when to get tested?"
            )
        if is_diagnosis:
            return (
                f"Do you want me to outline the common tests for "
                f"{topic or 'this condition'} (what they measure, "
                "normal ranges, and next steps)?"
            )
        if is_lifestyle:
            return (
                f"Should I draft a simple 1–2 week {topic or 'health'} "
                "plan (diet, activity, and monitoring) you can review "
                "with your clinician?"
            )
        if is_medication:
            return (
                "Would a short overview of medication options, common "
                "side effects, and interactions help?"
            )
        if is_lab:
            return (
                "Want a plain-English guide to interpreting these lab "
                "values and when to recheck?"
            )
        if is_preg_child:
            return (
                "Should I highlight considerations specific to "
                "pregnancy/children for this topic?"
            )
        if wants_region and topic:
            return (
                f"Would you like suggestions for clinics or programs in "
                f"your area for {topic} care?"
            )

        # Default: advance the conversation with a tailored next step
        fallback = (
            f"Would you like me to tailor next steps for {topic} to your "
            "goals and constraints?"
        ) if topic else (
            "Should I tailor the next steps to your goals and "
            "constraints (time, budget, access)?"
        )
        # Add Pidgin offer only if asked
        if asked_pidgin:
            fallback += " If you want, I can explain in Nigerian Pidgin."
        return fallback

    async def _format_response(  # noqa: D401
        self,
        original_query: str,
        response: str,
        target_language: str,
    ) -> str:
        """Return response with a small educational disclaimer if medical."""
        _ = target_language  # mark param as used
        
        # Only add medical disclaimer for medical queries
        if not self._is_medical_query(original_query):
            return response
            
        lower = response.lower()
        already_has_disclaimer = (
            "not a diagnosis" in lower or
            "licensed clinician" in lower or
            "emergency" in lower and "seek" in lower
        )
        if already_has_disclaimer:
            return response
        disclaimer = (
            "\n\nNote: This is educational information, not a medical "
            "diagnosis. For personal advice, please consult a licensed "
            "clinician."
        )
        return response + disclaimer

    async def _gather_context(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Collect optional context from RAG and MCP tools to assist the LLM.

        Returns a tuple of (context_text, context_meta). Failures are swallowed
        and simply produce empty context.
        """
        context_parts: List[str] = []
        meta: Dict[str, Any] = {
            "rag_used": False,
            "mcp_used": False,
            "sources": [],
        }

        # Initialize RAG if needed
        logger.info(
            f"RAG check: RAG_ENABLED={settings.RAG_ENABLED}, "
            f"RAG_AVAILABLE={RAG_AVAILABLE}"
        )
        if settings.RAG_ENABLED and RAG_AVAILABLE:
            try:
                logger.info("Attempting to ensure RAG initialized...")
                await self._ensure_rag_initialized()
                logger.info(
                    f"RAG initialized. general_knowledge_rag: "
                    f"{self._general_knowledge_rag is not None}"
                )
            except Exception as e:
                logger.warning(f"RAG initialization failed: {e}")
        
        # Try medical RAG for medical queries
        if settings.RAG_ENABLED and RAG_AVAILABLE:
            try:
                await self._ensure_rag_initialized()
                if not self._retriever:
                    raise RuntimeError("RAG retriever unavailable")
                rag_resp = await self._retriever.retrieve(
                    RetrievalRequest(
                        query=query,
                        top_k=settings.MAX_RETRIEVAL_DOCS,
                        similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    )
                )
                if rag_resp and rag_resp.documents:
                    meta["rag_used"] = True
                    top_snippets = []
                    max_docs = settings.MAX_RETRIEVAL_DOCS
                    for doc in rag_resp.documents[:max_docs]:
                        snippet = doc.document.content[:500]
                        src = (
                            doc.document.source
                            or doc.document.metadata.get("source", "unknown")
                        )
                        title = (
                            doc.document.metadata.get("title")
                            or (src if isinstance(src, str) else "RAG Source")
                        )
                        authors_md = (
                            doc.document.metadata.get("authors")
                            or doc.document.metadata.get("author")
                        )
                        year_md = (
                            doc.document.metadata.get("year")
                            or doc.document.metadata.get("publication_year")
                        )
                        top_snippets.append(
                            f"- Source: {src}\n  Excerpt: {snippet}"
                        )
                        # Track sources for neat referencing
                        meta["sources"].append({
                            "type": "rag",
                            "title": title,
                            "url": (
                                src
                                if isinstance(src, str)
                                and src.startswith("http")
                                else None
                            ),
                            "authors": authors_md,
                            "year": year_md,
                        })
                    context_parts.append(
                        "RAG Context:\n" + "\n".join(top_snippets)
                    )
            except Exception as e:
                # Swallow all RAG errors to avoid failing the whole query
                logger.warning(f"RAG context unavailable: {e}")

        # Then try lightweight MCP lookups
        try:
            def _extract_items(obj: Any) -> List[Dict[str, Any]]:
                if isinstance(obj, list):
                    return obj
                if not isinstance(obj, dict):
                    return []
                for key in [
                    "data", "results", "items", "entries", "articles",
                    "records", "papers", "topics"
                ]:
                    val = obj.get(key)
                    if isinstance(val, list) and val:
                        return val
                return []
            mcp_snippets = []
            # Health topics
            try:
                ht = await health_topics(query, max_results=5)
                items = _extract_items(ht)
                if isinstance(items, list) and items:
                    meta["mcp_used"] = True
                    for it in items[:3]:
                        title = it.get("title") or it.get("name") or ""
                        summary = (
                            it.get("summary") or it.get("description") or ""
                        )
                        mcp_snippets.append(
                            f"- {title}: {summary[:300]}"
                        )
                        link = (
                            it.get("url") or it.get("link") or it.get("source")
                        )
                        meta["sources"].append({
                            "type": "health_topic",
                            "title": title or "Health Topic",
                            "url": (
                                link
                                if isinstance(link, str)
                                and link.startswith("http")
                                else None
                            ),
                            "source": "MCP:health-topics",
                            "authors": None,
                            "year": None,
                        })
            except (
                httpx.HTTPError,
                MCPClientError,
                ValueError,
                KeyError,
            ) as e:
                logger.debug(f"health_topics failed: {e}")
            # PubMed search
            try:
                pm = await pubmed_search(query, max_results=3, date_range=5)
                items = _extract_items(pm)
                if isinstance(items, list) and items:
                    meta["mcp_used"] = True
                    for it in items[:3]:
                        title = it.get("title") or it.get("name") or ""
                        url = it.get("url") or it.get("link") or ""
                        mcp_snippets.append(
                            f"- PubMed: {title} ({url})"
                        )
                        authors = it.get("authors")
                        year = (
                            it.get("year")
                            or it.get("publication_year")
                            or it.get("date")
                        )
                        meta["sources"].append({
                            "type": "pubmed",
                            "title": title or "PubMed article",
                            "url": (
                                url
                                if isinstance(url, str)
                                and url.startswith("http")
                                else None
                            ),
                            "source": "PubMed",
                            "authors": authors,
                            "year": year,
                        })
            except (
                httpx.HTTPError,
                MCPClientError,
                ValueError,
                KeyError,
            ) as e:
                logger.debug(f"pubmed_search failed: {e}")

            if mcp_snippets:
                context_parts.append(
                    "MCP Findings:\n" + "\n".join(mcp_snippets)
                )
        except (httpx.HTTPError, MCPClientError, ValueError, KeyError) as e:
            logger.warning(f"MCP context unavailable: {e}")

        # Add Tavily general knowledge after MCP (for enhanced context)
        if (settings.RAG_ENABLED and RAG_AVAILABLE and
                self._general_knowledge_rag):
            try:
                logger.info("Attempting Tavily general knowledge retrieval")
                gk_resp = await self._general_knowledge_rag.retrieve_knowledge(
                    query)
                sources_count = len(gk_resp["sources"]) if gk_resp else 0
                logger.info("Tavily knowledge response: %s, sources: %d",
                            gk_resp is not None, sources_count)
                if gk_resp and gk_resp.get("sources"):
                    meta["rag_used"] = True
                    meta["general_knowledge_used"] = True
                    tavily_snippets = []
                    
                    # Add Tavily answer if available
                    if gk_resp.get("answer"):
                        context_parts.append(
                            f"Current Information:\n{gk_resp['answer']}"
                        )
                    
                    # Add sources and content
                    for source in gk_resp["sources"][:3]:
                        snippet = source.get("content", "")[:400]
                        title = source.get("title", "Knowledge Source")
                        url = source.get("url", "")
                        
                        if snippet:
                            tavily_snippets.append(f"- {title}: {snippet}")
                        
                        meta["sources"].append({
                            "type": "web",
                            "title": title,
                            "url": url if url else None,
                            "source": "Tavily Search",
                            "authors": None,
                            "year": None
                        })
                    
                    if tavily_snippets:
                        context_parts.append(
                            "Additional Context:\n" +
                            "\n".join(tavily_snippets)
                        )
                    
                    logger.info(
                        "Added Tavily knowledge context with %d sources",
                        len(gk_resp["sources"])
                    )
                
            except Exception as e:
                logger.warning(
                    f"Tavily general knowledge retrieval failed: {e}"
                )

        # If we have no sources at all, add a generic curated fallback
        if not meta["sources"]:
            meta["sources"].append({
                "type": "guideline",
                "title": "World Health Organization: Diabetes",
                "url": "https://www.who.int/health-topics/diabetes",
                "source": "WHO",
                "authors": None,
                "year": None,
            })

        context_text = "\n\n".join(context_parts).strip()
        return context_text, meta

    def _append_followups_and_sources(
        self,
        original_query: str,
        response: str,
        context_meta: Dict[str, Any],
    ) -> str:
        """Ensure a friendly opinion/follow-up and append neat sources.

        - Adds a one-sentence "My take" opinion if not already present.
        - Adds one contextual follow-up (varying among simpler explanation,
          Nigerian Pidgin on request, next steps, or care options by region),
          without auto-translation.
        - Appends a Sources section (information-prominent style).
        """
        out = response.strip()
        low = out.lower()

        # Add a brief opinion if missing (only for medical queries)
        is_medical = self._is_medical_query(original_query)
        if "my take:" not in low and is_medical:
            out += (
                "\n\nMy take: Based on current medical guidance, it's "
                "best to monitor symptoms, reduce risk factors, and speak "
                "with a clinician for personalized advice."
            )

        # Add one contextual follow-up (topic/intent aware;
        # no auto-Pidgin unless asked)
        followup = self._build_contextual_followup(original_query, out)
        # Only append if we didn't already add something similar
        if not any(p in low for p in [
            "simpler", "checklist", "clinics", "interpret", "plan",
            "tailor", "next steps", "when to"
        ]):
            out += "\n\n" + followup

        # Append sources if available and not present (medical only)
        sources = context_meta.get("sources", [])
        if sources and "sources:" not in low and is_medical:
            out += "\n\nSources:\n"
            # Limit to top 5 to keep tidy
            for s in sources[:5]:
                title = s.get("title") or s.get("source") or "Reference"
                url = s.get("url")
                src = s.get("source") or ""
                authors = s.get("authors")
                year = s.get("year")
                # Build mixed style: title+link (info prominent)
                # and author/year
                if isinstance(authors, list) and authors:
                    first = str(authors[0])
                    # Try to keep surname if formatted "Surname, Name"
                    first_short = first.split(",")[0].strip() or first
                    author_str = (
                        f"{first_short} et al."
                        if len(authors) > 1 else first_short
                    )
                elif isinstance(authors, str) and authors:
                    first_short = authors.split(",")[0].strip()
                    author_str = first_short
                else:
                    author_str = None

                details = []
                if author_str:
                    details.append(author_str)
                if year:
                    details.append(str(year))
                mixed_tail = (
                    f" — {', '.join(details)}" if details else ""
                )
                if url:
                    out += (
                        f"- [{title}]({url}) — {src}{mixed_tail}\n"
                    )
                else:
                    out += f"- {title} — {src}{mixed_tail}\n"

        return out

    async def _call_translation_service(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Call the translation service"""
        try:
            # Import here to avoid circular imports
            from app.services.translation.translator import TranslationService

            translator = TranslationService()
            await translator.initialize()

            result = await translator.translate(
                text=text,
                source_language=source_language,
                target_language=target_language
            )

            return result.translated_text

        except (RuntimeError, ValueError) as e:
            logger.error(f"Translation service call failed: {e}")
            raise
    
    async def _call_medical_reasoning(
        self,
        query: str,
        mcp_tools: List[Dict],
        context_text: str = "",
    ) -> str:
        """Call reasoning via XAI Grok or Groq with MCP tools.

        Adds a global, friendly chatbot system prompt and extra medical-safety
        guidance when the topic is health-related.
        """
        try:
            # Choose primary provider based on configuration
            provider = (settings.MEDICAL_MODEL_PROVIDER or "groq").lower()
            medical_domain_prompt = (
                "When the user's intent is medical, follow medical-safety "
                "best practices: avoid diagnosis/prescription, be "
                "educational, add a brief disclaimer, and recommend seeing "
                "a clinician for personal advice. If referring to external "
                "knowledge, describe which MCP tool you would use and why."
            )
            # Primary path selection
            if provider == "groq":
                return await self._call_groq_medical_reasoning(
                    query,
                    mcp_tools,
                    context_text,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.XAI_GROK_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": (
                                f"Bearer {settings.XAI_GROK_API_KEY}"
                            ),
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": settings.MEDICAL_MODEL_NAME,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": settings.SYSTEM_PROMPT,
                                },
                                {
                                    "role": "system",
                                    "content": (
                                        "If helpful, consult the provided "
                                        "context from RAG/MCP."
                                    ),
                                },
                                {
                                    "role": "system",
                                    "content": (
                                        "Available medical tools: "
                                        + json.dumps(mcp_tools, indent=2)
                                    ),
                                },
                                {
                                    "role": "system",
                                    "content": medical_domain_prompt,
                                },
                                {
                                    "role": "system",
                                    "content": (
                                        "End with 'My take' (non-"
                                        "diagnostic). Offer Nigerian "
                                        "Pidgin only if the user explicitly "
                                        "asked. Do not translate unless the "
                                        "user agrees."
                                    ),
                                },
                                {
                                    "role": "system",
                                    "content": (
                                        "When citing, use mixed style: "
                                        "include title + link and author/"
                                        "year if available."
                                    ),
                                },
                                *(
                                    [
                                        {
                                            "role": "system",
                                            "content": (
                                                f"Context:\n{context_text}"
                                            ),
                                        }
                                    ]
                                    if context_text
                                    else []
                                ),
                                {"role": "user", "content": query},
                            ],
                            "temperature": settings.TEMPERATURE,
                            "max_tokens": settings.MAX_TOKENS,
                            "top_p": settings.TOP_P,
                        },
                        timeout=settings.LLM_TIMEOUT,
                    )
                    response.raise_for_status()
                    return response.json()[
                        "choices"
                    ][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.warning(
                "LLM primary provider status %s; trying fallback.",
                e.response.status_code,
            )
            # Fallback to the other provider only if keys are present
            if provider != "groq" and settings.GROQ_API_KEY:
                return await self._call_groq_medical_reasoning(
                    query, mcp_tools, context_text
                )
            if provider == "groq" and settings.XAI_GROK_API_KEY:
                # Try XAI if configured
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{settings.XAI_GROK_BASE_URL}/chat/completions",
                            headers={
                                "Authorization": (
                                    f"Bearer {settings.XAI_GROK_API_KEY}"
                                ),
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": settings.MEDICAL_MODEL_NAME,
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": settings.SYSTEM_PROMPT,
                                    },
                                    {"role": "user", "content": query},
                                ],
                                "temperature": settings.TEMPERATURE,
                                "max_tokens": settings.MAX_TOKENS,
                            },
                            timeout=settings.LLM_TIMEOUT,
                        )
                        response.raise_for_status()
                        return response.json()[
                            "choices"
                        ][0]["message"]["content"]
                except (
                    httpx.HTTPError,
                    json.JSONDecodeError,
                    KeyError,
                    TimeoutError,
                    ValueError,
                ) as ee:
                    logger.warning(f"Fallback XAI failed: {ee}")
            raise
        except (
            httpx.RequestError,
            json.JSONDecodeError,
            KeyError,
            TimeoutError,
        ) as e:
            logger.warning(
                f"LLM primary provider failed, attempting fallback: {e}"
            )
            if provider != "groq" and settings.GROQ_API_KEY:
                return await self._call_groq_medical_reasoning(
                    query, mcp_tools, context_text
                )
            # As last resort, return error message
            raise

    async def _call_groq_medical_reasoning(
        self,
        query: str,
        mcp_tools: List[Dict],
        context_text: str = "",
    ) -> str:
        """Fallback reasoning using Groq API with the global system prompt."""
        try:
            from langchain_groq import ChatGroq

            llm = ChatGroq(
                model=settings.GROQ_MODEL,
                groq_api_key=settings.GROQ_API_KEY,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            medical_domain_prompt = (
                "When the user's intent is medical, follow medical-safety "
                "best practices: avoid diagnosis/prescription, be "
                "educational, add a brief disclaimer, and recommend seeing "
                "a clinician for personal advice. If referring to external "
                "knowledge, describe which MCP tool you would use and why."
            )

            msgs = [
                SystemMessage(content=settings.SYSTEM_PROMPT),
                SystemMessage(content=(
                    "Available medical tools: "
                    + json.dumps(mcp_tools, indent=2)
                )),
                SystemMessage(content=medical_domain_prompt),
                SystemMessage(content=(
                    "End with 'My take' (non-diagnostic). Offer Nigerian "
                    "Pidgin only if the user explicitly asked. Do not "
                    "translate unless the user agrees."
                )),
                SystemMessage(content=(
                    "When citing, use mixed style: include title+link and "
                    "author/year if available."
                )),
            ]
            if context_text:
                msgs.append(SystemMessage(content=f"Context:\n{context_text}"))
            msgs.append(HumanMessage(content=query))

            response = await llm.ainvoke(msgs)
            return response.content
            
        except Exception as e:
            logger.error(f"Groq medical reasoning failed: {e}")
            return (
                "Sorry, I encountered an error while processing your medical "
                f"query: {str(e)}"
            )

    async def _get_mcp_tools(self) -> List[Dict]:
        """Get available MCP tools (returns static list for now)"""
        # You can call usage_analytics or document available tools here
        # if needed
        return [
            {"name": "fda_drug_lookup", "description": "FDA Drug Lookup"},
            {"name": "pubmed_search", "description": "PubMed Search"},
            {"name": "health_topics", "description": "Health Topics"},
            {
                "name": "clinical_trials_search",
                "description": "Clinical Trials Search",
            },
            {
                "name": "medical_terminology_lookup",
                "description": "ICD-10/Medical Terminology Lookup",
            },
            {"name": "medrxiv_search", "description": "medRxiv Search"},
            {"name": "calculate_bmi", "description": "BMI Calculator"},
            {
                "name": "ncbi_bookshelf_search",
                "description": "NCBI Bookshelf Search",
            },
            {
                "name": "extract_dicom_metadata",
                "description": "Extract DICOM Metadata",
            },
            {"name": "usage_analytics", "description": "Usage Analytics"},
        ]

    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool via HTTP client"""
        try:
            if tool_name == "fda_drug_lookup":
                return await fda_drug_lookup(**arguments)
            elif tool_name == "pubmed_search":
                return await pubmed_search(**arguments)
            elif tool_name == "health_topics":
                return await health_topics(**arguments)
            elif tool_name == "clinical_trials_search":
                return await clinical_trials_search(**arguments)
            elif tool_name == "medical_terminology_lookup":
                return await medical_terminology_lookup(**arguments)
            elif tool_name == "medrxiv_search":
                return await medrxiv_search(**arguments)
            elif tool_name == "calculate_bmi":
                return await calculate_bmi(**arguments)
            elif tool_name == "ncbi_bookshelf_search":
                return await ncbi_bookshelf_search(**arguments)
            elif tool_name == "extract_dicom_metadata":
                return await extract_dicom_metadata(**arguments)
            elif tool_name == "usage_analytics":
                return await usage_analytics(**arguments)
            else:
                return {
                    "status": "error",
                    "error_message": f"Tool {tool_name} not available",
                }
        except (httpx.HTTPError, ValueError, KeyError) as e:
            logger.error(f"MCP tool call failed: {e}")
            return {"status": "error", "error_message": str(e)}

    async def initialize(self) -> None:
        """Initialize the workflow (no MCP client needed for HTTP mode)"""
        logger.info(
            "HealthLang workflow initialized successfully (MCP HTTP mode)"
        )
        # Optionally prime RAG so the first request is faster
        if settings.RAG_ENABLED and RAG_AVAILABLE:
            try:
                await self._ensure_rag_initialized()
            except (RuntimeError, ValueError) as e:
                logger.warning(
                    f"RAG pre-initialization failed (will try lazily): {e}"
                )

    async def cleanup(self) -> None:
        """Cleanup resources (no MCP client needed for HTTP mode)"""
        self._rag_initialized = False
        self._embedding_service = None
        self._vector_store = None
        self._document_processor = None
        self._retriever = None

    async def _ensure_rag_initialized(self) -> None:
        """Initialize RAG components once and reuse them."""
        if self._rag_initialized:
            return
        if not (settings.RAG_ENABLED and RAG_AVAILABLE):
            return
        try:
            self._embedding_service = EmbeddingService()
            self._vector_store = VectorStore()
            self._document_processor = DocumentProcessor()
            self._retriever = RAGRetriever(
                self._embedding_service,
                self._vector_store,
                self._document_processor,
            )
            self._general_knowledge_rag = TavilyKnowledgeService(settings)
            self._rag_initialized = True
            logger.info("RAG components initialized")
        except (RuntimeError, ValueError) as e:
            logger.warning(f"Failed to initialize RAG components: {e}")
            self._rag_initialized = False
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a medical query through the complete workflow"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # English-only chatbot flow
            detected_language = "en"

            # Gather optional tool/RAG context
            context_text, context_meta = await self._gather_context(query)

            # Medical reasoning with context
            medical_response = await self._medical_reasoning(
                query,
                await self._get_mcp_tools(),
                context_text,
            )

            # Determine success: if the response carries our error-apology
            # marker, treat as a failure for the success flag.
            ok = True
            if isinstance(medical_response, str) and (
                "Sorry, I encountered an error while processing your medical"
                in medical_response
            ):
                ok = False

            # No translation; just formatting
            formatted_response = await self._format_response(
                query,
                medical_response,
                detected_language,
            )
            # Ensure contextual follow-up and formatted sources are included
            formatted_response = self._append_followups_and_sources(
                query,
                formatted_response,
                context_meta,
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "request_id": f"req_{int(start_time * 1000)}",
                "original_query": query,
                "response": formatted_response,
                "response_markdown": True,
                "render_format": "markdown",
                "processing_time": processing_time,
                "timestamp": asyncio.get_event_loop().time(),
                "metadata": {
                    "original_language": detected_language,
                    "translation_used": False,
                    "rag_used": context_meta.get("rag_used", False),
                    "mcp_used": context_meta.get("mcp_used", False),
                    "processing_steps": 3,
                    "sources": context_meta.get("sources", []),
                    "error": None if ok else "LLM provider error"
                },
                "success": ok,
                "error": None if ok else "LLM provider error"
            }
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Query processing failed: {e}")
            
            return {
                "request_id": f"req_{int(start_time * 1000)}",
                "original_query": query,
                "response": (
                    "Sorry, I encountered an error while processing your "
                    f"query: {str(e)}"
                ),
                "processing_time": processing_time,
                "timestamp": asyncio.get_event_loop().time(),
                "metadata": {
                    "original_language": "unknown",
                    "translation_used": False,
                    "processing_steps": 0,
                    "error": str(e)
                },
                "success": False,
                "error": str(e)
            }
