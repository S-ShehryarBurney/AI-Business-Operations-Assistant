from app.rag import search_knowledge

def test_search_knowledge():
    result = search_knowledge("Can I return a product after a month?")

    assert "14 days of delivery" in result