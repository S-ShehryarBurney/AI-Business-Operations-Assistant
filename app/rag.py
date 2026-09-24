from openai import OpenAI
import os
from dotenv import load_dotenv
from app.database import SessionLocal
from app.errors import ToolError
from app.models import CompanyKnowledge

load_dotenv()

client = OpenAI(
    api_key = os.environ.get("OPENROUTER_API_KEY"),
    base_url = "https://openrouter.ai/api/v1"
)

def search_knowledge(query):

    if not isinstance(query, str):
        raise ToolError("Query must be a string.")

    if not query.strip():
        raise ToolError("Query cannot be empty.")

    query = query.strip()

    query_response = client.embeddings.create(
            model = "nvidia/nemotron-3-embed-1b:free",
            input = query,
            encoding_format = 'float'
        )
    query_embedding = query_response.data[0].embedding

    db = SessionLocal()

    result = (
        db.query(CompanyKnowledge)
        .order_by(CompanyKnowledge.embedding.cosine_distance(query_embedding))
        .first()
    )

    if result is None:
        db.close()
        raise ToolError("No company knowledge found.")

    content = result.content

    db.close()

    return content

def list_company_policies():
    db = SessionLocal()

    try:
        results = (db.query(CompanyKnowledge.policy_name)
        .distinct().order_by(CompanyKnowledge.policy_name).all())

        if not results:
            raise ToolError("No company policies found in the knowledge base.")

        return [result[0] for result in results]

    finally:
        db.close()