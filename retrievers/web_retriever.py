# retrievers/web_retriever.py
import requests
import time
from typing import List, Dict, Tuple
from ddgs import DDGS
from googleapiclient.discovery import build
from github import Github, Auth
from github.GithubException import RateLimitExceededException, BadCredentialsException
from config.settings import GITHUB_TOKEN, YOUTUBE_API_KEY, MAX_SEARCH_RESULTS, MAX_CONTEXT_LENGTH

class WebRetriever:
    def __init__(self):
        # Use the new authentication method
        if GITHUB_TOKEN:
            try:
                auth = Auth.Token(GITHUB_TOKEN)
                self.github_client = Github(auth=auth)
                # Test the token by making a simple API call
                self.github_client.get_user()
                print("GitHub authentication successful")
            except BadCredentialsException:
                print("GitHub token is invalid or expired")
                self.github_client = None
            except Exception as e:
                print(f"GitHub authentication error: {e}")
                self.github_client = None
        else:
            print("GitHub token not configured")
            self.github_client = None
        
        # Initialize YouTube API client
        if YOUTUBE_API_KEY:
            self.youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        else:
            self.youtube_client = None
    
    def _check_github_rate_limit(self):
        """Check GitHub rate limit and wait if necessary"""
        if not self.github_client:
            return False
        
        try:
            rate_limit = self.github_client.get_rate_limit()
            
            # Try different ways to access search rate limit
            search_limit = None
            if hasattr(rate_limit, 'search'):
                search_limit = rate_limit.search
            elif hasattr(rate_limit, 'core'):
                # Fallback to core rate limit
                search_limit = rate_limit.core
                print("⚠️  Using core rate limit as fallback")
            else:
                print("⚠️  Could not determine rate limit structure")
                return True  # Continue anyway
            
            if search_limit:
                remaining = search_limit.remaining
                reset_time = search_limit.reset
                
                if remaining <= 0:
                    wait_time = (reset_time - time.time()) + 60  # Add 60 seconds buffer
                    if wait_time > 0:
                        print(f"GitHub rate limit exceeded. Waiting {wait_time:.0f} seconds...")
                        time.sleep(wait_time)
                    return True
                return True
            else:
                print("⚠️  Rate limit information unavailable, continuing...")
                return True
                
        except Exception as e:
            print(f"Error checking GitHub rate limit: {e}")
            print("Continuing with search anyway...")
            return True
    
    def retrieve_structured(self, query: str) -> Dict:
        """Retrieve structured context from web, YouTube, and GitHub sources"""
        results = {
            'web_results': [],
            'youtube_results': [],
            'github_repositories': [],
            'sources_used': []
        }
        
        # Web search (most reliable, try first)
        try:
            web_results = self._web_search_structured(query)
            if web_results:
                results['web_results'] = web_results
                results['sources_used'].append('web')
                print(f"✅ Web search successful: {len(web_results)} results")
            else:
                print("⚠️ Web search returned no results")
        except Exception as e:
            print(f"❌ Web search failed: {e}")
        
        # YouTube search
        try:
            youtube_results = self._youtube_search_structured(query)
            if youtube_results:
                results['youtube_results'] = youtube_results
                results['sources_used'].append('youtube')
                print(f"✅ YouTube search successful: {len(youtube_results)} results")
            else:
                print("⚠️ YouTube search returned no results")
        except Exception as e:
            print(f"❌ YouTube search failed: {e}")
        
        # GitHub repository search only (removed code search to avoid 403 errors)
        try:
            github_repos = self._github_search_repositories_only(query)
            if github_repos:
                results['github_repositories'] = github_repos
                results['sources_used'].append('github')
                print(f"✅ GitHub repository search successful: {len(github_repos)} results")
            else:
                print("⚠️ GitHub repository search returned no results")
                
        except Exception as e:
            print(f"❌ GitHub search failed: {e}")
            print("Continuing with other sources...")
        
        # Ensure we have at least some results
        if not any([results['web_results'], results['youtube_results'], results['github_repositories']]):
            print("⚠️ No sources returned results, this might indicate a configuration issue")
        
        return results
    
    def retrieve(self, query: str) -> str:
        """Legacy method - kept for compatibility"""
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
    
    def _web_search_structured(self, query: str) -> List[Dict]:
        """Perform web search using DuckDuckGo and return structured data"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
                
                if not results:
                    return []
                
                structured_results = []
                for result in results:
                    structured_results.append({
                        'title': result.get('title', 'N/A'),
                        'url': result.get('link', 'N/A'),
                        'description': result.get('body', 'N/A')
                    })
                
                return structured_results
        except Exception as e:
            print(f"Web search error: {e}")
            return []
    
    def _youtube_search_structured(self, query: str) -> List[Dict]:
        """Search YouTube videos and return structured data"""
        if not self.youtube_client:
            print("YouTube API key not configured")
            return []
        
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
                return []
            
            # Get video IDs for detailed information
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video information
            videos_response = self.youtube_client.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            structured_results = []
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
                    
                    # Ensure views field is always present and valid
                    views = statistics.get('viewCount')
                    if views is None or views == '':
                        views = '0'
                    else:
                        views = str(views)
                    
                    structured_results.append({
                        'title': snippet.get('title', 'N/A'),
                        'channel': snippet.get('channelTitle', 'N/A'),
                        'duration': duration,
                        'url': f"https://www.youtube.com/watch?v={video.get('id', 'N/A')}",
                        'description': snippet.get('description', 'N/A')[:200] + "..." if len(snippet.get('description', '')) > 200 else snippet.get('description', 'N/A'),
                        'views': views,  # Always ensure views is present
                        'published': snippet.get('publishedAt', 'N/A')
                    })
                except Exception as video_error:
                    # Skip individual videos that cause errors
                    print(f"Error processing video: {video_error}")
                    continue
            
            return structured_results
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    def _github_search_repositories_only(self, query: str) -> List[Dict]:
        """Search GitHub repositories with relevance filtering, return structured data"""
        if not self.github_client:
            return []
        
        # Check rate limit before proceeding
        if not self._check_github_rate_limit():
            print("GitHub rate limit check failed, skipping GitHub search")
            return []
        
        query_lower = query.lower()
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
        is_programming_query = any(keyword in query_lower for keyword in programming_keywords)
        if not is_programming_query:
            return []
        
        try:
            print(f"Searching GitHub repositories for: {query}")
            repos = self.github_client.search_repositories(
                query=query, 
                sort="stars", 
                order="desc"
            )
            repo_results = []
            repos_list = list(repos) if repos is not None else []
            for repo in repos_list[:MAX_SEARCH_RESULTS]:
                repo_name_lower = repo.full_name.lower()
                repo_desc_lower = (repo.description or "").lower()
                query_terms = query_lower.split()
                relevance_score = sum(1 for term in query_terms if term in repo_name_lower or term in repo_desc_lower)
                if relevance_score > 0:
                    # Ensure all required fields are present and valid
                    repo_data = {
                        'repository': repo.full_name or 'N/A',
                        'description': repo.description or 'N/A',
                        'stars': int(repo.stargazers_count) if repo.stargazers_count is not None else 0,
                        'url': repo.html_url or 'N/A',
                        'relevance': int(relevance_score)
                    }
                    
                    # Validate that all required fields are present
                    if all(repo_data.values()) and repo_data['repository'] != 'N/A' and repo_data['url'] != 'N/A':
                        repo_results.append(repo_data)
            return repo_results
            
        except RateLimitExceededException:
            print("GitHub repository search rate limit exceeded")
            return []
        except Exception as e:
            print(f"GitHub search error: {e}")
            return []

    # Legacy methods for compatibility
    def _web_search(self, query: str) -> str:
        """Legacy method - Perform web search using DuckDuckGo"""
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
        """Legacy method - Search YouTube videos using the official YouTube Data API v3"""
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
                    
                    # Ensure views field is always present and valid
                    views = statistics.get('viewCount')
                    if views is None or views == '':
                        views = '0'
                    else:
                        views = str(views)
                    
                    formatted_results.append(f"Title: {snippet.get('title', 'N/A')}\n"
                                           f"Channel: {snippet.get('channelTitle', 'N/A')}\n"
                                           f"Duration: {duration}\n"
                                           f"URL: https://www.youtube.com/watch?v={video.get('id', 'N/A')}\n"
                                           f"Description: {snippet.get('description', 'N/A')[:200]}...\n"
                                           f"Views: {views}\n"
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
        """Legacy method - Search GitHub repositories with relevance filtering (code search removed)"""
        if not self.github_client:
            return ""
        
        # Check rate limit before proceeding
        if not self._check_github_rate_limit():
            print("GitHub rate limit check failed, skipping GitHub search")
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
            print(f"Searching GitHub repositories for: {query}")
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
            
            if repo_results:
                return "Top Repositories:\n" + "\n".join(repo_results)
            else:
                return ""
            
        except RateLimitExceededException:
            print("GitHub repository search rate limit exceeded")
            return "GitHub search temporarily unavailable due to rate limiting. Please try again later."
        except Exception as e:
            print(f"GitHub search error: {e}")
            return ""