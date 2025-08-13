# agents/external_agent.py
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from agents.base_agent import BaseAgent
from retrievers.web_retriever import WebRetriever
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from config.models import StructuredResponse, WebResult, YouTubeResult, GitHubResult

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
2. Relevant web search results (with title, url, description)
3. Relevant YouTube videos (with title, channel, duration, url, description, views, published)
4. Relevant GitHub repositories (with repository, description, stars, url, relevance)
5. List of sources used

IMPORTANT: Ensure ALL required fields are present for each result. Do not truncate or omit any fields.
For GitHub repositories, make sure each entry has: repository, description, stars (as integer), url, and relevance (as integer).
For web results, ensure each entry has: title, url, description.
For YouTube results, ensure each entry has: title, channel, duration, url, description, views, published.

DO NOT include any results with missing or incomplete fields. It's better to have fewer complete results than incomplete ones.

{format_instructions}"""),
            ("human", """User Query: {query}

Context from web sources:
{context}

Please provide a comprehensive answer based on the context above. If the context doesn't contain relevant information, provide a general answer.

IMPORTANT: Ensure all structured data is complete with all required fields for each result type."""),
        ])
    
    def get_response(self):
        """Generate structured response using Gemini with web-retrieved context"""
        try:
            # Retrieve structured context from web sources
            print(f"Retrieving context for query: {self.state.query}")
            structured_context = self.retriever.retrieve_structured(self.state.query)
            
            # Convert structured data to context string for the prompt
            context_parts = []
            
            if structured_context['web_results']:
                web_context = "Web Search Results:\n"
                valid_web_results = []
                for result in structured_context['web_results']:
                    # Validate that all required fields are present
                    if all(key in result and result[key] is not None for key in ['title', 'url', 'description']):
                        web_context += f"Title: {result['title']}\nURL: {result['url']}\nDescription: {result['description']}\n\n"
                        valid_web_results.append(result)
                    else:
                        print(f"Skipping invalid web result: {result}")
                
                # Update the structured context with only valid results
                structured_context['web_results'] = valid_web_results
                context_parts.append(web_context)
                print(f"Found {len(valid_web_results)} valid web results")
            
            if structured_context['youtube_results']:
                youtube_context = "YouTube Results:\n"
                valid_youtube_results = []
                for result in structured_context['youtube_results']:
                    # Validate that all required fields are present
                    required_fields = ['title', 'channel', 'duration', 'url', 'description', 'views', 'published']
                    if all(key in result and result[key] is not None for key in required_fields):
                        youtube_context += f"Title: {result['title']}\nChannel: {result['channel']}\nDuration: {result['duration']}\nURL: {result['url']}\nDescription: {result['description']}\nViews: {result['views']}\nPublished: {result['published']}\n\n"
                        valid_youtube_results.append(result)
                    else:
                        print(f"Skipping invalid YouTube result: {result}")
                
                # Update the structured context with only valid results
                structured_context['youtube_results'] = valid_youtube_results
                context_parts.append(youtube_context)
                print(f"Found {len(valid_youtube_results)} valid YouTube results")
            
            if structured_context['github_repositories']:
                github_context = "GitHub Repositories:\n"
                valid_github_results = []
                for result in structured_context['github_repositories']:
                    # Validate that all required fields are present
                    if all(key in result and result[key] is not None for key in ['repository', 'description', 'stars', 'url', 'relevance']):
                        github_context += f"Repository: {result['repository']}\nDescription: {result['description']}\nStars: {result['stars']}\nURL: {result['url']}\nRelevance: {result['relevance']} matching terms\n\n"
                        valid_github_results.append(result)
                    else:
                        print(f"Skipping invalid GitHub result: {result}")
                
                # Update the structured context with only valid results
                structured_context['github_repositories'] = valid_github_results
                context_parts.append(github_context)
                print(f"Found {len(valid_github_results)} valid GitHub repositories")
            
            # Log sources used
            if structured_context['sources_used']:
                print(f"Sources used: {', '.join(structured_context['sources_used'])}")
            else:
                print("No sources were successfully retrieved")
            
            full_context = "\n".join(context_parts) if context_parts else "No relevant information found."
            
            # Create the prompt with format instructions
            prompt = self.prompt_template.partial(
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Generate response using Gemini
            print("Generating response with Gemini...")
            try:
                chain = prompt | self.model | self.parser
                response = chain.invoke({
                    "query": self.state.query,
                    "context": full_context
                })
                
                # Convert the structured response to JSON
                return response.model_dump_json(indent=2)
            except Exception as parse_error:
                print(f"Parsing error: {parse_error}")
                # Fallback: try to generate a simpler response without structured parsing
                try:
                    # Generate a simple text response
                    simple_prompt = f"""Based on the following context, provide a comprehensive answer to: {self.state.query}

Context:
{full_context}

Answer:"""
                    
                    simple_response = self.model.invoke(simple_prompt)
                    return {
                        "answer": simple_response.content if hasattr(simple_response, 'content') else str(simple_response),
                        "web_results": structured_context.get('web_results', []),
                        "youtube_results": structured_context.get('youtube_results', []),
                        "github_repositories": structured_context.get('github_repositories', []),
                        "sources_used": structured_context.get('sources_used', [])
                    }
                except Exception as fallback_error:
                    print(f"Fallback error: {fallback_error}")
                    # Final fallback: return a basic response with available data
                    return {
                        "answer": f"Unable to generate a comprehensive response due to parsing errors. Here's what I found: {full_context[:500]}...",
                        "web_results": structured_context.get('web_results', []),
                        "youtube_results": structured_context.get('youtube_results', []),
                        "github_repositories": structured_context.get('github_repositories', []),
                        "sources_used": structured_context.get('sources_used', []),
                        "error": True,
                        "error_message": str(parse_error)
                    }
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            # Return a structured error response
            return {
                "error": True,
                "message": error_msg,
                "query": self.state.query,
                "sources_used": [],
                "answer": "Unable to generate response due to an error. Please check your API keys and try again."
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