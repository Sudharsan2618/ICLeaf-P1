# retrievers/pinecone_retriever.py
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from config.settings import PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL, MAX_SEARCH_RESULTS

class PineconeRetriever:
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize Pinecone client
        if PINECONE_API_KEY:
            try:
                import pinecone
                self.pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
                self.index = self.pc.Index(PINECONE_INDEX)
                self.pinecone_available = True
            except Exception as e:
                print(f"Pinecone initialization error: {e}")
                self.pinecone_available = False
        else:
            print("Pinecone API key not configured")
            self.pinecone_available = False
    
    def retrieve_structured(self, query: str) -> Dict:
        """Retrieve structured context from Pinecone with relevance scoring"""
        if not self.pinecone_available:
            return self._get_fallback_response()
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search Pinecone index
            results = self.index.query(
                vector=query_embedding,
                top_k=MAX_SEARCH_RESULTS,
                include_metadata=True
            )
            
            # Process and structure the results
            structured_results = {
                'internal_documents': [],
                'confidence_score': 0.0,
                'related_topics': [],
                'sources_used': []
            }
            
            if results.matches:
                documents = []
                total_score = 0.0
                topics = set()
                
                for match in results.matches:
                    metadata = match.metadata
                    score = match.score
                    
                    # Create structured document
                    document = {
                        'title': metadata.get('title', 'Untitled Document'),
                        'content': metadata.get('content', 'No content available'),
                        'source': metadata.get('source', 'knowledge_base'),
                        'relevance_score': float(score),
                        'metadata': {
                            'id': match.id,
                            'score': score,
                            'category': metadata.get('category', 'general'),
                            'tags': metadata.get('tags', [])
                        }
                    }
                    documents.append(document)
                    total_score += score
                    
                    # Extract related topics from tags
                    if 'tags' in metadata:
                        topics.update(metadata['tags'])
                
                # Calculate average confidence score
                avg_confidence = total_score / len(results.matches) if results.matches else 0.0
                
                structured_results['internal_documents'] = documents
                structured_results['confidence_score'] = min(avg_confidence, 1.0)
                structured_results['related_topics'] = list(topics)[:5]  # Top 5 topics
                structured_results['sources_used'] = ['pinecone']
            
            return structured_results
            
        except Exception as e:
            print(f"Pinecone search error: {e}")
            return self._get_fallback_response()
    
    def retrieve(self, query: str) -> str:
        """Legacy method - kept for compatibility"""
        structured_results = self.retrieve_structured(query)
        
        if not structured_results['internal_documents']:
            return "No relevant internal documents found."
        
        # Format results as text
        context_parts = []
        for doc in structured_results['internal_documents']:
            context_parts.append(
                f"Title: {doc['title']}\n"
                f"Source: {doc['source']}\n"
                f"Relevance: {doc['relevance_score']:.2f}\n"
                f"Content: {doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self) -> Dict:
        """Return fallback response when Pinecone is not available"""
        return {
            'internal_documents': [
                {
                    'title': 'Sample Internal Document',
                    'content': 'This is a sample internal document. Please configure Pinecone for actual internal knowledge retrieval.',
                    'source': 'fallback',
                    'relevance_score': 0.5,
                    'metadata': {'category': 'general', 'tags': ['sample']}
                }
            ],
            'confidence_score': 0.3,
            'related_topics': ['sample', 'configuration'],
            'sources_used': ['fallback']
        }
    
    def add_document(self, document_id: str, title: str, content: str, 
                    source: str = "knowledge_base", category: str = "general", 
                    tags: List[str] = None) -> bool:
        """Add a document to the Pinecone index"""
        if not self.pinecone_available:
            print("Pinecone not available for document addition")
            return False
        
        try:
            # Generate embedding for the content
            content_embedding = self.embedding_model.encode(content).tolist()
            
            # Prepare metadata
            metadata = {
                'title': title,
                'content': content,
                'source': source,
                'category': category,
                'tags': tags or []
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(document_id, content_embedding, metadata)]
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding document to Pinecone: {e}")
            return False