from openai import OpenAI
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_session, require_database_config
from app.errors import ToolError, ToolExecutionError
from app.models import CompanyKnowledge

load_dotenv()

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
) if openrouter_api_key else None


def require_client():
    if client is None:
        raise ToolExecutionError(
            "OpenRouter API key not configured. Set OPENROUTER_API_KEY before using knowledge search."
        )


def search_knowledge(query):

    require_client()
    require_database_config()

    if not isinstance(query, str):
        raise ToolError("Query must be a string.")

    if not query.strip():
        raise ToolError("Query cannot be empty.")

    query = query.strip()

    try:
        query_response = client.embeddings.create(
                model = "nvidia/nemotron-3-embed-1b:free",
                input = query,
                encoding_format = 'float'
            )
        query_embedding = query_response.data[0].embedding
    except Exception as exc:
        raise ToolExecutionError(
            "Knowledge search failed. Please try again later."
        ) from exc

    db = get_session()

    try:
        result = (
            db.query(CompanyKnowledge)
            .order_by(CompanyKnowledge.embedding.cosine_distance(query_embedding))
            .first()
        )

        if result is None:
            raise ToolError("No company knowledge found.")

        return result.content
    except SQLAlchemyError as exc:
        raise ToolExecutionError(
            "Knowledge lookup failed. Please try again later."
        ) from exc
    finally:
        db.close()


def list_company_policies():
    require_database_config()
    db = get_session()

    try:
        results = (db.query(CompanyKnowledge.policy_name)
        .distinct().order_by(CompanyKnowledge.policy_name).all())

        if not results:
            raise ToolError("No company policies found in the knowledge base.")

        return [result[0] for result in results]
    except SQLAlchemyError as exc:
        raise ToolExecutionError(
            "Policy lookup failed. Please try again later."
        ) from exc
    finally:
        db.close()