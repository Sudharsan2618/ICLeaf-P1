# agents/base_agent.py
from config.prompts import ROLE_PROMPTS

class BaseAgent:
    def __init__(self, state):
        self.state = state
        self.system_prompt = ROLE_PROMPTS.get(state.role, "")

    def get_response(self):
        raise NotImplementedError  # To be implemented by subclasses