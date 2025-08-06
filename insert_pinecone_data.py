# insert_pinecone_data.py
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import pinecone
from typing import List, Dict

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = "icleaf"  # Your index name
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions

class PineconeDataInserter:
    def __init__(self):
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize Pinecone
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        print("Initializing Pinecone...")
        self.pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(PINECONE_INDEX)
        
        print(f"Connected to Pinecone index: {PINECONE_INDEX}")
    
    def insert_sample_data(self):
        """Insert sample documents into Pinecone"""
        
        # Sample documents with various topics
        sample_documents = [
            {
                "id": "doc_001",
                "title": "Python Best Practices",
                "content": "Python best practices include using virtual environments, following PEP 8 style guidelines, writing docstrings, and using type hints. Always use meaningful variable names and write clean, readable code. Use list comprehensions for simple operations and consider performance implications for large datasets.",
                "source": "knowledge_base",
                "category": "programming",
                "tags": ["python", "best-practices", "coding", "development"]
            },
            {
                "id": "doc_002",
                "title": "Machine Learning Fundamentals",
                "content": "Machine learning fundamentals include supervised learning, unsupervised learning, and reinforcement learning. Key concepts include feature engineering, model selection, and evaluation metrics. Understanding bias-variance tradeoff is crucial for model performance.",
                "source": "training_material",
                "category": "ai",
                "tags": ["machine-learning", "ai", "algorithms", "data-science"]
            },
            {
                "id": "doc_003",
                "title": "Web Development with React",
                "content": "React is a popular JavaScript library for building user interfaces. Key concepts include components, props, state, and hooks. Use functional components with hooks for modern React development. Consider performance optimization with React.memo and useMemo.",
                "source": "knowledge_base",
                "category": "web-development",
                "tags": ["react", "javascript", "frontend", "web-development"]
            },
            {
                "id": "doc_004",
                "title": "Database Design Principles",
                "content": "Good database design principles include normalization, proper indexing, and relationship modeling. Choose appropriate data types and consider scalability. Use transactions for data integrity and implement proper backup strategies.",
                "source": "training_material",
                "category": "database",
                "tags": ["database", "sql", "design", "data-modeling"]
            },
            {
                "id": "doc_005",
                "title": "DevOps and CI/CD",
                "content": "DevOps practices include continuous integration, continuous deployment, and infrastructure as code. Use tools like Docker for containerization and Kubernetes for orchestration. Implement monitoring and logging for production systems.",
                "source": "knowledge_base",
                "category": "devops",
                "tags": ["devops", "ci-cd", "docker", "kubernetes"]
            },
            {
                "id": "doc_006",
                "title": "API Design Best Practices",
                "content": "RESTful API design principles include using proper HTTP methods, status codes, and resource naming. Implement authentication, rate limiting, and versioning. Document your APIs clearly and provide meaningful error messages.",
                "source": "training_material",
                "category": "api",
                "tags": ["api", "rest", "design", "web-services"]
            },
            {
                "id": "doc_007",
                "title": "Data Structures and Algorithms",
                "content": "Understanding data structures like arrays, linked lists, trees, and graphs is fundamental. Algorithm complexity analysis helps in choosing the right approach. Practice with common problems like sorting, searching, and dynamic programming.",
                "source": "knowledge_base",
                "category": "computer-science",
                "tags": ["algorithms", "data-structures", "complexity", "programming"]
            },
            {
                "id": "doc_008",
                "title": "Cloud Computing with AWS",
                "content": "AWS provides various services for cloud computing including EC2, S3, Lambda, and RDS. Understand the shared responsibility model and implement proper security practices. Use CloudFormation for infrastructure as code.",
                "source": "training_material",
                "category": "cloud",
                "tags": ["aws", "cloud", "infrastructure", "deployment"]
            },
            {
                "id": "doc_009",
                "title": "Testing Strategies",
                "content": "Comprehensive testing includes unit tests, integration tests, and end-to-end tests. Use test-driven development for better code quality. Implement automated testing in your CI/CD pipeline and maintain good test coverage.",
                "source": "knowledge_base",
                "category": "testing",
                "tags": ["testing", "tdd", "automation", "quality"]
            },
            {
                "id": "doc_010",
                "title": "Security Best Practices",
                "content": "Application security includes input validation, authentication, authorization, and data encryption. Follow OWASP guidelines and implement secure coding practices. Regular security audits and penetration testing are essential.",
                "source": "training_material",
                "category": "security",
                "tags": ["security", "authentication", "encryption", "owasp"]
            }
        ]
        
        print(f"Inserting {len(sample_documents)} documents into Pinecone...")
        
        success_count = 0
        for doc in sample_documents:
            try:
                # Generate embedding for the content
                content_embedding = self.embedding_model.encode(doc["content"]).tolist()
                
                # Prepare metadata
                metadata = {
                    'title': doc["title"],
                    'content': doc["content"],
                    'source': doc["source"],
                    'category': doc["category"],
                    'tags': doc["tags"]
                }
                
                # Upsert to Pinecone
                self.index.upsert(
                    vectors=[(doc["id"], content_embedding, metadata)]
                )
                
                print(f"✅ Inserted: {doc['title']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Failed to insert {doc['title']}: {e}")
        
        print(f"\n🎉 Successfully inserted {success_count}/{len(sample_documents)} documents!")
        return success_count
    
    def test_search(self, query: str = "python development"):
        """Test search functionality"""
        print(f"\n🔍 Testing search with query: '{query}'")
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )
            
            print(f"Found {len(results.matches)} results:")
            for i, match in enumerate(results.matches, 1):
                print(f"\n{i}. {match.metadata['title']}")
                print(f"   Score: {match.score:.3f}")
                print(f"   Category: {match.metadata['category']}")
                print(f"   Tags: {', '.join(match.metadata['tags'])}")
                print(f"   Content: {match.metadata['content'][:100]}...")
            
        except Exception as e:
            print(f"Search error: {e}")

def main():
    try:
        # Initialize inserter
        inserter = PineconeDataInserter()
        
        # Insert sample data
        success_count = inserter.insert_sample_data()
        
        if success_count > 0:
            # Test search functionality
            inserter.test_search("python development")
            inserter.test_search("machine learning")
            inserter.test_search("web development")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. PINECONE_API_KEY in your .env file")
        print("2. Internet connection to access Pinecone")
        print("3. Proper permissions for the index")

if __name__ == "__main__":
    main() 