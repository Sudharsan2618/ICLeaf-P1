# utils/state.py

class QueryState:
    def __init__(self, role, mode, query):
        self.role = role  # User role: learner, trainer, admin
        self.mode = mode  # Query mode: internal or external
        self.query = query  # User's question