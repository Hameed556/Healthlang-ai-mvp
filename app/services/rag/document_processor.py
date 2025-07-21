"""
Document Processor Service

This module provides document processing capabilities for the RAG system,
including text extraction, chunking, and metadata extraction.
"""

import asyncio
import re
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib

from loguru import logger

from app.config import settings
from app.core.exceptions import DocumentProcessingError
from app.services.rag.vector_store import Document
from app.utils.metrics import record_document_processing


class DocumentType(str, Enum):
    """Supported document types."""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"


class ChunkingStrategy(str, Enum):
    """Document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass
class ProcessingOptions:
    """Document processing options."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    include_metadata: bool = True
    extract_metadata: bool = True
    clean_text: bool = True
    language: str = "en"


@dataclass
class ProcessedDocument:
    """Processed document with chunks."""
    original_document: Document
    chunks: List[Document]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


class DocumentProcessor:
    """
    Service for processing documents for RAG system.
    
    Handles text extraction, chunking, and metadata extraction.
    """
    
    def __init__(self):
        """Initialize document processor."""
        self.supported_extensions = {
            '.txt': DocumentType.TEXT,
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML,
            '.md': DocumentType.MARKDOWN,
            '.json': DocumentType.JSON,
            '.csv': DocumentType.CSV
        }
        
    async def process_document(
        self, 
        document: Document, 
        options: ProcessingOptions
    ) -> ProcessedDocument:
        """
        Process a document for RAG.
        
        Args:
            document: Document to process
            options: Processing options
            
        Returns:
            ProcessedDocument with chunks
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            start_time = time.time()
            
            # Determine document type
            doc_type = self._detect_document_type(document)
            
            # Extract text content
            text_content = await self._extract_text(document, doc_type)
            
            # Clean text if requested
            if options.clean_text:
                text_content = self._clean_text(text_content)
            
            # Extract metadata if requested
            metadata = {}
            if options.extract_metadata:
                metadata = await self._extract_metadata(document, doc_type, text_content)
            
            # Chunk the document
            chunks = await self._chunk_document(
                text_content, 
                document, 
                options, 
                metadata
            )
            
            processing_time = time.time() - start_time
            
            # Record metrics
            await record_document_processing(
                doc_type.value, 
                len(chunks), 
                processing_time
            )
            
            logger.info(f"Processed document {document.id} into {len(chunks)} chunks in {processing_time:.2f}s")
            
            return ProcessedDocument(
                original_document=document,
                chunks=chunks,
                metadata=metadata,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise DocumentProcessingError(f"Document processing failed: {e}")
    
    def _detect_document_type(self, document: Document) -> DocumentType:
        """Detect document type based on content or metadata."""
        # Check if type is specified in metadata
        if document.metadata and 'type' in document.metadata:
            try:
                return DocumentType(document.metadata['type'])
            except ValueError:
                pass
        
        # Check if source path has extension
        if document.source:
            path = Path(document.source)
            if path.suffix.lower() in self.supported_extensions:
                return self.supported_extensions[path.suffix.lower()]
        
        # Default to text
        return DocumentType.TEXT
    
    async def _extract_text(self, document: Document, doc_type: DocumentType) -> str:
        """Extract text content from document."""
        if doc_type == DocumentType.TEXT:
            return document.content
        
        elif doc_type == DocumentType.PDF:
            return await self._extract_pdf_text(document)
        
        elif doc_type == DocumentType.DOCX:
            return await self._extract_docx_text(document)
        
        elif doc_type == DocumentType.HTML:
            return await self._extract_html_text(document)
        
        elif doc_type == DocumentType.MARKDOWN:
            return await self._extract_markdown_text(document)
        
        elif doc_type == DocumentType.JSON:
            return await self._extract_json_text(document)
        
        elif doc_type == DocumentType.CSV:
            return await self._extract_csv_text(document)
        
        else:
            # Fallback to content as-is
            return document.content
    
    async def _extract_pdf_text(self, document: Document) -> str:
        """Extract text from PDF document."""
        # TODO: Implement PDF text extraction
        # This would use libraries like PyPDF2, pdfplumber, or similar
        logger.warning("PDF text extraction not yet implemented")
        return document.content
    
    async def _extract_docx_text(self, document: Document) -> str:
        """Extract text from DOCX document."""
        # TODO: Implement DOCX text extraction
        # This would use python-docx library
        logger.warning("DOCX text extraction not yet implemented")
        return document.content
    
    async def _extract_html_text(self, document: Document) -> str:
        """Extract text from HTML document."""
        # TODO: Implement HTML text extraction
        # This would use BeautifulSoup or similar
        logger.warning("HTML text extraction not yet implemented")
        return document.content
    
    async def _extract_markdown_text(self, document: Document) -> str:
        """Extract text from Markdown document."""
        # For markdown, we can use the content directly
        # or convert to plain text if needed
        return document.content
    
    async def _extract_json_text(self, document: Document) -> str:
        """Extract text from JSON document."""
        try:
            import json
            data = json.loads(document.content)
            # Convert JSON to readable text format
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
            return document.content
    
    async def _extract_csv_text(self, document: Document) -> str:
        """Extract text from CSV document."""
        # TODO: Implement CSV text extraction
        # This would use pandas or csv library
        logger.warning("CSV text extraction not yet implemented")
        return document.content
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text.strip()
    
    async def _extract_metadata(
        self, 
        document: Document, 
        doc_type: DocumentType, 
        text_content: str
    ) -> Dict[str, Any]:
        """Extract metadata from document."""
        metadata = {}
        
        # Basic metadata
        metadata['document_type'] = doc_type.value
        metadata['content_length'] = len(text_content)
        metadata['word_count'] = len(text_content.split())
        
        # Extract title if possible
        title = self._extract_title(text_content)
        if title:
            metadata['title'] = title
        
        # Extract language if possible
        language = self._detect_language(text_content)
        if language:
            metadata['language'] = language
        
        # Extract key topics/themes
        topics = self._extract_topics(text_content)
        if topics:
            metadata['topics'] = topics
        
        # Merge with existing metadata
        if document.metadata:
            metadata.update(document.metadata)
        
        return metadata
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from text content."""
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) < 200 and not line.startswith(('http', 'www')):
                # Simple heuristic: first non-empty line that's not too long
                return line
        return None
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text content."""
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # Yoruba detection
        yoruba_words = ['ni', 'ti', 'o', 'a', 'e', 'ki', 'bi', 'si', 'fun', 'lori']
        yoruba_count = sum(1 for word in yoruba_words if word in text_lower)
        
        # English detection
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if yoruba_count > english_count:
            return 'yo'
        elif english_count > yoruba_count:
            return 'en'
        else:
            return None
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text content."""
        # Simple topic extraction based on frequency
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 5 most frequent words as topics
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [topic[0] for topic in topics]
    
    async def _chunk_document(
        self, 
        text: str, 
        original_doc: Document, 
        options: ProcessingOptions, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Chunk document into smaller pieces."""
        if options.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, original_doc, options, metadata)
        elif options.chunking_strategy == ChunkingStrategy.SEMANTIC:
            return await self._chunk_semantic(text, original_doc, options, metadata)
        elif options.chunking_strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_sentence(text, original_doc, options, metadata)
        elif options.chunking_strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_paragraph(text, original_doc, options, metadata)
        else:
            # Default to fixed size
            return self._chunk_fixed_size(text, original_doc, options, metadata)
    
    def _chunk_fixed_size(
        self, 
        text: str, 
        original_doc: Document, 
        options: ProcessingOptions, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Chunk document into fixed-size pieces."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + options.chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                # Look for the last space before the end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = f"{original_doc.id}_chunk_{len(chunks)}"
                
                chunk_metadata = metadata.copy() if options.include_metadata else {}
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'chunk_start': start,
                    'chunk_end': end,
                    'chunk_strategy': options.chunking_strategy.value,
                    'parent_document_id': original_doc.id
                })
                
                chunk = Document(
                    id=chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata,
                    source=original_doc.source
                )
                
                chunks.append(chunk)
            
            start = end - options.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def _chunk_semantic(
        self, 
        text: str, 
        original_doc: Document, 
        options: ProcessingOptions, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Chunk document semantically (placeholder)."""
        # TODO: Implement semantic chunking
        # This would use NLP techniques to find natural break points
        logger.warning("Semantic chunking not yet implemented, falling back to fixed size")
        return self._chunk_fixed_size(text, original_doc, options, metadata)
    
    def _chunk_sentence(
        self, 
        text: str, 
        original_doc: Document, 
        options: ProcessingOptions, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Chunk document by sentences."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > options.chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk)
                chunk_id = f"{original_doc.id}_chunk_{len(chunks)}"
                
                chunk_metadata = metadata.copy() if options.include_metadata else {}
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'chunk_strategy': options.chunking_strategy.value,
                    'parent_document_id': original_doc.id
                })
                
                chunk = Document(
                    id=chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata,
                    source=original_doc.source
                )
                
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else []
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = f"{original_doc.id}_chunk_{len(chunks)}"
            
            chunk_metadata = metadata.copy() if options.include_metadata else {}
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'chunk_strategy': options.chunking_strategy.value,
                'parent_document_id': original_doc.id
            })
            
            chunk = Document(
                id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata,
                source=original_doc.source
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_paragraph(
        self, 
        text: str, 
        original_doc: Document, 
        options: ProcessingOptions, 
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Chunk document by paragraphs."""
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph_length = len(paragraph)
            
            if current_length + paragraph_length > options.chunk_size and current_chunk:
                # Create chunk from current paragraphs
                chunk_text = '\n\n'.join(current_chunk)
                chunk_id = f"{original_doc.id}_chunk_{len(chunks)}"
                
                chunk_metadata = metadata.copy() if options.include_metadata else {}
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'chunk_strategy': options.chunking_strategy.value,
                    'parent_document_id': original_doc.id
                })
                
                chunk = Document(
                    id=chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata,
                    source=original_doc.source
                )
                
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [paragraph]
                current_length = paragraph_length
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk_id = f"{original_doc.id}_chunk_{len(chunks)}"
            
            chunk_metadata = metadata.copy() if options.include_metadata else {}
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'chunk_strategy': options.chunking_strategy.value,
                'parent_document_id': original_doc.id
            })
            
            chunk = Document(
                id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata,
                source=original_doc.source
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported document types."""
        return [doc_type.value for doc_type in DocumentType]
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.supported_extensions.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of document processor.
        
        Returns:
            Health status
        """
        try:
            # Test basic processing
            test_document = Document(
                id="health_check_test",
                content="This is a test document for health checking. It contains multiple sentences to test chunking functionality.",
                metadata={"type": "text"}
            )
            
            test_options = ProcessingOptions(
                chunk_size=50,
                chunk_overlap=10,
                chunking_strategy=ChunkingStrategy.FIXED_SIZE
            )
            
            processed = await self.process_document(test_document, test_options)
            
            return {
                "status": "healthy",
                "supported_types": self.get_supported_types(),
                "supported_extensions": self.get_supported_extensions(),
                "test_processing": {
                    "success": True,
                    "chunks_generated": len(processed.chunks),
                    "processing_time": processed.processing_time
                }
            }
            
        except Exception as e:
            logger.error(f"Document processor health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 