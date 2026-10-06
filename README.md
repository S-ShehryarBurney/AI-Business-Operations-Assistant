# AI Business Operations Assistant

This repository contains a FastAPI-based business operations assistant that answers operational questions using:

- PostgreSQL + SQLAlchemy for structured business records
- pgvector for semantic company knowledge retrieval
- OpenRouter-hosted LLM APIs for agent orchestration
- a bounded multi-step tool-calling loop

## Purpose

The project is designed to answer questions about:

- customers
- orders
- products
- internal company policies and operational knowledge

The assistant uses business data tools and a retrieval-augmented knowledge layer to ground responses in available evidence instead of inventing facts.

## Architecture

### Core application modules

- `app/main.py`: FastAPI API entry point and orchestration logic for the agent
- `app/database.py`: SQLAlchemy engine/session configuration and database startup checks
- `app/models.py`: SQLAlchemy table models for customers, orders, products, and company knowledge
- `app/rag.py`: semantic knowledge search and policy listing
- `app/errors.py`: project-specific exceptions for controlled tool and agent conditions
- `app/ingest_knowledge.py`: script to load and embed knowledge entries for the internal knowledge base
- `app/seed_data.py`: script to seed the database with sample business records

### Data model

The current architecture expects PostgreSQL with pgvector enabled.

Relevant tables include:

- `customers`: customer records
- `orders`: order records
- `products`: product records
- `company_knowledge`: policy content + vector embedding

`CompanyKnowledge.embedding` is modeled as `Vector(2048)` and therefore depends on the PostgreSQL + pgvector stack.

## Environment

Set the following environment variables before using the app:

- `DATABASE_URL`: PostgreSQL connection string for business records and knowledge storage
- `OPENROUTER_API_KEY`: API key used by the LLM and embedding endpoints

Example:

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@host:5432/ai_business_operations"
export OPENROUTER_API_KEY="your-key"
```

## Database setup

The project expects a PostgreSQL database with the pgvector extension available.

Initialize the schema with SQLAlchemy metadata creation or via the project bootstrap flow used in your local environment.

Do not use a SQLite fallback for the configured architecture.

## Knowledge ingestion

To load the company policy knowledge base:

```bash
python -m app.ingest_knowledge
```

This script reads the policy text from `knowledge/company_policies.txt`, chunks the content, requests embeddings from the configured OpenRouter embedding model, and writes the resulting vectorized documents into the PostgreSQL knowledge table.

## API usage

Run the API with:

```bash
uvicorn app.main:app --reload
```

The assistant endpoint is:

- `POST /assistant`

Request body:

```json
{
  "message": "What is the status of order 112?"
}
```

Successful response contract:

```json
{
  "answer": "..."
}
```

The system intentionally avoids exposing raw Python exceptions or database internals through the API.

## Agent behavior

The agent is bounded to a maximum number of reasoning/tool-calling rounds to avoid runaway loops. If that limit is exhausted, it raises an `AgentLoopError` and the API returns a controlled answer string instead of crashing.

Tool execution follows a controlled pattern:

- expected business logic conditions use `ToolError`
- infrastructure or execution failures are translated to `ToolExecutionError`
- tool outputs include sanitized error information instead of leaking internal SQL or stack traces

## Grounding / hallucination guardrails

The assistant is instructed to:

- rely on actual tool outputs as evidence
- avoid guessing when a record is missing
- say when information is unavailable instead of inventing it
- use `list_company_policies()` for policy enumeration requests
- use `search_knowledge()` for policy-content questions
- treat tool errors as evidence that the requested fact was not retrieved successfully

## Testing

Run the full suite with:

```bash
pytest
```

The repository currently includes tests covering:

- customer lookup validation and error handling
- order lookup validation and error handling
- product lookup validation and error handling
- RAG knowledge retrieval and query validation
- agent tool call and loop safety behavior
- API response contract behavior

## Current limitations

- The repository is a portfolio/application example rather than a full enterprise deployment.
- The database and knowledge sources are expected to be configured externally via environment variables.
- The system does not include an n8n workflow implementation in this repository; if such an integration exists conceptually, it is external to the codebase represented here.
- The project intentionally avoids hiding configuration errors behind silent fallbacks; missing PostgreSQL/pgvector configuration is treated as a startup/runtime requirement rather than being replaced with another backend.
