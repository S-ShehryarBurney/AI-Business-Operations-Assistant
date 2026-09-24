from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from fastapi import FastAPI, Depends
from app.database import SessionLocal
from app.models import Customer, Order, Product
from app.rag import search_knowledge, list_company_policies
from pydantic import BaseModel
from app.errors import AgentLoopError, ToolError

load_dotenv()

app = FastAPI()

class AssistantRequest(BaseModel):
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/customers/{customer_id}")
def read_customer(customer_id: int, db = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if not customer:
        return {"error": "Customer does not exist."}

    return{
        "customer_id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "status": customer.status
    }

@app.get("/orders/{order_id}")
def read_order(order_id: int, db = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        return {"error": "Order does not exist."}

    return{
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "product_id": order.product_id,
        "status": order.status
    }

@app.get("/products/{product_id}")
def read_product(product_id: int, db = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()

    if not product:
        return {"error": "Product does not exist."}

    return{
        "product_id": product.product_id,
        "name": product.name,
        "price": product.price,
        "status": product.status
    }

@app.post("/assistant")
def assistant(request: AssistantRequest):
    try:
        answer = run_agent(request.message)
        return {"answer": answer}

    except AgentLoopError as error:
        return {"answer": str(error)}

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

if openrouter_api_key:
    print("OpenRouter API Key Loaded")
else:
    raise ValueError("OpenRouter API Key Not Found")

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

def get_customer(customer_id):

    if isinstance(customer_id, bool) or not isinstance(customer_id, int):
        raise ToolError("Invalid customer ID. ID must be an integer.")

    if customer_id <= 0:
        raise ToolError("Invalid customer ID. ID must be a positive integer.")

    db = SessionLocal()

    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

        if not customer:
            raise ToolError("Customer does not exist.")

        return{
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status
        }
    finally:
        db.close()

def get_order(order_id):

    if isinstance(order_id, bool) or not isinstance(order_id, int):
        raise ToolError("Invalid order ID. ID must be an integer.")

    if order_id <= 0:
        raise ToolError("Invalid order ID. ID must be a positive integer.")

    db = SessionLocal()

    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise ToolError("Order does not exist.")

        return{
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "product_id": order.product_id,
            "status": order.status
        }
    finally:
        db.close()

def get_product(product_id):
    if isinstance(product_id, bool) or not isinstance(product_id, int):
        raise ToolError("Invalid product ID. ID must be an integer.")

    if product_id <= 0:
        raise ToolError("Invalid product ID. ID must be a positive integer.")

    db = SessionLocal()

    try:
        product = db.query(Product).filter(Product.product_id == product_id).first()

        if not product:
            raise ToolError("Product does not exist.")

        return{
            "product_id": product.product_id,
            "name": product.name,
            "price": product.price,
            "status": product.status
        }
    finally:
        db.close()

get_customer_tool = {
    "type": "function",
    "name": "get_customer",
    "description": "Use this tool when a user asks for information about a specific customer. Retrieve the customer's record using the customer's ID.",
    "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "A unique integer ID used to identify a specific customer in the database."
                }
            },
    "required": ["customer_id"]       
    }
}

get_order_tool = {
    "type": "function",
    "name": "get_order",
    "description": "Use this tool when a user asks for information about a specific order. Retrieve the order's record using the order's ID.",
    "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "A unique integer ID used to identify a specific order in the database."
                }
            },
    "required": ["order_id"]       
    }
}

get_product_tool = {
    "type": "function",
    "name": "get_product",
    "description": "Use this tool when a user asks for information about a specific product. Retrieve the product's record using the product's ID.",
    "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "A unique integer ID used to identify a specific product in the database."
                }
            },
    "required": ["product_id"]       
    }
}

get_search_knowledge_tool = {
    "type": "function",
    "name": "search_knowledge",
    "description": "Use this tool when a user asks about company policies, procedures, rules, or other information contained in the company's internal knowledge.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The user's question or request to search for relevant information in the company's internal knowledge."
            }
        },
    "required": ["query"]
    }
}   

list_company_policies_tool = {
    "type": "function",
    "name": "list_company_policies",
    "description": "Use this tool when a user asks for a list of all company policies available in the company's internal knowledge.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

agent_instructions = """
You are an AI business operations assistant.

Your job is to answer the user's request using the available business data and company knowledge tools.

Before answering:
- Understand exactly what information the user is asking for.
- Identify all information needed to answer the request accurately.
- Use the appropriate tools to retrieve that information.
- Follow dependencies between tool results when necessary. For example, an order may identify a product ID that must then be used to retrieve the product.
- Use company knowledge when the request involves company policies, procedures, rules, or internal information.
- Cross-reference business data and company knowledge when the user's question requires both.
- Do not guess or invent information.
- Use tool results as evidence for your answer.
- Continue using tools until you have enough information to answer the user's complete request.
- Once you have sufficient information, stop using tools and provide a concise, clear answer.
- Use list_company_policies when the user asks to list, name, or identify all policies in the internal knowledge base. Use search_knowledge when the user asks about the content or details of a policy.
"""

def run_agent(user_message):
    
    conversation = [
        {
            "role": "user",
            "content": user_message
        }
    ]
    max_rounds = 5

    response = client.responses.create(
        model = "nvidia/nemotron-3.5-lightning:free",
        instructions = agent_instructions,
        input = conversation,
        tools = [get_customer_tool, 
                 get_order_tool, 
                 get_product_tool, 
                 get_search_knowledge_tool, 
                 list_company_policies_tool]
    )

    for round_number in range(max_rounds):
        tool_outputs = []
        tool_called = False

        for item in response.output:

            if item.type == "function_call":
                tool_called = True

                try:
                    try:
                        arguments = json.loads(item.arguments)
                    except (json.JSONDecodeError, TypeError):
                        raise ToolError("Tool arguments must be valid JSON.")    

                    if not isinstance(arguments, dict):
                        raise ToolError("Tool arguments must be a JSON object.")
                
                    if item.name == "get_customer":
                        if "customer_id" not in arguments:
                            raise ToolError("Missing required argument: customer_id.")

                        tool_output = get_customer(arguments["customer_id"])

                    elif item.name == "get_order":
                        if "order_id" not in arguments:
                            raise ToolError("Missing required argument: order_id.")

                        tool_output = get_order(arguments["order_id"])

                    elif item.name == "get_product":
                        if "product_id" not in arguments:
                            raise ToolError("Missing required argument: product_id.")
                        
                        tool_output = get_product(arguments["product_id"])

                    elif item.name == "search_knowledge":
                        if "query" not in arguments:
                            raise ToolError("Missing required argument: query.")

                        tool_output = search_knowledge(arguments["query"])

                    elif item.name == "list_company_policies":
                        tool_output = list_company_policies()

                    else:
                        raise ToolError(f"Unknown tool: {item.name}")

                except ToolError as error:
                    tool_output = {"error": str(error)}

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(tool_output)
                })

        conversation.extend(response.output)
        conversation.extend(tool_outputs)

        if not tool_called:
            return response.output_text

        response = client.responses.create(
                model = "nvidia/nemotron-3.5-lightning:free",
                instructions = agent_instructions,
                input = conversation,
                tools = [get_customer_tool, 
                         get_order_tool, 
                         get_product_tool, 
                         get_search_knowledge_tool, 
                         list_company_policies_tool]
            )

    raise AgentLoopError("The agent could not complete the task within the allowed reasoning limit.")
