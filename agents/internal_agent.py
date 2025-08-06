# agents/internal_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from retrievers.pinecone_retriever import PineconeRetriever
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from config.models import InternalResponse, InternalDocument

class InternalAgent(BaseAgent):
    def __init__(self, state):
        super().__init__(state)
        # Configure Google Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )
        self.retriever = PineconeRetriever()
        
        # Set up Pydantic output parser
        self.parser = PydanticOutputParser(pydantic_object=InternalResponse)
        
        # Set up ChatPromptTemplate
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that provides comprehensive answers based on internal knowledge base and training materials.

Your task is to analyze the provided internal context and create a structured response that includes:
1. A comprehensive answer to the user's query based on internal knowledge
2. Relevant internal documents and their sources
3. Confidence score for your response
4. Related topics or concepts
5. List of internal sources used

{format_instructions}"""),
            ("human", """User Query: {query}

Context from internal knowledge base:
{context}

Please provide a comprehensive answer based on the internal context above. If the context doesn't contain relevant information, provide a general answer based on your training."""),
        ])
    
    def get_response(self):
        """Generate structured response using Gemini with internal knowledge context"""
        try:
            # Retrieve structured context from internal knowledge base
            structured_context = self.retriever.retrieve_structured(self.state.query)
            
            # Convert structured data to context string for the prompt
            context_parts = []
            
            if structured_context['internal_documents']:
                internal_context = "Internal Knowledge Base Results:\n"
                for doc in structured_context['internal_documents']:
                    internal_context += f"Title: {doc['title']}\n"
                    internal_context += f"Source: {doc['source']}\n"
                    internal_context += f"Relevance Score: {doc['relevance_score']:.2f}\n"
                    internal_context += f"Content: {doc['content']}\n\n"
                context_parts.append(internal_context)
            
            # Add confidence and related topics info
            if structured_context['confidence_score'] > 0:
                confidence_info = f"Overall Confidence: {structured_context['confidence_score']:.2f}\n"
                context_parts.append(confidence_info)
            
            if structured_context['related_topics']:
                topics_info = f"Related Topics: {', '.join(structured_context['related_topics'])}\n"
                context_parts.append(topics_info)
            
            full_context = "\n".join(context_parts) if context_parts else "No relevant internal information found."
            
            # Create the prompt with format instructions
            prompt = self.prompt_template.partial(
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Generate response using Gemini
            chain = prompt | self.model | self.parser
            response = chain.invoke({
                "query": self.state.query,
                "context": full_context
            })
            
            # Convert the structured response to JSON
            return response.model_dump_json(indent=2)
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

def call_gemini_api(prompt):
    """Legacy function - kept for compatibility"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"