from types import SimpleNamespace

import pytest
from app.rag import list_company_policies, search_knowledge
from app.errors import ToolError


@pytest.fixture(autouse=True)
def mock_openrouter_client(monkeypatch):
    monkeypatch.setattr("app.rag.client", object())


def test_search_knowledge(monkeypatch):
    expected_query = "Can I return a product after a month?"
    expected_embedding = [0.1, 0.2, 0.3]
    captured = {}

    class FakeQuery:
        def order_by(self, distance_expression):
            captured["distance_expression"] = distance_expression
            return self

        def first(self):
            return SimpleNamespace(content="Customers can return unused products within 14 days of delivery.")

    class FakeSession:
        def query(self, *args, **kwargs):
            captured["query_target"] = args[0]
            return FakeQuery()

        def close(self):
            return None

    def fake_create(**kwargs):
        captured["embedding_model"] = kwargs["model"]
        captured["embedding_input"] = kwargs["input"]
        return SimpleNamespace(data=[SimpleNamespace(embedding=expected_embedding)])

    monkeypatch.setattr("app.rag.require_database_config", lambda: None)
    monkeypatch.setattr("app.rag.get_session", lambda: FakeSession())
    monkeypatch.setattr("app.rag.client", SimpleNamespace(embeddings=SimpleNamespace(create=fake_create)))

    result = search_knowledge(expected_query)

    assert result == "Customers can return unused products within 14 days of delivery."
    assert captured["embedding_input"] == expected_query
    assert captured["embedding_model"] == "nvidia/nemotron-3-embed-1b:free"
    assert captured["query_target"] is not None
    assert captured["distance_expression"] is not None


@pytest.mark.parametrize("query", [
    None,
    123,
    True,
    []
])
def test_search_knowledge_invalid_query_type(monkeypatch, query):
    monkeypatch.setattr("app.rag.client", object())

    with pytest.raises(ToolError, match = "Query must be a string."):
        search_knowledge(query)


@pytest.mark.parametrize("query", [
    "",
    "   ",
    "\n\t"
])
def test_search_knowledge_empty_query(monkeypatch, query):
    monkeypatch.setattr("app.rag.client", object())

    with pytest.raises(ToolError, match = "Query cannot be empty."):
        search_knowledge(query)


def test_search_knowledge_no_results(monkeypatch):
    class FakeQuery:
        def order_by(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class FakeSession:
        def query(self, *args, **kwargs):
            return FakeQuery()

        def close(self):
            return None

    monkeypatch.setattr("app.rag.require_database_config", lambda: None)
    monkeypatch.setattr("app.rag.get_session", lambda: FakeSession())
    monkeypatch.setattr("app.rag.client", SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])]))))

    with pytest.raises(ToolError, match="No company knowledge found."):
        search_knowledge("What is the refund policy?")


def test_list_company_policies_returns_expected_policy_names(monkeypatch):
    class FakeQuery:
        def distinct(self):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return [("Returns Policy",), ("Shipping Policy",)]

    class FakeSession:
        def query(self, *args, **kwargs):
            return FakeQuery()

        def close(self):
            return None

    monkeypatch.setattr("app.rag.require_database_config", lambda: None)
    monkeypatch.setattr("app.rag.get_session", lambda: FakeSession())

    result = list_company_policies()

    assert result == ["Returns Policy", "Shipping Policy"]


def test_list_company_policies_no_policies(monkeypatch):
    class FakeQuery:
        def distinct(self):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return []

    class FakeSession:
        def query(self, *args, **kwargs):
            return FakeQuery()

        def close(self):
            return None

    monkeypatch.setattr("app.rag.require_database_config", lambda: None)
    monkeypatch.setattr("app.rag.get_session", lambda: FakeSession())

    with pytest.raises(ToolError, match="No company policies found in the knowledge base."):
        list_company_policies()