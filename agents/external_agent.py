# agents/external_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agents.base_agent import BaseAgent
from retrievers.web_retriever import WebRetriever
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

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
    
    def get_response(self):
        """Generate response using Gemini with web-retrieved context"""
        try:
            # Retrieve context from web sources
            context = self.retriever.retrieve(self.state.query)
            
            # Compose the prompt with system message and context
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                User Query: {self.state.query}
                
                Context from web sources:
                {context}
                
                Please provide a comprehensive answer based on the context above. 
                If the context doesn't contain relevant information, provide a general answer.
                """)
            ]
            
            # Generate response using Gemini
            response = self.model.invoke(messages)
            return response.content
            
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