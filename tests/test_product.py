import pytest
from app.main import get_product

@pytest.mark.parametrize("product_id, expected_name", [
    (10, "Zero Carbon Earbuds"),
    (12, "Zero Platinum Smartwatch"),
    (14, "Gionee Headphones"),
])
def test_get_valid_product_ids(product_id, expected_name):
    product = get_product(product_id)

    assert product["name"] == expected_name

def test_get_product_invalid_id():
    with pytest.raises(ValueError, match="Product does not exist."):
        get_product(13)