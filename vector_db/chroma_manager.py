#!/usr/bin/env python3
"""
ChromaDB Manager for Vector Database
Handles document indexing and semantic search
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class ChromaManager:
    """Manages ChromaDB vector database for document search"""
    
    def __init__(self, persist_directory: str = "vector_db/chroma_data"):
        """Initialize ChromaDB with persistence"""
        self.persist_directory = persist_directory
        
        # Create ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use default embedding function (all-MiniLM-L6-v2)
        # This is a lightweight, fast, and good quality embedding model
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection_name = "business_documents"
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✅ Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Business documents for DecisionAI"}
            )
            print(f"✅ Created new collection: {self.collection_name}")
    
    def add_documents(self, documents: List[Dict[str, str]], chunk_size: int = 1000):
        """Add documents to the vector database with chunking"""
        from .document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        chunk_counter = 0
        
        for doc in documents:
            filename = doc['filename']
            text = doc['text']
            filetype = doc['filetype']
            
            # Chunk the document
            chunks = processor.chunk_text(text, chunk_size=chunk_size)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_chunk_{i}"
                all_chunks.append(chunk)
                all_metadatas.append({
                    'filename': filename,
                    'filetype': filetype,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                all_ids.append(chunk_id)
                chunk_counter += 1
        
        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i+batch_size]
            batch_metadatas = all_metadatas[i:i+batch_size]
            batch_ids = all_ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        print(f"✅ Added {chunk_counter} chunks from {len(documents)} documents")
        return chunk_counter
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documents using semantic similarity"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            
            if results and results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection_name
        }
    
    def reset_collection(self):
        """Delete and recreate the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"🗑️ Deleted collection: {self.collection_name}")
        except:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Business documents for DecisionAI"}
        )
        print(f"✅ Created new collection: {self.collection_name}")

if __name__ == "__main__":
    # Test
    manager = ChromaManager()
    print(manager.get_collection_stats())
