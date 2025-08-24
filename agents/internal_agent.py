# agents/internal_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from tools.internal_tools import InternalToolManager
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from config.models import InternalResponse, InternalDocument
from config.prompts import INTERNAL_AGENT_SYSTEM_PROMPT
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import MessagesPlaceholder
import json
import random
import re

class InternalAgent(BaseAgent):
    def __init__(self, state):
        super().__init__(state)
        # Configure Google Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )
        self._setup_tools()
        self._create_agent()
    
    def _setup_tools(self):
        """Set up internal tools"""
        tool_manager = InternalToolManager()
        self.tools = tool_manager.get_tools()
    
    def _create_agent(self):
        """Create agent with intelligent tool selection"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTERNAL_AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _starts_with_greeting(self, query: str) -> bool:
        """Returns True if the message starts with a greeting token."""
        pattern = r"^\s*(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening)\b"
        return re.search(pattern, query.lower()) is not None

    def _contains_question(self, query: str) -> bool:
        """Production-safe heuristic for detecting an actual question."""
        if "?" in query:
            return True
        interrogatives = (
            r"\b(who|what|when|where|why|how|which)\b",
            r"\b(can|could|would|should)\s+you\b",
            r"\b(tell me|show me|help me|need|find|explain)\b",
        )
        q = query.lower()
        return any(re.search(p, q) for p in interrogatives)

    def get_response(self):
        """Get response with intelligent tool selection"""
        try:
            user_query = (self.state.query or "").strip()

            # Fast path: pure greeting only (no need to call any tools)
            if self._is_greeting(user_query) and not self._contains_question(user_query):
                # Return greeting response without using tools
                greeting_responses = [
                    "Hello! How can I help you with internal knowledge today?",
                    "Hi there! I'm here to assist you with company information and internal resources.",
                    "Good to see you! What would you like to know about our internal knowledge base?",
                    "Hello! I'm ready to help you find information from our internal documents and resources."
                ]
                return {
                    "answer": random.choice(greeting_responses),
                    "source_document": None
                }
            
            # Greeting + question: greet then run internal knowledge pipeline
            greeting_prefix = ""
            if self._starts_with_greeting(user_query) and self._contains_question(user_query):
                greeting_prefix = random.choice([
                    "Hello! ",
                    "Hi! ",
                    "Hey! ",
                    "Good to see you! "
                ])
            
            # Use agent for knowledge queries
            result = self.executor.invoke({"input": user_query})
            
            # Parse the result to maintain UI compatibility
            try:
                # Try to parse as JSON if it's a structured response
                parsed_result = json.loads(result["output"])
                if greeting_prefix:
                    # Prepend greeting to the answer field if present
                    if isinstance(parsed_result, dict) and parsed_result.get("answer"):
                        parsed_result["answer"] = f"{greeting_prefix}{parsed_result['answer']}"
                return parsed_result
            except:
                # If not JSON, return as simple answer
                answer_text = result.get("output", "")
                if greeting_prefix:
                    answer_text = f"{greeting_prefix}{answer_text}"
                return {
                    "answer": answer_text,
                    "source_document": "internal_knowledge_base"
                }
                
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}", 
                "source_document": None
            }

def call_gemini_api(prompt):
    """Legacy function - kept for compatibility"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"