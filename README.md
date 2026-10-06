# AI Business Operations Assistant

A grounded AI business operations assistant for customer, order, product, and policy questions. The project combines a Streamlit frontend, a FastAPI backend, a tool-calling OpenRouter-backed agent, and a PostgreSQL + pgvector data layer to provide operational answers grounded in retrieved evidence.

The system is designed to answer questions such as:

- customer status and profile details
- order status and related product context
- product availability and business record details
- company policy questions using the internal knowledge base

## What is in this repository

This repository contains the implementation and local validation artifacts for the project:

- `app/` — FastAPI app, agent orchestration, database models, RAG helpers, and setup scripts
- `frontend/streamlit_app.py` — dark-themed Streamlit operations dashboard
- `knowledge/company_policies.txt` — internal company policy content used for retrieval
- `tests/` — automated validation for customer, order, product, policy, and agent behavior
- `requirements.txt` — Python dependencies for the project

## Current architecture

```text
Browser
  ↓
Streamlit frontend
  ↓ HTTP POST /assistant
FastAPI backend
  ↓
run_agent()
  ↓
OpenRouter-hosted model
  ↓
5 business tools
├── get_customer
├── get_order
├── get_product
├── search_knowledge
└── list_company_policies
  ↓
PostgreSQL + SQLAlchemy
  and/or
pgvector knowledge retrieval
  ↓
agent reasoning loop
  ↓
grounded final answer
  ↓
Streamlit UI
```

The local application flow above reflects the repository as it currently exists. The agent is bounded to a maximum of 5 reasoning/tool-calling rounds before it stops with an `AgentLoopError` instead of continuing indefinitely.

The LLM handles natural-language interpretation, reasoning, and tool selection. Deterministic Python and database logic remain authoritative for the business facts returned to the user.

## FastAPI backend

The backend is implemented in `app/main.py` and exposes the assistant API.

Responsibilities include:

- validating incoming requests
- rejecting blank or whitespace-only messages with HTTP 422
- routing the user message through the tool-calling agent
- invoking database-backed business tools for customers, orders, products, and policy lookups
- returning a consistent `{ "answer": "..." }` JSON contract

The request model accepts:

```json
{
  "message": "What is the status of order 112?"
}
```

The successful response format is:

```json
{
  "answer": "..."
}
```

## Streamlit frontend

The frontend is implemented in `frontend/streamlit_app.py`.

It includes:

- a dark professional operations dashboard theme
- a chat-style conversation UI
- suggested prompts for common operational requests
- session-state conversation history
- a New Conversation control
- loading/progress feedback while the backend is processing
- graceful handling if the backend is unavailable or returns an invalid response
- non-200 HTTP handling from the FastAPI service

This Streamlit app communicates with the FastAPI backend over HTTP only. It does not connect directly to PostgreSQL or OpenRouter.

## Business data model

The SQLAlchemy models in `app/models.py` define the core relational records used by the assistant:

- `Customer`
- `Order`
- `Product`
- `CompanyKnowledge`

The project uses PostgreSQL + SQLAlchemy for the structured business tables and stores document knowledge with pgvector. The `CompanyKnowledge.embedding` field is defined as `Vector(2048)`, matching the current implementation.

There is no formal migration framework in the repository at the current project level; the schema is created through the project’s local bootstrap scripts and in-project setup flow.

## Agent tools

The agent exposes 5 purpose-built tools:

| Tool | Purpose | Data source | Input |
| --- | --- | --- | --- |
| `get_customer` | Retrieve a specific customer record | PostgreSQL `customers` table | `customer_id` |
| `get_order` | Retrieve a specific order record | PostgreSQL `orders` table | `order_id` |
| `get_product` | Retrieve a specific product record | PostgreSQL `products` table | `product_id` |
| `search_knowledge` | Search internal policy knowledge semantically | pgvector-backed knowledge table | `query` |
| `list_company_policies` | List the available company policy names | `company_knowledge` table | none |

Each tool is validated before execution, including malformed JSON handling, missing required arguments, and controlled error propagation.

## RAG and policy retrieval

The repository includes a knowledge base in `knowledge/company_policies.txt`.

The ingestion flow in `app/ingest_knowledge.py`:

- reads the knowledge file
- chunks the text into policy sections
- requests OpenRouter embeddings for each chunk
- stores the results in PostgreSQL using pgvector

The retrieval layer in `app/rag.py` implements:

- `search_knowledge(query)` — semantic retrieval using an OpenRouter embedding and cosine-distance ordering
- `list_company_policies()` — deterministic enumeration of the available policy names

These are intentionally separate behaviors:

- Semantic search answers questions about the content of a policy, such as "What is the return policy?"
- Deterministic enumeration answers questions about the set of policy names, such as "What policies are available?"

