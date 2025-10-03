"""
Medical Analyzer Service

This module provides medical analysis and reasoning capabilities using LLMs
with specialized medical prompts, safety checks, and structured output.
"""

import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from app.config import settings
from app.core.exceptions import MedicalAnalysisError, SafetyCheckError
from app.services.medical.llm_client import LLMClient, LLMRequest
from app.utils.metrics import record_medical_analysis, record_safety_check


class MedicalQueryType(str, Enum):
    """Types of medical queries."""
    SYMPTOM_ANALYSIS = "symptom_analysis"
    MEDICATION_INFO = "medication_info"
    TREATMENT_OPTIONS = "treatment_options"
    DIAGNOSIS_HELP = "diagnosis_help"
    PREVENTIVE_CARE = "preventive_care"
    EMERGENCY_ASSESSMENT = "emergency_assessment"
    GENERAL_QUESTION = "general_question"


class SafetyLevel(str, Enum):
    """Safety levels for medical responses."""
    SAFE = "safe"
    CAUTION = "caution"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class MedicalAnalysisRequest:
    """Medical analysis request."""
    query: str
    query_type: MedicalQueryType
    language: str = "en"
    context: Optional[Dict[str, Any]] = None
    user_age: Optional[int] = None
    user_gender: Optional[str] = None
    existing_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    symptoms_duration: Optional[str] = None
    severity_level: Optional[str] = None


@dataclass
class MedicalAnalysisResponse:
    """Medical analysis response."""
    analysis: str
    recommendations: List[str]
    safety_level: SafetyLevel
    confidence_score: float
    query_type: MedicalQueryType
    disclaimers: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    emergency_indicators: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)


