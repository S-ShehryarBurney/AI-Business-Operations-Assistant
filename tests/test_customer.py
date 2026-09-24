import pytest
from app.main import get_customer
from app.errors import ToolError

@pytest.mark.parametrize("customer_id, expected_name", [
    (101, "Nida"),
    (102, "Hashmat"),
    (103, "Shehryar"),
])
def test_get_customer_valid_ids(customer_id, expected_name):
    customer = get_customer(customer_id)

    assert customer["name"] == expected_name

def test_get_customer_invalid_id():
    with pytest.raises(ToolError, match="Customer does not exist."):
        get_customer(116)

@pytest.mark.parametrize("customer_id",[
    "101",  # string instead of int
    0,
    -1,  # negative integer
    True  # boolean value
])
def test_get_customer_invalid_arguments(customer_id):
    with pytest.raises(ToolError):
        get_customer(customer_id)