The project does not claim a mathematical hallucination-proof guarantee. Grounding is enforced through retrieved tool evidence and explicit agent instructions rather than by an arbitrary hardcoded relevance threshold in the current implementation.

## n8n integration note

An external n8n workflow was used during development and manually tested end-to-end as an automation layer around the FastAPI assistant.

The workflow conceptually operated as:

```text
n8n Webhook
  ↓
HTTP Request
  ↓
FastAPI /assistant
  ↓
AI agent / tool orchestration
  ↓
final response
  ↓
n8n
```

That n8n workflow was created and tested in the n8n browser interface, but the workflow configuration is not stored as a tracked file in this repository. The repository contains the application code; the n8n automation remains an external integration layer that was used during development.

## Safety and reliability work

The project includes explicit safety and reliability patterns in the agent and tool layers.

This corresponds to the Phase 6 safety work:

- 6.1 Controlled Tool Errors
- 6.2 Input / Argument Validation
- 6.3 Tool Failure Handling
- 6.4 Agent Loop Safety
- 6.5 Grounding / Hallucination Guardrails
- 6.6 Consistent API Response Contract
- 6.7 Reliability Test Suite

### Error classes

The project defines these classes in `app/errors.py`:

- `ToolError` — validation issues such as invalid arguments or missing records
- `ToolExecutionError` — infrastructure or execution-level errors such as failed database access or missing provider configuration
- `AgentLoopError` — the agent exceeded the allowed reasoning/tool loop limit

### Guardrails and reliability rules

The implementation includes:

- tool argument validation
- malformed JSON protection
- required-argument enforcement
- preserved `call_id` values for `function_call_output`
- controlled tool errors
- tool execution error handling
- bounded agent loop exhaustion handling
- grounding and evidence-based response behavior
- consistent API output contract

The agent loop is capped at 5 rounds to avoid runaway reasoning while still supporting multi-step business questions.

## Environment and local setup

The application expects the following environment variables to be configured locally:

- `DATABASE_URL` — PostgreSQL connection string for business records and knowledge storage
- `OPENROUTER_API_KEY` — API key used for the configured OpenRouter model and embedding endpoints
- `ASSISTANT_API_URL` — optional frontend override; defaults to `http://127.0.0.1:8000/assistant`

Example:

```powershell
$env:DATABASE_URL="postgresql://user:password@localhost:5432/ai_business_operations"
$env:OPENROUTER_API_KEY="your-api-key"
```

### Run the backend

```bash
uvicorn app.main:app --reload
```

### Run the frontend

```bash
streamlit run frontend/streamlit_app.py
```

## Project initialization helpers

The repository includes helper scripts for setup and local bootstrapping:

- `app.init_db` — create the SQLAlchemy tables
- `app.seed_data` — seed sample customer, product, and order records
- `app.ingest_knowledge` — load `knowledge/company_policies.txt` and store policy embeddings in pgvector

The database contents are sample operational data and policy knowledge used for local development and testing, not a production-scale enterprise dataset.

## Testing

The repository contains a test suite organized in these files:

- `tests/test_customer.py`
- `tests/test_order.py`
- `tests/test_product.py`
- `tests/test_rag.py`
- `tests/test_agent.py`

The tests cover:

- customer record validation and invalid ID handling
- order record validation and invalid ID handling
- product record validation and invalid ID handling
- RAG query validation and knowledge retrieval behavior
- tool argument validation, error conversion, and loop-safety checks
- FastAPI response contract behavior

### Final verified automated result

The test suite was verified with the project virtual environment using:

```bash
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

- 44 tests collected
- 44 tests passed
- 0 tests failed

The RAG tests are mocked to avoid live OpenRouter requests while still validating the actual local vector search behavior and content retrieval path. The repository therefore has a stable automated test suite that does not depend on a live external embedding request.

## Manual validation performed during development

The project was manually validated in a running local environment during development, including:

- FastAPI backend requests and responses
- the Streamlit frontend submitting prompts and rendering answers
- customer, order, and product lookup flows through the agent tools
- knowledge search and policy enumeration behavior against the local knowledge base
- n8n automation developed and manually tested in the browser as an external integration layer around the FastAPI assistant

The n8n workflow itself is not stored as a tracked repository file, but the end-to-end live validation was part of the project’s development process.

## Summary

This project is a functional prototype of a grounded business assistant that connects a human-friendly Streamlit interface to a FastAPI backend, a tool-calling AI agent, a PostgreSQL data layer, and a pgvector knowledge base. It demonstrates how a business assistant can answer operational questions using structured records and internal policy knowledge while keeping the final answer tied to retrieved evidence and explicit safety controls.
