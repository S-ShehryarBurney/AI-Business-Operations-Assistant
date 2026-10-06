from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.database import SessionLocal, require_database_config
from app.models import CompanyKnowledge

load_dotenv()


def get_client():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured for knowledge ingestion.")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )


def load_knowledge():
    knowledge_file = Path("knowledge/company_policies.txt")
    return knowledge_file.read_text(encoding="utf-8")


def chunk_knowledge(text):
    sections = text.split("\n\nCOMPANY")

    chunks = []

    for section in sections:
        if section.startswith("COMPANY"):
            chunks.append(section)
        else:
            chunks.append("COMPANY" + section)

    return chunks


def create_embeddings(chunks, client=None):
    client = client or get_client()
    embeddings = []

    for chunk in chunks:
        response = client.embeddings.create(
            model = "nvidia/nemotron-3-embed-1b:free",
            input = chunk,
            encoding_format = 'float'
        )

        embeddings.append(response.data[0].embedding)

    return embeddings


def ingest_knowledge():
    require_database_config()
    client = get_client()
    text = load_knowledge()
    chunks = chunk_knowledge(text)
    embeddings = create_embeddings(chunks, client=client)

    db = SessionLocal()

    try:
        db.query(CompanyKnowledge).delete()

        for chunk, embedding in zip(chunks, embeddings):
            policy_name = chunk.splitlines()[0].strip()
            knowledge = CompanyKnowledge(
                policy_name=policy_name,
                content=chunk,
                embedding=embedding
            )
            db.add(knowledge)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    ingest_knowledge()