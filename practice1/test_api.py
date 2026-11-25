"""
Test script for CommerceHub Order Management API
Tests the API endpoints and database operations
"""

import json
import requests
import time
import subprocess
import sys
import os


class APITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.test_results = []
    
    def test_health(self):
        """Test the health check endpoint"""
        print("\n" + "="*60)
        print("TEST 1: Health Check (GET /health)")
        print("="*60)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200 and response.json()["status"] == "ok":
                print("✓ PASSED")
                self.test_results.append(("Health Check", True))
                return True
            else:
                print("✗ FAILED")
                self.test_results.append(("Health Check", False))
                return False
        except Exception as e:
            print(f"✗ FAILED: {e}")
            self.test_results.append(("Health Check", False))
            return False
    
    def test_create_order(self):
        """Test creating an order"""
        print("\n" + "="*60)
        print("TEST 2: Create Order (POST /orders)")
        print("="*60)
        
        order_data = {
            "customer_name": "Anu",
            "items": [
                {"name": "Notebook", "quantity": 2, "unit_price": 50},
                {"name": "Pen", "quantity": 1, "unit_price": 20}
            ]
        }
        
        print(f"Request Payload:")
        print(json.dumps(order_data, indent=2))
        
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                json=order_data,
                timeout=5
            )
            print(f"\nStatus Code: {response.status_code}")
            response_json = response.json()
            print(f"Response:")
            print(json.dumps(response_json, indent=2))
            
            # Verify response
            if (response.status_code == 201 and 
                response_json.get("total") == 120.0 and
                response_json.get("customer_name") == "Anu"):
                print("✓ PASSED - Order created with correct total (120.0)")
                self.test_results.append(("Create Order", True))
                return True
            else:
                print("✗ FAILED - Unexpected response")
                self.test_results.append(("Create Order", False))
                return False
        except Exception as e:
            print(f"✗ FAILED: {e}")
            self.test_results.append(("Create Order", False))
            return False
    
    def test_list_orders(self):
        """Test listing all orders"""
        print("\n" + "="*60)
        print("TEST 3: List All Orders (GET /orders)")
        print("="*60)
        
        try:
            response = requests.get(f"{self.base_url}/orders", timeout=5)
            print(f"Status Code: {response.status_code}")
            response_json = response.json()
            print(f"Response (first 2 orders):")
            print(json.dumps(response_json[:2] if len(response_json) > 2 else response_json, indent=2))
            
            if response.status_code == 200 and len(response_json) >= 1:
                print(f"✓ PASSED - Retrieved {len(response_json)} order(s)")
                self.test_results.append(("List Orders", True))
                return True
            else:
                print("✗ FAILED - Expected status 200 and at least 1 order")
                self.test_results.append(("List Orders", False))
                return False
        except Exception as e:
            print(f"✗ FAILED: {e}")
            self.test_results.append(("List Orders", False))
            return False
    
    def test_invalid_quantity(self):
        """Test that quantity 0 is rejected"""
        print("\n" + "="*60)
        print("TEST 4: Invalid Quantity Validation (Quantity = 0)")
        print("="*60)
        
        invalid_order = {
            "customer_name": "Test User",
            "items": [
                {"name": "Notebook", "quantity": 0, "unit_price": 50}
            ]
        }
        
        print(f"Request Payload (with invalid quantity):")
        print(json.dumps(invalid_order, indent=2))
        
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                json=invalid_order,
                timeout=5
            )
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 422:
                print("✓ PASSED - Invalid quantity rejected with 422")
                self.test_results.append(("Invalid Quantity", True))
                return True
            else:
                print(f"✗ FAILED - Expected status 422, got {response.status_code}")
                self.test_results.append(("Invalid Quantity", False))
                return False
        except Exception as e:
            print(f"✗ FAILED: {e}")
            self.test_results.append(("Invalid Quantity", False))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name:.<40} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return False


def main():
    """Run the test suite"""
    print("="*60)
    print("CommerceHub API Test Suite")
    print("="*60)
    print("Note: Make sure the FastAPI server is running on port 8000")
    print("Command: uvicorn app.main:app --reload")
    
    tester = APITester()
    
    # Give the server a moment to be ready
    time.sleep(2)
    
    # Run tests
    tester.test_health()
    tester.test_create_order()
    tester.test_list_orders()
    tester.test_invalid_quantity()
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
