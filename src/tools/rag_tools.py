import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools.retriever import create_retriever_tool

# Setup paths and embeddings
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
persist_dir = os.path.join(base_dir, "vector_store")
hf_embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Connect to the existing vector store on disk (does NOT re-embed text)
vectorstore = Chroma(persist_directory=persist_dir, embedding_function=hf_embeddings)

from langchain_core.tools import tool

# 1. Isolated agent tool for the Scenario Generator (Carnival Domain)
@tool("search_orangeHRM_kb")
def orangehrmDomain_kb_tool(query: str) -> str:
    """Searches the OrangeHRM knowledge base. Use this to get the context of the domain before generating test scenarios."""
    print(f"\n[DEBUG] 🔍 AGENT IS SEARCHING KNOWLEDGE BASE FOR: {query}\n")
    retriever = vectorstore.as_retriever(search_kwargs={"filter": {"domain": "orangeHRM_domain"}, "k": 3})
    docs = retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs])

# 2. Isolated agent tool for another agent
# other_kb_tool = create_retriever_tool(
#     vectorstore.as_retriever(search_kwargs={"filter": {"domain": "other"}, "k": 3}),
#     name="search_other_kb",
#     description="Searches rules and manuals for the other domain."
# )
