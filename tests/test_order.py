import pytest
from app.main import get_order

@pytest.mark.parametrize("order_id, expected_status", [
    (112, "shipped"),
    (113, "processing"),
    (114, "cancelled"),
])
def test_get_order_valid_ids(order_id, expected_status):
    order = get_order(order_id)

    assert order["status"] == expected_status

def test_get_order_invalid_id():
    with pytest.raises(ValueError, match="Order does not exist."):
        get_order(115)