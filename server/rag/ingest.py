import os
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from openai import OpenAI

DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"
CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "aura_wealth_docs"


def get_chroma_collection(client=None):
    if client is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(COLLECTION_NAME)


def ingest_documents(openai_client=None, chroma_client=None):
    if openai_client is None:
        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    collection = get_chroma_collection(chroma_client)
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)

    total_chunks = 0
    for pdf_path in sorted(DOCS_DIR.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        chunks = splitter.split_text(text)
        if not chunks:
            continue

        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=chunks,
        )
        embeddings = [e.embedding for e in response.data]
        ids = [f"{pdf_path.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": pdf_path.name, "chunk": i} for i in range(len(chunks))]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)

    return total_chunks
