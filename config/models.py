# config/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class WebResult(BaseModel):
    title: str = Field(description="Title of the web result")
    url: str = Field(description="URL of the web result")
    description: str = Field(description="Description or snippet of the web result")

class YouTubeResult(BaseModel):
    title: str = Field(description="Title of the YouTube video")
    channel: str = Field(description="Channel name")
    duration: str = Field(description="Duration of the video")
    url: str = Field(description="YouTube video URL")
    description: str = Field(description="Video description")
    views: str = Field(description="Number of views")
    published: str = Field(description="Publication date")

class GitHubResult(BaseModel):
    repository: str = Field(description="Repository name")
    description: str = Field(description="Repository description")
    stars: int = Field(description="Number of stars")
    url: str = Field(description="GitHub repository URL")
    relevance: int = Field(description="Relevance score")

class CodeResult(BaseModel):
    file: str = Field(description="File path in repository")
    repository: str = Field(description="Repository name")
    url: str = Field(description="GitHub file URL")
    relevance: int = Field(description="Relevance score")

class StructuredResponse(BaseModel):
    answer: str = Field(description="Comprehensive answer to the user query")
    web_results: List[WebResult] = Field(description="List of web search results", default_factory=list)
    youtube_results: List[YouTubeResult] = Field(description="List of YouTube video results", default_factory=list)
    github_repositories: List[GitHubResult] = Field(description="List of GitHub repository results", default_factory=list)
    github_code: List[CodeResult] = Field(description="List of GitHub code results", default_factory=list)
    sources_used: List[str] = Field(description="List of sources used (web, youtube, github)", default_factory=list)

# Internal Agent Models
class InternalDocument(BaseModel):
    title: str = Field(description="Title of the internal document")
    content: str = Field(description="Content or snippet of the document")
    source: str = Field(description="Source of the document (e.g., knowledge_base, training_material)")
    relevance_score: float = Field(description="Relevance score (0-1)")
    metadata: Optional[dict] = Field(description="Additional metadata", default_factory=dict)

class InternalResponse(BaseModel):
    answer: str = Field(description="Comprehensive answer based on internal knowledge")
    internal_documents: List[InternalDocument] = Field(description="List of relevant internal documents", default_factory=list)
    confidence_score: float = Field(description="Confidence score of the response (0-1)")
    related_topics: List[str] = Field(description="List of related topics or concepts", default_factory=list)
    sources_used: List[str] = Field(description="List of internal sources used", default_factory=list) 