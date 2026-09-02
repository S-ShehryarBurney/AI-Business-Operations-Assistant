from dotenv import load_dotenv
import os
from openai import OpenAI
import json

load_dotenv()

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

if openrouter_api_key:
    print("OpenRouter API Key Loaded")
else:
    raise ValueError("OpenRouter API Key Not Found")

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

customers = [
    {"customer_id": 101, "name": "Nida", "email": "nida@example.com", "status": "active"},
    {"customer_id": 102, "name": "Hashmat", "email": "hashmat@example.com", "status": "active"},
    {"customer_id": 103, "name": "Shehryar", "email": "shehryar@example.com", "status": "inactive"}
]

orders = [
    {"order_id": 112, "customer_id": 101, "product_id": 10, "status": "shipped"},
    {"order_id": 113, "customer_id": 102, "product_id": 12, "status": "processing"},
    {"order_id": 114, "customer_id": 103, "product_id": 14, "status": "cancelled"}
]

products = [
    {"product_id": 10, "name": "Zero Carbon Earbuds", "price": 2500, "status": "out of stock"},
    {"product_id": 12, "name": "Zero Platinum Smartwatch", "price": 14699, "status": "in stock"},
    {"product_id": 14, "name": "Gionee Handsfree", "price": 350, "status": "discontinued"}
]

def get_customer(customer_id):
    for customer in customers:
        if customer["customer_id"] == customer_id:
            return customer

    raise ValueError("Customer does not exist.")

def get_order(order_id):
    for order in orders:
        if order["order_id"] == order_id:
            return order

    raise ValueError("Order does not exist.")

def get_product(product_id):
    for product in products:
        if product["product_id"] == product_id:
            return product

    raise ValueError("Product does not exist.")

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

if __name__ == "__main__":
    response = client.responses.create(
        model = "nvidia/nemotron-3.5-lightning:free",
        input = "What is the status of customer 102?",
        tools = [get_customer_tool, get_order_tool, get_product_tool]
    )

    for item in response.output:
        if item.type == "function_call":
            print(item.name)
            print(item.arguments)
            print(item.call_id)
            arguments = json.loads(item.arguments)
            print(arguments)

            if item.name == "get_customer":
                tool_output = get_customer(arguments["customer_id"])

            elif item.name == "get_order":
                tool_output = get_order(arguments["order_id"])

            else:
                tool_output = get_product(arguments["product_id"])

            tool_output = json.dumps(tool_output)

            final_response = client.responses.create(
                model = "nvidia/nemotron-3.5-lightning:free",
                input = [
                *response.output,
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": tool_output
                }
                ]
            )

            print(final_response.output_text)

#print(response.output_text)