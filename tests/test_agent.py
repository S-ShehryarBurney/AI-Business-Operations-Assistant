import json
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.main import AssistantRequest, app, assistant, run_agent
from app.errors import AgentLoopError, ToolExecutionError

@pytest.mark.parametrize("message", ["", " "])
def test_assistant_rejects_empty_or_whitespace_message(message):
    response = TestClient(app).post("/assistant", json={"message": message})

    assert response.status_code == 422

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


def test_run_agent_handles_tool_execution_failure(monkeypatch):
    function_call = SimpleNamespace(
        type="function_call",
        name="get_customer",
        arguments=json.dumps({"customer_id": 101}),
        call_id="call_1"
    )

    first_response = SimpleNamespace(output=[function_call], output_text="")
    second_response = SimpleNamespace(output=[], output_text="Customer lookup failed.")
    responses = [first_response, second_response]
    captured_inputs = []

    def fake_create(**kwargs):
        captured_inputs.append(kwargs["input"])
        return responses.pop(0)

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=fake_create)
    )
    monkeypatch.setattr("app.main.client", fake_client)
    monkeypatch.setattr(
        "app.main.get_customer",
        lambda customer_id: (_ for _ in ()).throw(ToolExecutionError("Customer lookup failed. Please try again later."))
    )

    answer = run_agent("Please get customer information.")

    assert answer == "Customer lookup failed."
    second_input = captured_inputs[1]
    function_call_outputs = [
        item for item in second_input if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    assert function_call_outputs
    assert json.loads(function_call_outputs[0]["output"])["error_type"] == "tool_execution_error"


def test_agent_loop_exhaustion_raises_agent_loop_error(monkeypatch):
    function_call = SimpleNamespace(
        type="function_call",
        name="get_customer",
        arguments=json.dumps({"customer_id": 101}),
        call_id="call_1"
    )
    repeat_response = SimpleNamespace(output=[function_call], output_text="")

    def fake_create(**kwargs):
        return repeat_response

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=fake_create)
    )
    monkeypatch.setattr("app.main.client", fake_client)
    monkeypatch.setattr("app.main.get_customer", lambda customer_id: {"customer_id": customer_id, "name": "Example"})

    with pytest.raises(AgentLoopError, match="allowed reasoning limit"):
        run_agent("Please get customer information.")


def test_run_agent_raises_tool_execution_error_for_missing_provider(monkeypatch):
    monkeypatch.setattr("app.main.client", None)

    with pytest.raises(ToolExecutionError, match="OpenRouter API key not configured"):
        run_agent("Please get customer information.")


def test_assistant_returns_answer_contract_for_agent_errors(monkeypatch):
    def fake_run_agent(message):
        raise AgentLoopError("The agent could not complete the task within the allowed reasoning limit.")

    monkeypatch.setattr("app.main.run_agent", fake_run_agent)

    response = assistant(AssistantRequest(message="Please get customer information."))

    assert response == {"answer": "The agent could not complete the task within the allowed reasoning limit."}


def test_assistant_returns_answer_contract_for_success(monkeypatch):
    monkeypatch.setattr("app.main.run_agent", lambda message: "Customer 101 is active.")

    response = assistant(AssistantRequest(message="Please get customer information."))

    assert response == {"answer": "Customer 101 is active."}