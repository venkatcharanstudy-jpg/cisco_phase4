# CommerceHub Order Management API - Setup & Usage Guide

## 🎯 Overview

CommerceHub is a **layered FastAPI application** that demonstrates enterprise architecture patterns for managing stationery orders with MySQL database storage.

**Key Features:**
- ✅ Layered architecture (Presentation, Business Logic, Data Access, Database)
- ✅ RESTful API with FastAPI
- ✅ MySQL persistent data storage
- ✅ Pydantic validation
- ✅ Automatic Swagger UI documentation
- ✅ Order total calculation
- ✅ Error handling and validation

---

## 📋 Prerequisites

Before you begin, ensure you have:
- **Python 3.8+** installed
- **MySQL Server 8.0+** installed and running
- **Git** (optional, for version control)

### Check Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check MySQL
mysql --version    # Should be 8.0+

# Check MySQL is running
sudo systemctl status mysql
```

---

## 🚀 Quick Start (5 minutes)

### 1. Navigate to Project Directory
```bash
cd /home/venkave7615/Desktop/cisco/practice1
```

### 2. Run the Automated Startup Script
```bash
bash start.sh
```

This script will:
- Create a Python virtual environment
- Install dependencies
- Set up the MySQL database
- Start the FastAPI server

### 3. Access the API
- **Swagger UI:** http://127.0.0.1:8000/docs
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

---

## 📖 Manual Setup (Detailed Steps)

### Step 1: Create Virtual Environment

```bash
cd /home/venkave7615/Desktop/cisco/practice1
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- fastapi==0.104.1 - Web framework
- uvicorn==0.24.0 - ASGI server
- mysql-connector-python==8.2.0 - MySQL driver
- pydantic==2.5.0 - Data validation

### Step 3: Set up MySQL Database

#### Option A: Run Setup Script (Recommended)
```bash
python3 setup_db.py
```

#### Option B: Manual Setup
```bash
# Connect to MySQL
mysql -u root -p

# Then run:
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'Admin123';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EXIT;

# Then create database
python3 setup_db.py
```

### Step 4: Verify Database Setup
```bash
mysql -u admin -pAdmin123 -e "USE commercehub; SHOW TABLES; DESC orders; DESC order_items;"
```

Expected output:
```
Tables_in_commercehub
order_items
orders

(orders table schema)
(order_items table schema)
```

### Step 5: Start the Application

```bash
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
Connected to MySQL database: commercehub
```

---

## 📡 API Usage Examples

### 1. Health Check

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Response:**
```json
{"status": "ok"}
```

### 2. Create Order

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anu",
    "items": [
      {"name": "Notebook", "quantity": 2, "unit_price": 50},
      {"name": "Pen", "quantity": 1, "unit_price": 20}
    ]
  }'
```

**Response (HTTP 201):**
```json
{
  "order_id": 1,
  "customer_name": "Anu",
  "items": [
    {"name": "Notebook", "quantity": 2, "unit_price": 50.0},
    {"name": "Pen", "quantity": 1, "unit_price": 20.0}
  ],
  "total": 120.0
}
```

### 3. List All Orders

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/orders"
```

**Response (HTTP 200):**
```json
[
  {
    "order_id": 1,
    "customer_name": "Anu",
    "items": [
      {"name": "Notebook", "quantity": 2, "unit_price": 50.0},
      {"name": "Pen", "quantity": 1, "unit_price": 20.0}
    ],
    "total": 120.0
  }
]
```

### 4. Test Validation (Invalid Quantity)

**Request (with quantity = 0):**
```bash
curl -X POST "http://127.0.0.1:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test",
    "items": [
      {"name": "Notebook", "quantity": 0, "unit_price": 50}
    ]
  }'
```

**Response (HTTP 422 - Validation Error):**
```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "Input should be greater than 0",
      "input": 0
    }
  ]
}
```

---

## 🌐 Using Swagger UI

Swagger UI provides an interactive way to test the API:

1. **Open Swagger UI:** http://127.0.0.1:8000/docs

2. **Test Health Endpoint:**
   - Click "GET /health"
   - Click "Try it out"
   - Click "Execute"
   - See the response

3. **Create an Order:**
   - Click "POST /orders"
   - Click "Try it out"
   - Paste sample order JSON
   - Click "Execute"

4. **List Orders:**
   - Click "GET /orders"
   - Click "Try it out"
   - Click "Execute"

---

## 🏗️ Architecture Layers

