from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from fastapi import FastAPI, Depends
from app.database import SessionLocal
from app.models import Customer, Order, Product

load_dotenv()

app = FastAPI()

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
    db = SessionLocal()

    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    

        if not customer:
            raise ValueError("Customer does not exist.")

        return{
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status
        }
    finally:
        db.close()

def get_order(order_id):
    db = SessionLocal()

    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise ValueError("Order does not exist.")

        return{
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "product_id": order.product_id,
            "status": order.status
        }
    finally:
        db.close()

def get_product(product_id):
    db = SessionLocal()

    try:
        product = db.query(Product).filter(Product.product_id == product_id).first()

        if not product:
            raise ValueError("Product does not exist.")

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

if __name__ == "__main__":
    response = client.responses.create(
        model = "nvidia/nemotron-3.5-lightning:free",
        input = "What is the price and status of product 10?",
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