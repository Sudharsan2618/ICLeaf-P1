# agents/external_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from tools.external_tools import ExternalToolManager
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from config.models import StructuredResponse, WebResult, YouTubeResult, GitHubResult
from config.prompts import EXTERNAL_AGENT_SYSTEM_PROMPT
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import MessagesPlaceholder
import json
import random

class ExternalAgent(BaseAgent):
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
        """Set up external tools"""
        tool_manager = ExternalToolManager()
        self.tools = tool_manager.get_tools()
    
    def _create_agent(self):
        """Create agent with intelligent tool selection"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTERNAL_AGENT_SYSTEM_PROMPT),
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
    
    def get_response(self):
        """Get response with intelligent tool selection"""
        try:
            # Check if query is a greeting
            if self._is_greeting(self.state.query):
                # Return greeting response without using tools
                greeting_responses = [
                    "Hello! I'm here to help you with research and external information.",
                    "Hi there! I can search the web, YouTube, and GitHub to find information for you.",
                    "Good to see you! What would you like to research today?",
                    "Hello! I'm ready to help you find current information from external sources."
                ]
                return {
                    "answer": random.choice(greeting_responses),
                    "web_results": [],
                    "youtube_results": [],
                    "github_repositories": [],
                    "sources_used": []
                }
            
            # Use agent for research queries
            result = self.executor.invoke({"input": self.state.query})

            # Default empty payload
            payload = {
                "answer": "",
                "web_results": [],
                "youtube_results": [],
                "github_repositories": [],  # kept for UI compatibility but empty
                "sources_used": []
            }

            # Prefer the model's final text as summary
            payload["answer"] = result.get("output", "")

            # Try to parse structured JSON directly from output
            try:
                direct = result.get("output", "").strip()
                # Strip code fences if present
                if direct.startswith("```"):
                    direct = direct.strip("`\n ")
                    # after stripping language hints, find first '{'
                    brace_idx = direct.find('{')
                    if brace_idx != -1:
                        direct = direct[brace_idx:]
                parsed = json.loads(direct)
                payload["web_results"] = parsed.get("web_results", [])
                payload["youtube_results"] = parsed.get("youtube_results", [])
                payload["sources_used"] = [s for s in parsed.get("sources_used", []) if s in ("web", "youtube")]
                # Ensure github list is empty
                payload["github_repositories"] = []
                # If parsed also included an answer, prefer it
                if parsed.get("answer"):
                    payload["answer"] = parsed["answer"]
                return payload
            except Exception:
                pass

            # Fallback: try to parse tool observations from intermediate steps
            steps = result.get("intermediate_steps", [])
            if steps:
                # steps may be list of tuples (AgentAction, observation) or dicts
                for step in steps:
                    observation = None
                    if isinstance(step, (list, tuple)) and len(step) >= 2:
                        observation = step[1]
                    elif isinstance(step, dict):
                        observation = step.get("observation") or step.get("output")
                    if not observation:
                        continue
                    if isinstance(observation, str):
                        try:
                            parsed = json.loads(observation)
                            payload["web_results"] = parsed.get("web_results", [])
                            payload["youtube_results"] = parsed.get("youtube_results", [])
                            payload["sources_used"] = [s for s in parsed.get("sources_used", []) if s in ("web", "youtube")]
                            payload["github_repositories"] = []
                            break
                        except Exception:
                            continue

            # Ensure answer is not empty
            if not payload["answer"]:
                payload["answer"] = "Here are relevant web and YouTube results."
            return payload
                
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "web_results": [],
                "youtube_results": [],
                "github_repositories": [],
                "sources_used": []
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