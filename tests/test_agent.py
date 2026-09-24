import json
from types import SimpleNamespace
from app.main import run_agent

def test_run_agent_handles_malformed_tool_arguments(monkeypatch):
    function_call = SimpleNamespace(
        type = "function_call",
        name = "get_customer",
        arguments = "{invalid json",
        call_id = "call_1"
    )

    first_response = SimpleNamespace(
        output = [function_call],
        output_text = ""
    )

    second_response = SimpleNamespace(
        output = [],
        output_text = "The tool arguments were invalid."
    )

    responses = [first_response, second_response]

    def fake_create(**kwargs):
        return responses.pop(0)

    fake_client = SimpleNamespace(
        responses = SimpleNamespace(create = fake_create)
    )

    monkeypatch.setattr("app.main.client", fake_client)

    answer = run_agent("Please get customer information.")

    assert answer ==  "The tool arguments were invalid."

def test_run_agent_handles_missing_tool_argument(monkeypatch):
    function_call = SimpleNamespace(
        type = "function_call",
        name = "get_customer",
        arguments = json.dumps({}),  # Missing required argument
        call_id = "call_1"
    )

    first_response = SimpleNamespace(
        output = [function_call],
        output_text = ""
    )

    second_response = SimpleNamespace(
        output = [],
        output_text = "Missing required argument: customer_id."
    )

    responses = [first_response, second_response]

    def fake_create(**kwargs):
        return responses.pop(0)

    fake_client = SimpleNamespace(
        responses = SimpleNamespace(create = fake_create)
    )

    monkeypatch.setattr("app.main.client", fake_client)

    answer = run_agent("Please get customer information.")

    assert answer ==  "Missing required argument: customer_id."