from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models import CompanyKnowledge

load_dotenv()

client = OpenAI(
    api_key = os.environ.get("OPENROUTER_API_KEY"),
    base_url = "https://openrouter.ai/api/v1"
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

def create_embeddings(chunks):
    embeddings = []

    for chunk in chunks:
        response = client.embeddings.create(
            model = "nvidia/nemotron-3-embed-1b:free",
            input = chunk,
            encoding_format = 'float'
        )

        embeddings.append(response.data[0].embedding)

    return embeddings

text = load_knowledge()

chunks = chunk_knowledge(text)

embeddings = create_embeddings(chunks)

db = SessionLocal()

db.query(CompanyKnowledge).delete()

for chunk, embedding in zip(chunks, embeddings):
    policy_name = chunk.splitlines()[0].strip()  # Extract the first line as the policy name
    knowledge = CompanyKnowledge(
        policy_name = policy_name,
        content = chunk,
        embedding = embedding
    )

    db.add(knowledge)

db.commit()
db.close()