class MedicalAnalyzer:
    """
    Medical analysis service using LLMs with safety checks and structured output.
    
    Provides medical reasoning, symptom analysis, and safety assessments.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize medical analyzer.
        
        Args:
            llm_client: LLM client for medical reasoning
        """
        self.llm_client = llm_client
        self.safety_keywords = self._load_safety_keywords()
        self.emergency_keywords = self._load_emergency_keywords()
        self.medical_prompts = self._load_medical_prompts()
        
    def _load_safety_keywords(self) -> Dict[str, List[str]]:
        """Load safety-related keywords for different categories."""
        return {
            "emergency": [
                "chest pain", "heart attack", "stroke", "severe bleeding",
                "unconscious", "difficulty breathing", "severe injury",
                "poisoning", "overdose", "suicidal", "homicidal"
            ],
            "urgent": [
                "high fever", "severe pain", "sudden onset", "worsening",
                "cannot function", "severe symptoms", "rapid deterioration"
            ],
            "caution": [
                "persistent", "chronic", "recurring", "unusual",
                "new symptoms", "changes", "concerned"
            ]
        }
    
    def _load_emergency_keywords(self) -> List[str]:
        """Load emergency-specific keywords."""
        return [
            "emergency", "urgent", "immediate", "critical", "severe",
            "life-threatening", "dangerous", "serious", "acute"
        ]
    
    def _load_medical_prompts(self) -> Dict[str, str]:
        """Load specialized medical prompts for different query types."""
        return {
            MedicalQueryType.SYMPTOM_ANALYSIS: """
You are a medical AI assistant. Analyze the following symptoms and provide:
1. Possible causes (most likely to least likely)
2. Recommended next steps
3. Safety assessment
4. When to seek medical attention

User query: {query}

Context: {context}

Provide your analysis in a structured, professional manner. Always prioritize safety and recommend medical consultation when appropriate.
""",
            MedicalQueryType.MEDICATION_INFO: """
You are a medical AI assistant. Provide information about the following medication:
1. What it's used for
2. Common side effects
3. Important warnings
4. Drug interactions to be aware of
5. When to contact a healthcare provider

Medication: {query}

Context: {context}

Provide accurate, evidence-based information while emphasizing the importance of consulting healthcare providers for personalized advice.
""",
            MedicalQueryType.TREATMENT_OPTIONS: """
You are a medical AI assistant. Discuss treatment options for the following condition:
1. Available treatment approaches
2. Benefits and risks of each option
3. Lifestyle modifications that may help
4. When to consider different treatments
5. Importance of professional medical guidance

Condition: {query}

Context: {context}

Provide balanced information while emphasizing that treatment decisions should be made with healthcare providers.
""",
            MedicalQueryType.DIAGNOSIS_HELP: """
You are a medical AI assistant. Help understand the following condition:
1. What the condition involves
2. Common symptoms and presentations
3. Diagnostic process
4. Treatment approaches
5. Prognosis and management

Condition: {query}

Context: {context}

Provide educational information while making it clear that actual diagnosis requires professional medical evaluation.
""",
            MedicalQueryType.PREVENTIVE_CARE: """
You are a medical AI assistant. Provide preventive care information for:
1. Recommended screenings and check-ups
2. Lifestyle modifications for prevention
3. Risk factors to be aware of
4. Early warning signs
5. When to seek preventive care

Topic: {query}

Context: {context}

Focus on evidence-based preventive measures and the importance of regular healthcare visits.
""",
            MedicalQueryType.EMERGENCY_ASSESSMENT: """
You are a medical AI assistant. Assess the urgency of the following situation:
1. Immediate safety concerns
2. Urgency level assessment
3. Recommended immediate actions
4. When to seek emergency care
5. What to do while waiting for help

Situation: {query}

Context: {context}

Prioritize safety and provide clear guidance on when emergency care is needed.
""",
            MedicalQueryType.GENERAL_QUESTION: """
You are a medical AI assistant. Answer the following medical question:
1. Provide accurate, evidence-based information
2. Address the specific question asked
3. Include relevant context and caveats
4. Recommend when to consult healthcare providers
5. Provide additional resources if helpful

Question: {query}

Context: {context}

Provide helpful, accurate information while emphasizing the importance of professional medical advice for specific situations.
"""
        }
    
    async def analyze(
        self, 
        request: MedicalAnalysisRequest
    ) -> MedicalAnalysisResponse:
        """
        Perform medical analysis of the query.
        
        Args:
            request: Medical analysis request
            
        Returns:
            MedicalAnalysisResponse with analysis and recommendations
            
        Raises:
            MedicalAnalysisError: If analysis fails
            SafetyCheckError: If safety check fails
        """
        try:
            # Perform safety check first
            safety_level = await self._perform_safety_check(request)
            
            # Generate medical analysis
            analysis_result = await self._generate_medical_analysis(request)
            
            # Structure the response
            response = self._structure_response(analysis_result, safety_level, request)
            
            # Record metrics
            await record_medical_analysis(request.query_type, safety_level)
            
            logger.info(f"Medical analysis completed for {request.query_type} with safety level {safety_level}")
            return response
            
        except Exception as e:
            logger.error(f"Medical analysis failed: {e}")
            raise MedicalAnalysisError(f"Medical analysis failed: {e}")
    
    async def _perform_safety_check(self, request: MedicalAnalysisRequest) -> SafetyLevel:
        """
        Perform safety assessment of the medical query.
        
        Args:
            request: Medical analysis request
            
        Returns:
            SafetyLevel indicating urgency
        """
        try:
            query_lower = request.query.lower()
            
            # Check for emergency keywords
            for keyword in self.emergency_keywords:
                if keyword in query_lower:
                    await record_safety_check("emergency_keyword", SafetyLevel.EMERGENCY)
                    return SafetyLevel.EMERGENCY
            
            # Check safety keyword categories
            for category, keywords in self.safety_keywords.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        if category == "emergency":
                            await record_safety_check("emergency_category", SafetyLevel.EMERGENCY)
                            return SafetyLevel.EMERGENCY
                        elif category == "urgent":
                            await record_safety_check("urgent_category", SafetyLevel.URGENT)
                            return SafetyLevel.URGENT
                        elif category == "caution":
                            await record_safety_check("caution_category", SafetyLevel.CAUTION)
                            return SafetyLevel.CAUTION
            
            # Use LLM for more nuanced safety assessment
            safety_prompt = f"""
Assess the safety level of this medical query. Consider:
- Urgency of symptoms
- Potential for serious conditions
- Need for immediate medical attention
- Risk level

Query: {request.query}
Context: {request.context or 'No additional context'}

Respond with only one word: SAFE, CAUTION, URGENT, or EMERGENCY
"""
            
            safety_request = LLMRequest(
                prompt=safety_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            safety_response = await self.llm_client.generate(safety_request)
            safety_result = safety_response.content.strip().upper()
            
            # Map LLM response to safety level
            safety_mapping = {
                "SAFE": SafetyLevel.SAFE,
                "CAUTION": SafetyLevel.CAUTION,
                "URGENT": SafetyLevel.URGENT,
                "EMERGENCY": SafetyLevel.EMERGENCY
            }
            
            safety_level = safety_mapping.get(safety_result, SafetyLevel.CAUTION)
            await record_safety_check("llm_assessment", safety_level)
            
            return safety_level
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            # Default to caution if safety check fails
            return SafetyLevel.CAUTION
    
    async def _generate_medical_analysis(
        self, 
        request: MedicalAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Generate medical analysis using LLM.
        
        Args:
            request: Medical analysis request
            
        Returns:
            Dictionary with analysis results
        """
        # Get appropriate prompt template
        prompt_template = self.medical_prompts.get(
            request.query_type, 
            self.medical_prompts[MedicalQueryType.GENERAL_QUESTION]
        )
        
        # Format prompt with context
        context_str = json.dumps(request.context) if request.context else "No additional context"
        
        formatted_prompt = prompt_template.format(
            query=request.query,
            context=context_str
        )
        
        # Add safety and disclaimer instructions
        system_prompt = (
            settings.SYSTEM_PROMPT
            + "\n"  # Ensure persona is applied universally
            + (
                "You are a medical AI assistant. Provide helpful, "
                "evidence-based medical information while:\n\n"
                "1. Always emphasize consulting healthcare providers for "
                "specific medical advice\n"
                "2. Include appropriate disclaimers about the limitations of "
                "AI medical advice\n"
                "3. Prioritize safety and recommend medical attention when "
                "appropriate\n"
                "4. Provide structured, clear responses\n"
                "5. Acknowledge when symptoms require immediate medical "
                "attention\n\n"
                "Your responses should be educational and supportive, not "
                "diagnostic or prescriptive."
            )
        )
        
        llm_request = LLMRequest(
            prompt=formatted_prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.1
        )
        
        response = await self.llm_client.generate(llm_request)
        
        # Parse and structure the response
        return self._parse_llm_response(response.content, request.query_type)
    
    def _parse_llm_response(
        self, 
        content: str, 
        query_type: MedicalQueryType
    ) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.
        
        Args:
            content: Raw LLM response
            query_type: Type of medical query
            
        Returns:
            Structured response data
        """
        # Extract recommendations
        recommendations = self._extract_recommendations(content)
        
        # Extract disclaimers
        disclaimers = self._extract_disclaimers(content)
        
        # Extract follow-up questions
        follow_up_questions = self._extract_follow_up_questions(content)
        
        # Extract emergency indicators
        emergency_indicators = self._extract_emergency_indicators(content)
        
        # Calculate confidence score (simplified)
        confidence_score = self._calculate_confidence_score(content, query_type)
        
        return {
            "analysis": content,
            "recommendations": recommendations,
            "disclaimers": disclaimers,
            "follow_up_questions": follow_up_questions,
            "emergency_indicators": emergency_indicators,
            "confidence_score": confidence_score
        }
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from LLM response."""
        recommendations = []
        
        # Look for numbered or bulleted recommendations
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('•', '-', '*', '1.', '2.', '3.')) and 
                any(keyword in line.lower() for keyword in ['recommend', 'should', 'consider', 'seek', 'consult'])):
                recommendations.append(line.lstrip('•-*123456789. '))
        
        return recommendations[:5]  # Limit to top 5
    
    def _extract_disclaimers(self, content: str) -> List[str]:
        """Extract disclaimers from LLM response."""
        disclaimers = []
        
        disclaimer_keywords = [
            'disclaimer', 'important', 'note', 'warning', 'caution',
            'consult', 'professional', 'medical advice', 'limitation'
        ]
        
        sentences = re.split(r'[.!?]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in disclaimer_keywords):
                disclaimers.append(sentence)
        
        return disclaimers[:3]  # Limit to top 3
    
    def _extract_follow_up_questions(self, content: str) -> List[str]:
        """Extract follow-up questions from LLM response."""
        questions = []
        
        # Look for question marks
        sentences = re.split(r'[.!?]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if '?' in sentence and len(sentence) > 10:
                questions.append(sentence)
        
        return questions[:3]  # Limit to top 3
    
    def _extract_emergency_indicators(self, content: str) -> List[str]:
        """Extract emergency indicators from LLM response."""
        indicators = []
        
        emergency_phrases = [
            'seek immediate', 'emergency', 'urgent', 'call 911',
            'go to hospital', 'emergency room', 'immediate attention'
        ]
        
        sentences = re.split(r'[.!?]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(phrase in sentence.lower() for phrase in emergency_phrases):
                indicators.append(sentence)
        
        return indicators
    
    def _calculate_confidence_score(self, content: str, query_type: MedicalQueryType) -> float:
        """
        Calculate confidence score for the analysis.
        
        Args:
            content: LLM response content
            query_type: Type of medical query
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence by query type
        base_confidence = {
            MedicalQueryType.MEDICATION_INFO: 0.8,
            MedicalQueryType.PREVENTIVE_CARE: 0.7,
            MedicalQueryType.GENERAL_QUESTION: 0.6,
            MedicalQueryType.DIAGNOSIS_HELP: 0.5,
            MedicalQueryType.TREATMENT_OPTIONS: 0.5,
            MedicalQueryType.SYMPTOM_ANALYSIS: 0.4,
            MedicalQueryType.EMERGENCY_ASSESSMENT: 0.3
        }.get(query_type, 0.5)
        
        # Adjust based on response quality indicators
        quality_indicators = 0.0
        
        # Check for structured response
        if any(marker in content for marker in ['1.', '2.', '3.', '•', '-']):
            quality_indicators += 0.1
        
        # Check for disclaimers (indicates responsible response)
        if any(word in content.lower() for word in ['consult', 'professional', 'medical advice']):
            quality_indicators += 0.1
        
        # Check for specific recommendations
        if any(word in content.lower() for word in ['recommend', 'should', 'consider']):
            quality_indicators += 0.1
        
        # Check for safety considerations
        if any(word in content.lower() for word in ['safety', 'emergency', 'urgent']):
            quality_indicators += 0.1
        
        return min(1.0, base_confidence + quality_indicators)
    
    def _structure_response(
        self, 
        analysis_result: Dict[str, Any],
        safety_level: SafetyLevel,
        request: MedicalAnalysisRequest
    ) -> MedicalAnalysisResponse:
        """
        Structure the final medical analysis response.
        
        Args:
            analysis_result: Parsed analysis results
            safety_level: Determined safety level
            request: Original request
            
        Returns:
            Structured MedicalAnalysisResponse
        """
        # Add safety-based disclaimers
        disclaimers = analysis_result.get("disclaimers", [])
        if safety_level in [SafetyLevel.URGENT, SafetyLevel.EMERGENCY]:
            disclaimers.insert(0, "This situation may require immediate medical attention. Please consult a healthcare provider or emergency services.")
        
        # Add general medical disclaimer
        disclaimers.append("This information is for educational purposes only and should not replace professional medical advice.")
        
        return MedicalAnalysisResponse(
            analysis=analysis_result["analysis"],
            recommendations=analysis_result.get("recommendations", []),
            safety_level=safety_level,
            confidence_score=analysis_result.get("confidence_score", 0.5),
            query_type=request.query_type,
            disclaimers=disclaimers,
            follow_up_questions=analysis_result.get("follow_up_questions", []),
            emergency_indicators=analysis_result.get("emergency_indicators", []),
            sources=[],  # TODO: Add source tracking
            structured_data={
                "query_type": request.query_type.value,
                "safety_level": safety_level.value,
                "language": request.language,
                "context": request.context
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of medical analyzer.
        
        Returns:
            Health status
        """
        try:
            # Test LLM client health
            llm_health = await self.llm_client.health_check()
            
            # Test basic analysis
            test_request = MedicalAnalysisRequest(
                query="What are common symptoms of a cold?",
                query_type=MedicalQueryType.GENERAL_QUESTION
            )
            
            test_response = await self.analyze(test_request)
            
            return {
                "status": "healthy",
                "llm_client": llm_health,
                "analysis_test": {
                    "success": True,
                    "safety_level": test_response.safety_level.value,
                    "confidence_score": test_response.confidence_score
                }
            }
            
        except Exception as e:
            logger.error(f"Medical analyzer health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 