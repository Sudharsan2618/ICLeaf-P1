from langchain.tools import BaseTool, StructuredTool
from retrievers.web_retriever import WebRetriever
from typing import List, Dict, Any
import json

class ExternalToolManager:
    def __init__(self):
        self.retriever = WebRetriever()
    
    def get_tools(self) -> List[BaseTool]:
        return [
            StructuredTool.from_function(
                func=self._search_web_sources,
                name="search_web_sources", 
                description="Search the web and YouTube for current information. Use this when the user asks for research, latest information, tutorials, best practices, or external knowledge."
            )
        ]
    
    def _search_web_sources(self, query: str) -> str:
        """Search external sources using WebRetriever"""
        try:
            structured_results = self.retriever.retrieve_structured(query)
            return json.dumps(structured_results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to search external sources: {str(e)}"})
