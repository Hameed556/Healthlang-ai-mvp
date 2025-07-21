"""
Response Formatter Service

This module provides formatting capabilities for medical analysis responses,
supporting multiple languages and output formats.
"""

import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from app.config import settings
from app.core.exceptions import FormattingError
from app.services.medical.medical_analyzer import MedicalAnalysisResponse, SafetyLevel
from app.utils.metrics import record_response_formatting


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    STRUCTURED = "structured"


@dataclass
class FormattingOptions:
    """Options for response formatting."""
    format: OutputFormat = OutputFormat.JSON
    language: str = "en"
    include_sources: bool = True
    include_disclaimers: bool = True
    include_confidence: bool = True
    include_emergency_indicators: bool = True
    include_follow_up: bool = True
    max_length: Optional[int] = None
    simplify_for_mobile: bool = False


@dataclass
class FormattedResponse:
    """Formatted medical response."""
    content: str
    format: OutputFormat
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseFormatter:
    """
    Service for formatting medical analysis responses.
    
    Supports multiple languages and output formats with customizable options.
    """
    
    def __init__(self):
        """Initialize response formatter."""
        self.language_templates = self._load_language_templates()
        self.format_templates = self._load_format_templates()
        self.safety_level_messages = self._load_safety_level_messages()
        
    def _load_language_templates(self) -> Dict[str, Dict[str, str]]:
        """Load language-specific templates."""
        return {
            "en": {
                "analysis_header": "Medical Analysis",
                "recommendations_header": "Recommendations",
                "safety_level_header": "Safety Assessment",
                "disclaimers_header": "Important Disclaimers",
                "follow_up_header": "Follow-up Questions",
                "emergency_header": "Emergency Indicators",
                "sources_header": "Sources",
                "confidence_header": "Confidence Level"
            },
            "yo": {
                "analysis_header": "Ìtúpalẹ̀ Ìṣègùn",
                "recommendations_header": "Ìmọ̀ràn",
                "safety_level_header": "Ìdíwọ̀n Ààbò",
                "disclaimers_header": "Ìkìlọ̀ Pàtàkì",
                "follow_up_header": "Ìbéèrè Tẹ̀lé",
                "emergency_header": "Àmì Ìṣẹ́lẹ̀",
                "sources_header": "Oríṣun",
                "confidence_header": "Ìwọ̀n Ìgbẹ̀kẹ̀"
            }
        }
    
    def _load_format_templates(self) -> Dict[str, str]:
        """Load format-specific templates."""
        return {
            OutputFormat.MARKDOWN: {
                "section": "## {header}\n\n{content}\n\n",
                "list_item": "- {item}\n",
                "emphasis": "**{text}**",
                "warning": "⚠️ {text}",
                "emergency": "🚨 {text}"
            },
            OutputFormat.HTML: {
                "section": "<h2>{header}</h2>\n<div>{content}</div>\n\n",
                "list_item": "<li>{item}</li>",
                "emphasis": "<strong>{text}</strong>",
                "warning": "<div class='warning'>⚠️ {text}</div>",
                "emergency": "<div class='emergency'>🚨 {text}</div>"
            },
            OutputFormat.TEXT: {
                "section": "{header}\n{separator}\n{content}\n\n",
                "list_item": "• {item}\n",
                "emphasis": "{text}",
                "warning": "WARNING: {text}",
                "emergency": "EMERGENCY: {text}"
            }
        }
    
    def _load_safety_level_messages(self) -> Dict[str, Dict[str, str]]:
        """Load safety level messages for different languages."""
        return {
            "en": {
                SafetyLevel.SAFE: "This appears to be a safe situation for general information.",
                SafetyLevel.CAUTION: "Please exercise caution and consider consulting a healthcare provider.",
                SafetyLevel.URGENT: "This situation may require prompt medical attention.",
                SafetyLevel.EMERGENCY: "This may be an emergency situation. Seek immediate medical attention."
            },
            "yo": {
                SafetyLevel.SAFE: "Eyi dà bí ìpò tí ó wà ní ààbò fún ìmọ̀ràn gbogbogbò.",
                SafetyLevel.CAUTION: "Jọ̀ọ́ ṣe ìṣọ̀ra kí o sì ronú láti bá oníṣègùn sọ̀rọ̀.",
                SafetyLevel.URGENT: "Ìpò yí lè nilo ìtọ́jú ìṣègùn lẹ́sẹ̀kẹ̀sẹ̀.",
                SafetyLevel.EMERGENCY: "Eyi lè jẹ́ ìpò ìṣẹ́lẹ̀. Wa ìtọ́jú ìṣègùn lẹ́sẹ̀kẹ̀sẹ̀."
            }
        }
    
    async def format_response(
        self,
        response: MedicalAnalysisResponse,
        options: FormattingOptions
    ) -> FormattedResponse:
        """
        Format medical analysis response.
        
        Args:
            response: Medical analysis response
            options: Formatting options
            
        Returns:
            FormattedResponse with formatted content
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            start_time = time.time()
            
            if options.format == OutputFormat.JSON:
                formatted_content = self._format_json(response, options)
            elif options.format == OutputFormat.STRUCTURED:
                formatted_content = self._format_structured(response, options)
            else:
                formatted_content = self._format_text(response, options)
            
            # Apply length limits if specified
            if options.max_length and len(formatted_content) > options.max_length:
                formatted_content = self._truncate_content(formatted_content, options.max_length)
            
            # Apply mobile simplification if requested
            if options.simplify_for_mobile:
                formatted_content = self._simplify_for_mobile(formatted_content, options.format)
            
            # Record metrics
            await record_response_formatting(options.format, options.language, time.time() - start_time)
            
            logger.info(f"Response formatted to {options.format} in {options.language}")
            
            return FormattedResponse(
                content=formatted_content,
                format=options.format,
                language=options.language,
                metadata={
                    "original_safety_level": response.safety_level.value,
                    "original_confidence": response.confidence_score,
                    "formatting_options": options.__dict__
                }
            )
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            raise FormattingError(f"Response formatting failed: {e}")
    
    def _format_json(
        self, 
        response: MedicalAnalysisResponse, 
        options: FormattingOptions
    ) -> str:
        """Format response as JSON."""
        output = {
            "analysis": response.analysis,
            "recommendations": response.recommendations,
            "safety_level": response.safety_level.value,
            "confidence_score": response.confidence_score if options.include_confidence else None,
            "query_type": response.query_type.value,
            "structured_data": response.structured_data
        }
        
        if options.include_disclaimers:
            output["disclaimers"] = response.disclaimers
        
        if options.include_follow_up:
            output["follow_up_questions"] = response.follow_up_questions
        
        if options.include_emergency_indicators:
            output["emergency_indicators"] = response.emergency_indicators
        
        if options.include_sources:
            output["sources"] = response.sources
        
        # Remove None values
        output = {k: v for k, v in output.items() if v is not None}
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_structured(
        self, 
        response: MedicalAnalysisResponse, 
        options: FormattingOptions
    ) -> str:
        """Format response as structured text."""
        templates = self.language_templates.get(options.language, self.language_templates["en"])
        safety_messages = self.safety_level_messages.get(options.language, self.safety_level_messages["en"])
        
        sections = []
        
        # Analysis section
        sections.append(f"{templates['analysis_header']}\n{response.analysis}")
        
        # Safety level section
        safety_message = safety_messages.get(response.safety_level, safety_messages[SafetyLevel.CAUTION])
        sections.append(f"{templates['safety_level_header']}\n{safety_message}")
        
        # Recommendations section
        if response.recommendations:
            recommendations_text = "\n".join([f"• {rec}" for rec in response.recommendations])
            sections.append(f"{templates['recommendations_header']}\n{recommendations_text}")
        
        # Emergency indicators section
        if options.include_emergency_indicators and response.emergency_indicators:
            emergency_text = "\n".join([f"⚠️ {indicator}" for indicator in response.emergency_indicators])
            sections.append(f"{templates['emergency_header']}\n{emergency_text}")
        
        # Follow-up questions section
        if options.include_follow_up and response.follow_up_questions:
            follow_up_text = "\n".join([f"• {question}" for question in response.follow_up_questions])
            sections.append(f"{templates['follow_up_header']}\n{follow_up_text}")
        
        # Disclaimers section
        if options.include_disclaimers and response.disclaimers:
            disclaimers_text = "\n".join([f"• {disclaimer}" for disclaimer in response.disclaimers])
            sections.append(f"{templates['disclaimers_header']}\n{disclaimers_text}")
        
        # Confidence section
        if options.include_confidence:
            confidence_text = f"{response.confidence_score:.1%}"
            sections.append(f"{templates['confidence_header']}\n{confidence_text}")
        
        return "\n\n".join(sections)
    
    def _format_text(
        self, 
        response: MedicalAnalysisResponse, 
        options: FormattingOptions
    ) -> str:
        """Format response as text using specified format."""
        format_type = options.format
        templates = self.format_templates.get(format_type, self.format_templates[OutputFormat.TEXT])
        lang_templates = self.language_templates.get(options.language, self.language_templates["en"])
        safety_messages = self.safety_level_messages.get(options.language, self.safety_level_messages["en"])
        
        sections = []
        
        # Analysis section
        analysis_content = response.analysis
        if format_type == OutputFormat.MARKDOWN:
            sections.append(templates["section"].format(
                header=lang_templates["analysis_header"],
                content=analysis_content
            ))
        elif format_type == OutputFormat.HTML:
            sections.append(templates["section"].format(
                header=lang_templates["analysis_header"],
                content=analysis_content
            ))
        else:  # TEXT format
            sections.append(templates["section"].format(
                header=lang_templates["analysis_header"],
                separator="=" * len(lang_templates["analysis_header"]),
                content=analysis_content
            ))
        
        # Safety level section
        safety_message = safety_messages.get(response.safety_level, safety_messages[SafetyLevel.CAUTION])
        if format_type == OutputFormat.MARKDOWN:
            safety_content = templates["warning"].format(text=safety_message)
        elif format_type == OutputFormat.HTML:
            safety_content = templates["warning"].format(text=safety_message)
        else:
            safety_content = templates["warning"].format(text=safety_message)
        
        sections.append(templates["section"].format(
            header=lang_templates["safety_level_header"],
            content=safety_content
        ))
        
        # Recommendations section
        if response.recommendations:
            recommendations_content = "".join([
                templates["list_item"].format(item=rec) for rec in response.recommendations
            ])
            sections.append(templates["section"].format(
                header=lang_templates["recommendations_header"],
                content=recommendations_content
            ))
        
        # Emergency indicators section
        if options.include_emergency_indicators and response.emergency_indicators:
            emergency_content = "".join([
                templates["list_item"].format(item=indicator) for indicator in response.emergency_indicators
            ])
            sections.append(templates["section"].format(
                header=lang_templates["emergency_header"],
                content=emergency_content
            ))
        
        # Follow-up questions section
        if options.include_follow_up and response.follow_up_questions:
            follow_up_content = "".join([
                templates["list_item"].format(item=question) for question in response.follow_up_questions
            ])
            sections.append(templates["section"].format(
                header=lang_templates["follow_up_header"],
                content=follow_up_content
            ))
        
        # Disclaimers section
        if options.include_disclaimers and response.disclaimers:
            disclaimers_content = "".join([
                templates["list_item"].format(item=disclaimer) for disclaimer in response.disclaimers
            ])
            sections.append(templates["section"].format(
                header=lang_templates["disclaimers_header"],
                content=disclaimers_content
            ))
        
        # Confidence section
        if options.include_confidence:
            confidence_text = f"{response.confidence_score:.1%}"
            sections.append(templates["section"].format(
                header=lang_templates["confidence_header"],
                content=confidence_text
            ))
        
        return "".join(sections)
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to specified length."""
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundaries
        sentences = content.split('. ')
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length - 10:  # Leave room for "..."
                truncated += sentence + '. '
            else:
                break
        
        if truncated:
            return truncated.rstrip() + "..."
        else:
            # If no sentences fit, truncate at word boundaries
            words = content.split()
            truncated = ""
            
            for word in words:
                if len(truncated + word + ' ') <= max_length - 10:
                    truncated += word + ' '
                else:
                    break
            
            return truncated.rstrip() + "..."
    
    def _simplify_for_mobile(self, content: str, format_type: OutputFormat) -> str:
        """Simplify content for mobile devices."""
        if format_type == OutputFormat.JSON:
            # For JSON, just ensure it's properly formatted
            return content
        
        # For text formats, simplify by:
        # 1. Reducing section headers
        # 2. Shortening sentences
        # 3. Removing redundant information
        
        # Simple text simplification
        simplified = content
        
        # Remove excessive whitespace
        simplified = re.sub(r'\n{3,}', '\n\n', simplified)
        
        # Shorten long sentences (basic approach)
        sentences = simplified.split('. ')
        shortened_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 100:
                # Try to break at natural points
                words = sentence.split()
                if len(words) > 20:
                    # Take first 15 words and add "..."
                    shortened = ' '.join(words[:15]) + "..."
                    shortened_sentences.append(shortened)
                else:
                    shortened_sentences.append(sentence)
            else:
                shortened_sentences.append(sentence)
        
        return '. '.join(shortened_sentences)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return [format.value for format in OutputFormat]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.language_templates.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of response formatter.
        
        Returns:
            Health status
        """
        try:
            # Test basic formatting
            test_response = MedicalAnalysisResponse(
                analysis="Test analysis",
                recommendations=["Test recommendation"],
                safety_level=SafetyLevel.SAFE,
                confidence_score=0.8,
                query_type=MedicalQueryType.GENERAL_QUESTION
            )
            
            test_options = FormattingOptions(
                format=OutputFormat.JSON,
                language="en"
            )
            
            formatted = await self.format_response(test_response, test_options)
            
            return {
                "status": "healthy",
                "supported_formats": self.get_supported_formats(),
                "supported_languages": self.get_supported_languages(),
                "test_formatting": {
                    "success": True,
                    "output_length": len(formatted.content)
                }
            }
            
        except Exception as e:
            logger.error(f"Response formatter health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 