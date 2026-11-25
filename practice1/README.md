# CommerceHub Order Management API

A layered FastAPI application for managing stationery orders with MySQL database storage.

## Project Structure

```
practice1/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # Pydantic models for validation
│   ├── service.py           # Business logic (OrderService)
│   ├── repository.py        # Data access layer (OrderRepository)
│   └── db.py                # Database connection utilities
├── setup_db.py              # Database initialization script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Architecture Layers

### 1. **Presentation Layer** (`main.py`)
- Defines FastAPI routes
- Handles HTTP requests/responses
- Manages dependency injection

### 2. **Business Logic Layer** (`service.py`)
- OrderService: Implements business rules
- Calculates order totals
- Orchestrates data operations

### 3. **Data Access Layer** (`repository.py`)
- OrderRepository: Manages database operations
- Handles order persistence
- Retrieves orders from database

### 4. **Database Layer** (`db.py`)
- Database connection management
- Query execution utilities
- Connection pooling

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server 5.7+
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set up MySQL Database

```bash
python setup_db.py
```

This script will:
- Create the `commercehub` database
- Create the `orders` table (order_id, customer_name, total, created_at)
- Create the `order_items` table (item_id, order_id, name, quantity, unit_price)
- Set up foreign key relationships

**Default MySQL Credentials:**
- User: `admin`
- Password: `Admin123`
- Host: `localhost`

### Step 3: Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

## API Endpoints

### 1. Health Check
```
GET /health
```
**Response:** `{"status": "ok"}`

### 2. Create Order
```
POST /orders
Content-Type: application/json

{
  "customer_name": "Anu",
  "items": [
    {"name": "Notebook", "quantity": 2, "unit_price": 50},
    {"name": "Pen", "quantity": 1, "unit_price": 20}
  ]
}
```

**Response (201 Created):**
```json
{
  "order_id": 1,
  "customer_name": "Anu",
  "items": [
    {"name": "Notebook", "quantity": 2, "unit_price": 50},
    {"name": "Pen", "quantity": 1, "unit_price": 20}
  ],
  "total": 120.0
}
```

### 3. List All Orders
```
GET /orders
```

**Response (200 OK):**
```json
[
  {
    "order_id": 1,
    "customer_name": "Anu",
    "items": [
      {"name": "Notebook", "quantity": 2, "unit_price": 50},
      {"name": "Pen", "quantity": 1, "unit_price": 20}
    ],
    "total": 120.0
  }
]
```

## Validation Rules

### OrderItem
- **quantity**: Must be greater than 0
- **unit_price**: Must be >= 0

### OrderRequest
- **customer_name**: Required string
- **items**: At least one item required

### Order Total Calculation
```
Total = Sum(quantity × unit_price) for all items
```

## Error Handling

### Invalid Quantity (0 or negative)
```
POST /orders with quantity: 0
Response (422 Unprocessable Entity)
```

### Empty Items List
```
POST /orders with items: []
Response (422 Unprocessable Entity)
```

### Database Connection Error
```
Response (500 Internal Server Error)
```

## Testing with Swagger UI

1. Open `http://127.0.0.1:8000/docs`
2. Click on an endpoint (e.g., POST /orders)
3. Click "Try it out"
4. Enter the request data
5. Click "Execute"

## Workflow Example

1. **Create an order:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/orders" \
     -H "Content-Type: application/json" \
     -d '{"customer_name":"Anu","items":[{"name":"Notebook","quantity":2,"unit_price":50},{"name":"Pen","quantity":1,"unit_price":20}]}'
   ```

2. **Retrieve all orders:**
   ```bash
   curl -X GET "http://127.0.0.1:8000/orders"
   ```

3. **Check health:**
   ```bash
   curl -X GET "http://127.0.0.1:8000/health"
   ```

## Database Schema

### orders table
| Column | Type | Notes |
|--------|------|-------|
| order_id | INT | Auto-increment primary key |
| customer_name | VARCHAR(255) | Customer name |
| total | DECIMAL(10, 2) | Order total amount |
| created_at | TIMESTAMP | Creation timestamp |

### order_items table
| Column | Type | Notes |
|--------|------|-------|
| item_id | INT | Auto-increment primary key |
| order_id | INT | Foreign key to orders |
| name | VARCHAR(255) | Item name |
| quantity | INT | Item quantity |
| unit_price | DECIMAL(10, 2) | Price per unit |

## Troubleshooting

### MySQL Connection Error
- Ensure MySQL server is running
- Verify credentials in `setup_db.py` and `app/main.py`
- Check if host is `localhost` and port is `3306`

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### Port 8000 Already in Use
```bash
uvicorn app.main:app --reload --port 8001
```

## Future Enhancements
- Authentication and authorization
- Order status tracking (pending, completed, cancelled)
- Update and delete order operations
- Order search and filtering
- Pagination for order lists
- API rate limiting
- Request/response logging

## Author
Developed as a hands-on demonstration of layered architecture patterns.