### Layer 1: Presentation (main.py)
- Defines HTTP routes
- Handles requests/responses
- Returns appropriate HTTP status codes
- 📄 File: `app/main.py`

### Layer 2: Business Logic (service.py)
- Implements order creation
- Calculates totals: sum(quantity × unit_price)
- Orchestrates data operations
- 📄 File: `app/service.py`

### Layer 3: Data Access (repository.py)
- Saves orders to database
- Retrieves orders from database
- Manages database operations
- 📄 File: `app/repository.py`

### Layer 4: Database (db.py)
- Manages MySQL connections
- Executes SQL queries
- Handles connection pooling
- 📄 File: `app/db.py`

### Models & Schemas (models.py)
- OrderItem: name, quantity > 0, unit_price >= 0
- OrderRequest: customer_name, items (at least 1)
- OrderResponse: order_id, customer_name, items, total
- 📄 File: `app/models.py`

---

## 📊 Database Schema

### orders Table
```sql
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### order_items Table
```sql
CREATE TABLE order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
```

---

## 🧪 Testing

### Run Automated Tests

```bash
# Make sure the server is running in another terminal
source venv/bin/activate
python3 test_api.py
```

### Expected Test Results

```
✓ PASSED - Health Check
✓ PASSED - Create Order
✓ PASSED - List Orders  
✓ PASSED - Invalid Quantity

Total: 4/4 tests passed 🎉
```

### Manual Testing with curl

```bash
# Test 1: Health
curl http://127.0.0.1:8000/health

# Test 2: Create order
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Anu","items":[{"name":"Notebook","quantity":2,"unit_price":50}]}'

# Test 3: List orders
curl http://127.0.0.1:8000/orders

# Test 4: Invalid quantity (should return 422)
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Test","items":[{"name":"Notebook","quantity":0,"unit_price":50}]}'
```

---

## 🔧 Troubleshooting

### Issue: MySQL Connection Failed

**Solution:**
```bash
# Check MySQL is running
sudo systemctl status mysql

# If not running, start it
sudo systemctl start mysql

# Verify admin user exists
mysql -u admin -pAdmin123 -e "SELECT USER();"
```

### Issue: Module Not Found (pydantic, fastapi, etc.)

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Port 8000 Already in Use

**Solution:**
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001

# Access at: http://127.0.0.1:8001
```

### Issue: Database Not Created

**Solution:**
```bash
# Run setup script again
python3 setup_db.py

# Or manually create database
mysql -u admin -pAdmin123 << EOF
CREATE DATABASE IF NOT EXISTS commercehub;
USE commercehub;
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
EOF
```

### Issue: "externally-managed-environment" Error

**Solution:**
```bash
# Use virtual environment instead of system Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📁 File Structure

```
practice1/
├── app/
│   ├── __init__.py              # Package init
│   ├── main.py                  # FastAPI app & routes
│   ├── models.py                # Pydantic models
│   ├── service.py               # Business logic
│   ├── repository.py            # Data access
│   └── db.py                    # Database utilities
├── setup_db.py                  # Database setup
├── test_api.py                  # API tests
├── start.sh                     # Quick start script
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

---

## 🎓 Learning Outcomes

After completing this project, you will understand:

✅ **Layered Architecture:**
- Separation of concerns
- Presentation layer independence
- Business logic isolation
- Data access abstraction

✅ **FastAPI Framework:**
- Route definitions
- Request/response handling
- Pydantic validation
- Swagger UI documentation

✅ **MySQL Database:**
- Table design
- Foreign key relationships
- Data persistence
- Query execution

✅ **API Development:**
- RESTful principles
- HTTP status codes
- Request validation
- Error handling

---

## 📞 Support

If you encounter issues:

1. **Check the README.md** for detailed documentation
2. **Review troubleshooting section** above
3. **Check server logs** in terminal where uvicorn is running
4. **Verify database setup** with: `mysql -u admin -pAdmin123 commercehub`
5. **Run tests** to identify specific failures: `python3 test_api.py`

---

## 📝 Notes

- Database data is **persistent** (unlike the original in-memory implementation)
- Each order gets a **unique auto-incrementing order_id**
- Order totals are **rounded to 2 decimal places**
- Timestamps are recorded for each order creation
- All validation is handled by Pydantic before reaching the database layer

---

## 🎉 Next Steps

1. ✅ Set up the application using this guide
2. ✅ Test all endpoints using Swagger UI
3. ✅ Run the automated test suite
4. ✅ Explore the code to understand the architecture
5. 🚀 Deploy to production (optional)

Good luck! 🚀
