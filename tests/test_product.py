import pytest
from app.main import get_product
from app.errors import ToolError

@pytest.mark.parametrize("product_id, expected_name", [
    (10, "Zero Carbon Earbuds"),
    (12, "Zero Platinum Smartwatch"),
    (14, "Gionee Headphones"),
])
def test_get_valid_product_ids(product_id, expected_name):
    product = get_product(product_id)

    assert product["name"] == expected_name

def test_get_product_invalid_id():
    with pytest.raises(ToolError, match="Product does not exist."):
        get_product(13)

@pytest.mark.parametrize("product_id", [
    "10",
    0,
    -1,
    True
])
def test_get_product_invalid_arguments(product_id):
    with pytest.raises(ToolError):
        get_product(product_id)