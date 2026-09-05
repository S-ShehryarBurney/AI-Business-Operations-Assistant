from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database import Base
from pgvector.sqlalchemy import Vector

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False)

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, nullable=False)

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    status = Column(String, nullable=False)

class CompanyKnowledge(Base):
    __tablename__ = "company_knowledge"

    id = Column(Integer, primary_key = True)
    content = Column(Text, nullable = False)
    embedding = Column(Vector(2048), nullable = False)