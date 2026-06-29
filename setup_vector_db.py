#!/usr/bin/env python3
"""
Setup Vector Database with Business Documents
Indexes all PDF, DOCX, and XLSX files into ChromaDB
"""

from vector_db.document_processor import DocumentProcessor
from vector_db.chroma_manager import ChromaManager

def main():
    print("="*80)
    print("📚 SETTING UP VECTOR DATABASE")
    print("="*80)
    
    # Step 1: Process documents
    print("\n📄 Step 1: Processing documents...")
    processor = DocumentProcessor(docs_directory="business_documents")
    documents = processor.process_all_documents()
    
    if not documents:
        print("❌ No documents found to process!")
        return
    
    print(f"\n✅ Processed {len(documents)} documents")
    
    # Step 2: Initialize ChromaDB
    print("\n💾 Step 2: Initializing ChromaDB...")
    chroma = ChromaManager()
    
    # Reset if exists (for fresh setup)
    print("\n🔄 Resetting collection for fresh indexing...")
    chroma.reset_collection()
    
    # Step 3: Index documents
    print("\n📊 Step 3: Indexing documents into vector database...")
    total_chunks = chroma.add_documents(documents, chunk_size=1000)
    
    # Step 4: Verify
    print("\n✅ Step 4: Verification...")
    stats = chroma.get_collection_stats()
    print(f"   Total chunks indexed: {stats['total_chunks']}")
    print(f"   Collection name: {stats['collection_name']}")
    
    # Step 5: Test search
    print("\n🔍 Step 5: Testing search functionality...")
    test_queries = [
        "What is our expansion strategy for Netherlands?",
        "What is our hiring budget?",
        "What features do users want most?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = chroma.search(query, n_results=2)
        if results:
            print(f"   Found {len(results)} relevant chunks:")
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result['metadata']['filename']} (chunk {result['metadata']['chunk_index']})")
                print(f"         Preview: {result['text'][:100]}...")
        else:
            print("   No results found")
    
    print("\n" + "="*80)
    print("✅ VECTOR DATABASE SETUP COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Documents processed: {len(documents)}")
    print(f"   Total chunks indexed: {total_chunks}")
    print(f"   Vector DB location: vector_db/chroma_data/")
    print(f"\n🎉 Ready to integrate with AI agent!")

if __name__ == "__main__":
    main()
