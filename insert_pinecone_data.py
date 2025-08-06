# insert_pinecone_data.py
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import pinecone
from typing import List, Dict
import PyPDF2
import uuid

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
    
    def insert_pdf_data(self, pdf_path: str, chunk_size: int = 500, overlap: int = 50):
        """Extracts text from a PDF, chunks it, embeds, and inserts into Pinecone."""


        print(f"Reading PDF: {pdf_path}")
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

        # Chunk the text
        def chunk_text(text, chunk_size, overlap):
            words = text.split()
            chunks = []
            i = 0
            while i < len(words):
                chunk = words[i:i+chunk_size]
                chunks.append(' '.join(chunk))
                i += chunk_size - overlap
            return chunks

        chunks = chunk_text(full_text, chunk_size, overlap)
        print(f"Extracted {len(chunks)} chunks from PDF.")

        success_count = 0
        for idx, chunk in enumerate(chunks):
            try:
                embedding = self.embedding_model.encode(chunk).tolist()
                metadata = {
                    'source': pdf_path,
                    'chunk_index': idx,
                    'content': chunk
                }
                vector_id = str(uuid.uuid4())
                self.index.upsert(vectors=[(vector_id, embedding, metadata)])
                print(f"✅ Inserted chunk {idx+1}/{len(chunks)}")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to insert chunk {idx+1}: {e}")
        print(f"\n🎉 Successfully inserted {success_count}/{len(chunks)} PDF chunks!")
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

        # Insert PDF data (update the path to your PDF file)
        pdf_path = "sample.pdf"  # <-- Change this to your PDF file path
        inserter.insert_pdf_data(pdf_path)

        # Optionally, test search functionality
        inserter.test_search("Explain about autonomous AI Agents?")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. PINECONE_API_KEY in your .env file")
        print("2. Internet connection to access Pinecone")
        print("3. Proper permissions for the index")

if __name__ == "__main__":
    main() 