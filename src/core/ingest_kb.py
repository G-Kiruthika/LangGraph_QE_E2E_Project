import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# pyrefly: ignore [missing-import]
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def build_vector_store():
    hf_embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=75)
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    orangeHRM_domain_file = os.path.join(base_dir, "src", "knowledge_base", "orangehrm-dashboard-kb.txt")
    #other_file = os.path.join(base_dir, "knowledge_base", "other_domain_kb", "some_other_manual.txt")
    persist_dir = os.path.join(base_dir, "vector_store") 
    
    all_splits = []

    # 1. Load OrangeHRM KB and attach metadata
    if os.path.exists(orangeHRM_domain_file):
        orangeHRM_domain_splits = splitter.split_documents(TextLoader(orangeHRM_domain_file).load())
        for doc in orangeHRM_domain_splits:
            doc.metadata["domain"] = "orangeHRM_domain"
        all_splits.extend(orangeHRM_domain_splits)
        print(f"Loaded {len(orangeHRM_domain_splits)} chunks from OrangeHRM KB")

    # 2. Load Other KB and attach metadata
    # if os.path.exists(other_file):
    #     other_splits = splitter.split_documents(TextLoader(other_file).load())
    #     for doc in other_splits:
    #         doc.metadata["domain"] = "other"
    #     all_splits.extend(other_splits)
    #     print(f"Loaded {len(other_splits)} chunks from Other KB")

    # 3. Save all documents to the single Chroma vector store on disk
    if all_splits:
        chroma_db=Chroma.from_documents(
            documents=all_splits, 
            embedding=hf_embeddings,
            persist_directory=persist_dir
        )
        print(f"Successfully saved vector database to {persist_dir}")

if __name__ == "__main__":
    build_vector_store()
