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

def search_knowledge(query):

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
        raise ValueError("No company knowledge found.")

    content = result.content

    db.close()

    return content

query = "How long does standard shipping take?"

result = search_knowledge(query)

print("Best Chunk:")
print(result)

prompt = f"""
Answer the user's question using the company policy below.

Company Policy:
{result}

User Question:
{query}
"""

response = client.responses.create(
    model = "nvidia/nemotron-3.5-lightning:free",
    input = prompt
)

print("AI Answer:")
print(response.output_text)