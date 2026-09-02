from app.database import SessionLocal
from app.models import Customer, Product, Order

customers = [
    Customer(
        customer_id = 101,
        name = "Nida",
        email = "nida@example.com",
        status = "active"
    ),
    Customer(
        customer_id = 102,
        name = "Hashmat",
        email = "hashmat@example.com",
        status = "active"
    ),
    Customer(
        customer_id = 103,
        name = "Shehryar",
        email = "shehryar@example.com",
        status = "inactive"
    ),
]

products = [
    Product(
        product_id = 10,
        name = "Zero Carbon Earbuds",
        price = 2500,
        status = "out of stock"
    ),
    Product(
        product_id = 12,
        name = "Zero Platinum Smartwatch",
        price = 14699,
        status = "in stock"
    ),
    Product(
        product_id = 14,
        name = "Gionee Headphones",
        price = 350,
        status = "discontinued"
    ),
]

orders = [
    Order(
        order_id = 112,
        customer_id = 101,
        product_id = 10,
        status = "shipped"
    ),
    Order(
        order_id = 113,
        customer_id = 102,
        product_id = 12,
        status = "processing"
    ),
    Order(
        order_id = 114,
        customer_id = 103,
        product_id = 14,
        status = "cancelled"
    ),
]

db = SessionLocal()

db.add_all(customers)
db.commit()

db.add_all(products)
db.commit()

db.add_all(orders)
db.commit()

db.close()

print("Database seeded successfully.")