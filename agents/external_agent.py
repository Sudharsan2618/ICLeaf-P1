# agents/external_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from retrievers.web_retriever import WebRetriever
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from config.models import StructuredResponse, WebResult, YouTubeResult, GitHubResult, CodeResult

class ExternalAgent(BaseAgent):
    def __init__(self, state):
        super().__init__(state)
        # Configure Google Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )
        self.retriever = WebRetriever()
        
        # Set up Pydantic output parser
        self.parser = PydanticOutputParser(pydantic_object=StructuredResponse)
        
        # Set up ChatPromptTemplate
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that provides comprehensive answers based on web search results, YouTube videos, and GitHub repositories.

Your task is to analyze the provided context and create a structured response that includes:
1. A comprehensive answer to the user's query
2. Relevant web search results
3. Relevant YouTube videos
4. Relevant GitHub repositories and code files
5. List of sources used

{format_instructions}"""),
            ("human", """User Query: {query}

Context from web sources:
{context}

Please provide a comprehensive answer based on the context above. If the context doesn't contain relevant information, provide a general answer."""),
        ])
    
    def get_response(self):
        """Generate structured response using Gemini with web-retrieved context"""
        try:
            # Retrieve structured context from web sources
            structured_context = self.retriever.retrieve_structured(self.state.query)
            
            # Convert structured data to context string for the prompt
            context_parts = []
            
            if structured_context['web_results']:
                web_context = "Web Search Results:\n"
                for result in structured_context['web_results']:
                    web_context += f"Title: {result['title']}\nURL: {result['url']}\nDescription: {result['description']}\n\n"
                context_parts.append(web_context)
            
            if structured_context['youtube_results']:
                youtube_context = "YouTube Results:\n"
                for result in structured_context['youtube_results']:
                    youtube_context += f"Title: {result['title']}\nChannel: {result['channel']}\nDuration: {result['duration']}\nURL: {result['url']}\nDescription: {result['description']}\nViews: {result['views']}\nPublished: {result['published']}\n\n"
                context_parts.append(youtube_context)
            
            if structured_context['github_repositories']:
                github_context = "GitHub Repositories:\n"
                for result in structured_context['github_repositories']:
                    github_context += f"Repository: {result['repository']}\nDescription: {result['description']}\nStars: {result['stars']}\nURL: {result['url']}\nRelevance: {result['relevance']} matching terms\n\n"
                context_parts.append(github_context)
            
            if structured_context['github_code']:
                code_context = "GitHub Code Files:\n"
                for result in structured_context['github_code']:
                    code_context += f"File: {result['file']}\nRepository: {result['repository']}\nURL: {result['url']}\nRelevance: {result['relevance']} matching terms\n\n"
                context_parts.append(code_context)
            
            full_context = "\n".join(context_parts) if context_parts else "No relevant information found."
            
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