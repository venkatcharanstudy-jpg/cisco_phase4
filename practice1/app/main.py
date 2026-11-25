from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.models import OrderRequest, OrderResponse
from app.db import Database
from app.repository import OrderRepository
from app.service import OrderService

# Database configuration
db = Database(
    host="localhost",
    user="admin",
    password="Admin123",
    database="commercehub"
)

# Initialize database connection
try:
    db.connect()
except Exception as e:
    print(f"Failed to connect to database: {e}")

# Create service and repository instances
repository = OrderRepository(db)
service = OrderService(repository)

# Initialize FastAPI app
app = FastAPI(
    title="CommerceHub Order Management API",
    description="A layered API for managing stationery orders",
    version="1.0.0"
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/orders", status_code=201, response_model=OrderResponse, tags=["Orders"])
def create_order(order_request: OrderRequest):
    """Create a new order and calculate the total"""
    try:
        order_response = service.create_order(order_request)
        return order_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders", status_code=200, response_model=list[OrderResponse], tags=["Orders"])
def list_orders():
    """Retrieve all orders"""
    try:
        orders = service.list_orders()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
def shutdown_event():
    """Close database connection on shutdown"""
    db.disconnect()
