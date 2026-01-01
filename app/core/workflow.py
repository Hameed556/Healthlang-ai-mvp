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
    
    async def _is_medical_query(self, query: str) -> bool:
        """
        Use Groq LLM to accurately detect if a query is medical-related.
        Falls back to keyword matching if LLM classification fails.
        
        Args:
            query: The user's query to classify
            
        Returns:
            bool: True if the query is medical/health-related, False otherwise
        """
        try:
            # Classification prompt for the LLM
            classification_prompt = (
                "You are a medical query classifier. Your task is to determine "
                "if a question requires medical or health expertise.\n\n"
                "Medical/Health queries include:\n"
                "- Symptoms, diseases, conditions, syndromes\n"
                "- Treatments, medications, therapies, procedures\n"
                "- Diagnoses, medical tests, lab results\n"
                "- Anatomy, physiology, biology related to health\n"
                "- Mental health, psychology, psychiatry\n"
                "- Nutrition for medical conditions, dietary health\n"
                "- Pregnancy, childbirth, pediatric health\n"
                "- Medical advice, health concerns, wellness\n\n"
                "Non-medical queries include:\n"
                "- Greetings, social pleasantries, casual conversation\n"
                "- Jokes, entertainment, stories\n"
                "- General knowledge (current events, sports, politics, history)\n"
                "- Technology, business, education (non-health)\n"
                "- Personal questions about the AI itself\n\n"
                f'Question: "{query}"\n\n'
                "Respond with ONLY \"MEDICAL\" or \"NON-MEDICAL\" - nothing else."
            )
            
            # Use Groq via LLM client
            from app.services.medical.llm_client import LLMClient, LLMProvider
            
            llm_client = LLMClient()
            
            # Use Groq only
            if (hasattr(llm_client, 'clients') and
                    LLMProvider.GROQ in llm_client.clients):
                groq_client = llm_client.clients[LLMProvider.GROQ]
                response = await groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "user", "content": classification_prompt}
                    ],
                    max_tokens=10,
                    temperature=0.0
                )
                classification = response.choices[0].message.content.strip().upper()
            else:
                raise ValueError("Groq client not available")
            
            is_medical = classification == "MEDICAL"
            logger.info(
                f"Groq classified query as: {classification} "
                f"(is_medical: {is_medical})"
            )
            return is_medical
            
        except Exception as e:
            logger.warning(
                f"Groq classification failed ({str(e)}), using fallback keyword matching"
            )
            # Fallback to keyword-based detection
            return self._is_medical_query_keywords(query)
    
    def _is_medical_query_keywords(self, query: str) -> bool:
        """
        Fallback keyword-based medical query detection.
        Used when LLM classification is unavailable.
        
        Args:
            query: The user's query to classify
            
        Returns:
            bool: True if the query appears medical-related based on keywords
        """
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

    async def _build_contextual_followup(
        self,
        original_query: str,
        response: str,
    ) -> str:
        """
        Generate intelligent, context-aware follow-up using LLM.
        Falls back to simple generic response if LLM fails.

        Args:
            original_query: The user's original question
            response: The AI's response to analyze for context

        Returns:
            str: Natural, contextual follow-up question
        """
        # First check if this is actually a medical query
        if not await self._is_medical_query(original_query):
            # For non-medical queries, provide general assistance follow-up
            return "How else can I help you today?"

        try:
            # Build intelligent follow-up prompt for LLM
            followup_prompt = (
                "You are a medical assistant generating natural follow-up "
                "questions.\n\n"
                f"User asked: \"{original_query}\"\n\n"
                f"Your response was: \"{response[:500]}...\"\n\n"
                "Based on this conversation context, generate ONE natural, "
                "helpful follow-up question that:\n"
                "1. Advances the conversation logically\n"
                "2. Addresses potential next steps (symptoms checklist, "
                "tests, lifestyle plan, medication info, lab interpretation, "
                "pregnancy/child considerations, regional resources)\n"
                "3. Is personalized to the specific condition/topic discussed\n"
                "4. Sounds natural and conversational\n"
                "5. If user mentioned 'pidgin' or Nigerian context, offer "
                "translation\n\n"
                "Return ONLY the follow-up question, nothing else. "
                "Keep it under 30 words."
            )

            # Use Groq LLM client
            from app.services.medical.llm_client import LLMClient, LLMProvider

            llm_client = LLMClient()

            # Get intelligent follow-up from Groq
            if (hasattr(llm_client, 'clients') and
                    LLMProvider.GROQ in llm_client.clients):
                groq_client = llm_client.clients[LLMProvider.GROQ]
                llm_response = await groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "user", "content": followup_prompt}
                    ],
                    max_tokens=50,
                    temperature=0.7  # Allow creativity for natural language
                )
                followup = llm_response.choices[0].message.content.strip()
            else:
                raise ValueError("Groq client not available")

            # Clean up the follow-up (remove quotes if LLM added them)
            followup = followup.strip('"\'')

            logger.info(f"Generated contextual follow-up: {followup}")
            return followup

        except Exception as e:
            logger.warning(
                f"LLM follow-up generation failed ({str(e)}), "
                "using fallback"
            )
            # Fallback to simple keyword-based follow-up
            return self._build_keyword_followup(original_query, response)

    def _build_keyword_followup(
        self, original_query: str, response: str
    ) -> str:
        """
        Fallback keyword-based follow-up generation.
        Used when LLM-based generation fails.

        Args:
            original_query: The user's original question
            response: The AI's response

        Returns:
            str: Generic follow-up question
        """
        oq = (original_query or "").lower()
        rsp = (response or "").lower()

        # Simple topic extraction
        topics = [
            "diabetes", "hypertension", "asthma", "depression",
            "anxiety", "cholesterol", "obesity", "malaria",
            "tuberculosis", "anemia", "covid", "ulcer",
        ]
        topic = next((t for t in topics if t in oq or t in rsp), None)

        # Intent detection via keywords
        def has(words):
            return any(w in oq for w in words) or any(w in rsp for w in words)

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
            "metformin", "statin", "side effect", "interaction",
        ])
        is_lab = has(["lab", "result", "range", "units", "normal"])
        is_preg_child = has([
            "pregnan", "child", "kid", "baby", "pediatric", "breastfeed"
        ])
        wants_region = has([
            "nigeria", "lagos", "abuja", "africa", "ghana", "kenya"
        ])
        asked_pidgin = "pidgin" in oq

        # Build a tailored follow-up based on detected intent
        if is_symptoms:
            return (
                f"Would you like a checklist of key {topic or 'condition'} "
                "symptoms and when to get tested?"
            )
        if is_diagnosis:
            return (
                f"Would you like me to outline common tests for "
                f"{topic or 'this condition'}?"
            )
        if is_lifestyle:
            return (
                f"Should I create a simple {topic or 'health'} management "
                "plan you can review with your clinician?"
            )
        if is_medication:
            return (
                "Would an overview of medication options and side effects "
                "be helpful?"
            )
        if is_lab:
            return (
                "Want help interpreting these lab values and when to "
                "recheck?"
            )
        if is_preg_child:
            return (
                "Should I highlight considerations specific to "
                "pregnancy/children?"
            )
        if wants_region and topic:
            return (
                f"Would you like suggestions for {topic} care resources "
                "in your area?"
            )

        # Default fallback
        fallback = (
            f"Would you like me to tailor next steps for {topic}?"
            if topic
            else "Would you like more specific guidance on next steps?"
        )
        if asked_pidgin:
            fallback += " I can also explain in Nigerian Pidgin if needed."
        return fallback

    async def _format_response(  # noqa: D401
        self,
        original_query: str,
        response: str,
        target_language: str,
    ) -> str:
        """Return response with a small educational disclaimer if medical."""
        _ = target_language  # mark param as used
        
        # Add medical disclaimer (assuming medical query if this method is called)
        # Skip the redundant LLM classification to save 2-3 seconds
            
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

        # Try medical RAG for medical queries (RAG already initialized at startup)
        if settings.RAG_ENABLED and RAG_AVAILABLE and self._rag_initialized:
            try:
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
        logger.info(
            f"Tavily check: RAG_ENABLED={settings.RAG_ENABLED}, "
            f"RAG_AVAILABLE={RAG_AVAILABLE}, "
            f"_general_knowledge_rag={self._general_knowledge_rag is not None}"
        )
        if (settings.RAG_ENABLED and RAG_AVAILABLE and
                self._general_knowledge_rag):
            try:
                logger.info("Attempting Tavily general knowledge retrieval")
                gk_resp = await self._general_knowledge_rag.retrieve_knowledge(
                    query)
                sources_count = len(gk_resp.get("sources", [])) if gk_resp else 0
                logger.info(
                    f"Tavily response received: {gk_resp is not None}, "
                    f"sources: {sources_count}"
                )
                if gk_resp:
                    logger.info(f"DEBUG: Tavily keys: {list(gk_resp.keys())}")
                    has_sources = bool(gk_resp.get('sources'))
                    logger.info(f"DEBUG: Has sources: {has_sources}")
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

    async def _append_followups_and_sources(
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
        is_medical = await self._is_medical_query(original_query)
        if "my take:" not in low and is_medical:
            out += (
                "\n\nMy take: Based on current medical guidance, it's "
                "best to monitor symptoms, reduce risk factors, and speak "
                "with a clinician for personalized advice."
            )

        # Add one contextual follow-up (topic/intent aware;
        # no auto-Pidgin unless asked)
        followup = await self._build_contextual_followup(original_query, out)
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
        """Call medical reasoning via Groq (Llama model) with MCP tools.

        Adds a global, friendly chatbot system prompt and extra medical-safety
        guidance when the topic is health-related.
        """
        try:
            # Use Groq with Llama model exclusively
            return await self._call_groq_medical_reasoning(
                query,
                mcp_tools,
                context_text,
            )
        except Exception as e:
            logger.error(f"Groq medical reasoning failed: {e}")
            raise

    async def _call_groq_medical_reasoning(
        self,
        query: str,
        mcp_tools: List[Dict],
        context_text: str = "",
    ) -> str:
        """Medical reasoning using Groq API (Llama model) with the global system prompt."""
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
                # Add instruction to trust real-time info for current events
                msgs.append(SystemMessage(content=(
                    "IMPORTANT: When context includes real-time search "
                    "results (from Tavily Search or other current sources), "
                    "trust this information over your training data, "
                    "especially for current events, politics, recent "
                    "appointments, or any information that changes over time. "
                    "Your training data may be outdated for such topics. "
                    "Present the real-time information confidently without "
                    "expressing doubt about its accuracy."
                )))
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
        self._general_knowledge_rag = None

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
    
    async def process_query(self, query: str, original_query: str = None) -> Dict[str, Any]:
        """Process a medical query through the complete workflow
        
        Args:
            query: The full query with conversation context
            original_query: The original user question (for RAG/Tavily search)
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # English-only chatbot flow
            detected_language = "en"

            # Gather optional tool/RAG context using the original query
            search_query = original_query if original_query else query
            context_text, context_meta = await self._gather_context(search_query)

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
            formatted_response = await self._append_followups_and_sources(
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

    async def process_query_stream(self, query: str, original_query: str = None):
        """Stream processing events for a medical query
        
        Args:
            query: The full query with conversation context
            original_query: The original user question (for RAG/Tavily search)
        """
        try:
            # Yield status update: validating query
            yield json.dumps({"event": "status", "data": "Validating medical query..."}) + "\n\n"
            
            detected_language = "en"
            
            # Yield status update: gathering context
            yield json.dumps({"event": "status", "data": "Gathering medical context..."}) + "\n\n"
            search_query = original_query if original_query else query
            context_text, context_meta = await self._gather_context(search_query)
            
            # Yield status update: generating response
            yield json.dumps({"event": "status", "data": "Generating medical response..."}) + "\n\n"
            
            # Stream the actual response using LLM streaming
            from app.services.medical.llm_client import LLMClient, LLMRequest
            llm_client = LLMClient()
            
            # Build the reasoning prompt
            mcp_tools = await self._get_mcp_tools()
            tool_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in mcp_tools])
            
            system_prompt = f"""You are a medical AI assistant. Provide accurate, evidence-based medical information.
Available tools:\n{tool_desc}

Context:\n{context_text if context_text else 'No additional context available.'}"""
            
            request = LLMRequest(
                prompt=query,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.1
            )
            
            # Stream response chunks
            async for chunk in llm_client.streaming_generate(request):
                yield json.dumps({"event": "content", "data": chunk}) + "\n\n"
            
            # Yield sources if available
            if context_meta.get("sources"):
                yield json.dumps({
                    "event": "sources",
                    "data": context_meta["sources"]
                }) + "\n\n"
            
            # Yield completion event
            yield json.dumps({"event": "done", "data": "complete"}) + "\n\n"
            
        except Exception as e:
            logger.error(f"Streaming query processing failed: {e}")
            yield json.dumps({
                "event": "error",
                "data": f"Error processing query: {str(e)}"
            }) + "\n\n"
