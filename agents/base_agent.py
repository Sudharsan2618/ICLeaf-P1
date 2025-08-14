# agents/base_agent.py
from config.prompts import ROLE_PROMPTS
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from typing import List
import re

class BaseAgent:
    def __init__(self, state):
        self.state = state
        self.system_prompt = ROLE_PROMPTS.get(state.role, "")
        self.tools = []
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.agent = None
        self.executor = None
        self.llm = None

    def _setup_tools(self):
        """Override in subclasses to set up specific tools"""
        pass
    
    def _create_agent(self):
        """Create LangChain agent with tools"""
        pass
    
    def _is_greeting(self, query: str) -> bool:
        """Determine if query is a greeting using pattern matching"""
        greeting_patterns = [
            r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
            r'\bhow are you\b',
            r'\bwhat\'s up\b',
            r'\bthanks? you\b',
            r'\bgoodbye|bye\b',
            r'\bsee you\b'
        ]
        return any(re.search(pattern, query.lower()) for pattern in greeting_patterns)

    def get_response(self):
        raise NotImplementedError  # To be implemented by subclasses