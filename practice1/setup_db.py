"""
Database setup script for CommerceHub
This script creates the MySQL database and tables required for the application.
Run this script once before starting the application.
"""

import mysql.connector
from mysql.connector import Error


def create_database():
    """Create the CommerceHub database and tables"""
    
    # Database configuration
    host = "localhost"
    user = "admin"
    password = "Admin123"
    
    try:
        # Connect to MySQL server without selecting a database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            print("Creating database 'commercehub'...")
            cursor.execute("DROP DATABASE IF EXISTS commercehub")
            cursor.execute("CREATE DATABASE IF NOT EXISTS commercehub")
            print("✓ Database created successfully")
            
            # Select the database
            cursor.execute("USE commercehub")
            
            # Create orders table
            print("Creating 'orders' table...")
            create_orders_table = """
            CREATE TABLE orders (
                order_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(255) NOT NULL,
                total DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_orders_table)
            print("✓ 'orders' table created successfully")
            
            # Create order_items table
            print("Creating 'order_items' table...")
            create_items_table = """
            CREATE TABLE order_items (
                item_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
            )
            """
            cursor.execute(create_items_table)
            print("✓ 'order_items' table created successfully")
            
            connection.commit()
            print("\n✓ Database setup completed successfully!")
            print("\nDatabase Schema:")
            print("- Database: commercehub")
            print("- Tables: orders, order_items")
            print("\nYou can now run the application with:")
            print("  uvicorn app.main:app --reload")
            
            cursor.close()
            
    except Error as e:
        print(f"Error: {e}")
        return False
    
    finally:
        if connection and connection.is_connected():
            connection.close()
    
    return True


if __name__ == "__main__":
    create_database()
