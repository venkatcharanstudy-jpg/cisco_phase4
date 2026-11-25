from fastapi import FastAPI, HTTPException
from app.models import OrderRequest, OrderResponse
from app.storage import InMemoryOrderStorage
from app.repository import OrderRepository
from app.calculator import StandardPriceCalculator
from app.service import OrderService

storage = InMemoryOrderStorage()
calculator = StandardPriceCalculator()
repository = OrderRepository(storage)
service = OrderService(repository, calculator)

app = FastAPI(
    title="CommerceHub SOLID API",
    description="Order Management API with SOLID principles",
    version="2.0.0"
)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/orders", status_code=201, response_model=OrderResponse, tags=["Orders"])
def create_order(order_request: OrderRequest):
    """Create a new order"""
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
