import pytest
from app.rag import search_knowledge
from app.errors import ToolError

def test_search_knowledge():
    result = search_knowledge("Can I return a product after a month?")

    assert "14 days of delivery" in result

@pytest.mark.parametrize("query", [
    None,
    123,
    True,
    []
])
def test_search_knowledge_invalid_query_type(query):
    with pytest.raises(ToolError, match = "Query must be a string."):
        search_knowledge(query)

@pytest.mark.parametrize("query", [
    "",
    "   ",
    "\n\t"
])
def test_search_knowledge_empty_query(query):
    with pytest.raises(ToolError, match = "Query cannot be empty."):
        search_knowledge(query)