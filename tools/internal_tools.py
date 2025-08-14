from langchain.tools import BaseTool, StructuredTool
from retrievers.pinecone_retriever import PineconeRetriever
from typing import List, Dict, Any
import json

class InternalToolManager:
    def __init__(self):
        self.retriever = PineconeRetriever()
    
    def get_tools(self) -> List[BaseTool]:
        return [
            StructuredTool.from_function(
                func=self._retrieve_internal_knowledge,
                name="retrieve_internal_knowledge",
                description="Search internal knowledge base for relevant documents and information. Use this when the user asks about company policies, internal procedures, project documentation, or any internal knowledge."
            )
        ]
    
    def _retrieve_internal_knowledge(self, query: str) -> str:
        """Retrieve internal knowledge using PineconeRetriever"""
        try:
            structured_results = self.retriever.retrieve_structured(query)
            return json.dumps(structured_results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to retrieve internal knowledge: {str(e)}"})
