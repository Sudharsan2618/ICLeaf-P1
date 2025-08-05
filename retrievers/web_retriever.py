# retrievers/web_retriever.py
import requests
from typing import List, Dict
from ddgs import DDGS
from googleapiclient.discovery import build
from github import Github, Auth
from config.settings import GITHUB_TOKEN, YOUTUBE_API_KEY, MAX_SEARCH_RESULTS, MAX_CONTEXT_LENGTH

class WebRetriever:
    def __init__(self):
        # Use the new authentication method
        if GITHUB_TOKEN:
            auth = Auth.Token(GITHUB_TOKEN)
            self.github_client = Github(auth=auth)
        else:
            self.github_client = None
        
        # Initialize YouTube API client
        if YOUTUBE_API_KEY:
            self.youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        else:
            self.youtube_client = None
    
    def retrieve(self, query: str) -> str:
        """Retrieve context from web, YouTube, and GitHub sources"""
        context_parts = []
        
        # Web search
        web_results = self._web_search(query)
        if web_results:
            context_parts.append("Web Search Results:\n" + web_results)
        
        # YouTube search
        youtube_results = self._youtube_search(query)
        if youtube_results:
            context_parts.append("YouTube Results:\n" + youtube_results)
        
        # GitHub search
        github_results = self._github_search(query)
        if github_results:
            context_parts.append("GitHub Results:\n" + github_results)
        
        # Combine all results
        full_context = "\n\n".join(context_parts)
        
        # Truncate if too long
        if len(full_context) > MAX_CONTEXT_LENGTH:
            full_context = full_context[:MAX_CONTEXT_LENGTH] + "..."
        
        return full_context if full_context else "No relevant information found."
    
    def _web_search(self, query: str) -> str:
        """Perform web search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
                
                if not results:
                    return ""
                
                formatted_results = []
                for result in results:
                    formatted_results.append(f"Title: {result.get('title', 'N/A')}\n"
                                           f"URL: {result.get('link', 'N/A')}\n"
                                           f"Description: {result.get('body', 'N/A')}\n")
                
                return "\n".join(formatted_results)
        except Exception as e:
            print(f"Web search error: {e}")
            return ""
    
    def _youtube_search(self, query: str) -> str:
        """Search YouTube videos using the official YouTube Data API v3"""
        if not self.youtube_client:
            print("YouTube API key not configured")
            return ""
        
        try:
            # Search for videos using the YouTube Data API v3
            search_response = self.youtube_client.search().list(
                q=query,
                part='id,snippet',
                maxResults=MAX_SEARCH_RESULTS,
                type='video',
                order='relevance'
            ).execute()
            
            if not search_response.get('items'):
                return ""
            
            # Get video IDs for detailed information
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video information
            videos_response = self.youtube_client.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            formatted_results = []
            for video in videos_response.get('items', []):
                try:
                    snippet = video.get('snippet', {})
                    content_details = video.get('contentDetails', {})
                    statistics = video.get('statistics', {})
                    
                    # Format duration from ISO 8601 format
                    duration = content_details.get('duration', 'N/A')
                    if duration != 'N/A':
                        # Convert ISO 8601 duration to readable format
                        import re
                        duration_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                        if duration_match:
                            hours, minutes, seconds = duration_match.groups()
                            duration_parts = []
                            if hours and hours != '0':
                                duration_parts.append(f"{hours}h")
                            if minutes and minutes != '0':
                                duration_parts.append(f"{minutes}m")
                            if seconds and seconds != '0':
                                duration_parts.append(f"{seconds}s")
                            duration = ' '.join(duration_parts) if duration_parts else 'N/A'
                    
                    formatted_results.append(f"Title: {snippet.get('title', 'N/A')}\n"
                                           f"Channel: {snippet.get('channelTitle', 'N/A')}\n"
                                           f"Duration: {duration}\n"
                                           f"URL: https://www.youtube.com/watch?v={video.get('id', 'N/A')}\n"
                                           f"Description: {snippet.get('description', 'N/A')[:200]}...\n"
                                           f"Views: {statistics.get('viewCount', 'N/A')}\n"
                                           f"Published: {snippet.get('publishedAt', 'N/A')}\n")
                except Exception as video_error:
                    # Skip individual videos that cause errors
                    print(f"Error processing video: {video_error}")
                    continue
            
            return "\n".join(formatted_results)
        except Exception as e:
            print(f"YouTube search error: {e}")
            return ""
    
    def _github_search(self, query: str) -> str:
        """Search GitHub repositories and code with relevance filtering"""
        if not self.github_client:
            return ""
        
        # Define programming/technical keywords that make GitHub searches relevant
        programming_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'laravel',
            'api', 'library', 'framework', 'tool', 'script', 'bot', 'automation',
            'algorithm', 'data structure', 'machine learning', 'ai', 'ml', 'neural',
            'database', 'sql', 'nosql', 'redis', 'mongodb', 'postgresql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'cloud',
            'git', 'github', 'gitlab', 'ci/cd', 'deployment', 'devops',
            'mobile', 'android', 'ios', 'flutter', 'react native',
            'web', 'frontend', 'backend', 'fullstack', 'microservices'
        ]
        
        # Check if query contains programming-related terms
        query_lower = query.lower()
        is_programming_query = any(keyword in query_lower for keyword in programming_keywords)
        
        # If it's not a programming-related query, skip GitHub search
        if not is_programming_query:
            return ""
        
        try:
            # Search repositories with better filtering
            repos = self.github_client.search_repositories(
                query=query, 
                sort="stars", 
                order="desc"
            )
            repo_results = []
            
            for repo in repos[:MAX_SEARCH_RESULTS]:
                # Additional relevance check
                repo_name_lower = repo.full_name.lower()
                repo_desc_lower = (repo.description or "").lower()
                
                # Check if repository name or description contains query terms
                query_terms = query_lower.split()
                relevance_score = sum(1 for term in query_terms if term in repo_name_lower or term in repo_desc_lower)
                
                # Only include if it has some relevance
                if relevance_score > 0:
                    repo_results.append(f"Repository: {repo.full_name}\n"
                                      f"Description: {repo.description or 'N/A'}\n"
                                      f"Stars: {repo.stargazers_count}\n"
                                      f"URL: {repo.html_url}\n"
                                      f"Relevance: {relevance_score} matching terms\n")
            
            # Search code with better filtering
            code_results = self.github_client.search_code(query=query)
            code_list = []
            
            for code in code_results[:MAX_SEARCH_RESULTS]:
                # Check if the file path or repository name is relevant
                file_path_lower = code.path.lower()
                repo_name_lower = code.repository.full_name.lower()
                
                query_terms = query_lower.split()
                relevance_score = sum(1 for term in query_terms if term in file_path_lower or term in repo_name_lower)
                
                # Only include if it has some relevance
                if relevance_score > 0:
                    code_list.append(f"File: {code.repository.full_name}/{code.path}\n"
                                   f"Repository: {code.repository.full_name}\n"
                                   f"URL: {code.html_url}\n"
                                   f"Relevance: {relevance_score} matching terms\n")
            
            github_results = []
            if repo_results:
                github_results.append("Top Repositories:\n" + "\n".join(repo_results))
            if code_list:
                github_results.append("Code Results:\n" + "\n".join(code_list))
            
            return "\n\n".join(github_results)
        except Exception as e:
            print(f"GitHub search error: {e}")
            return ""