from flask import Flask, jsonify, request, Blueprint
from database import get_connection
from mysql.connector import Error

customers_bp = Blueprint("customers", __name__)

#----------------------------- Customers API ------------------------------------------------
# get all customers
@customers_bp.route("/customers", methods=["GET"])
def get_customers():
    """
    Get all customers or filter customers
    ---
    parameters:
      - name: search
        in: query
        type: string
        required: false
        description: Search customers by name
        example: Ahmed

      - name: customer_id
        in: query
        type: integer
        required: false
        description: Filter by customer ID
        example: 3

      - name: price_list_id
        in: query
        type: integer
        required: false
        description: Filter customers by price list ID
        example: 2

    responses:
      200:
        description: A list of customers
        schema:
          type: array
          items:
            type: object
            properties:
              customer_id:
                type: integer
              name:
                type: string
              price_list_id:
                type: integer

      400:
        description: Invalid filter value
    """

    search = request.args.get("search")
    customer_id = request.args.get("customer_id")
    price_list_id = request.args.get("price_list_id")

    # Clean search text
    if search:
        search = search.strip()

    # Validate customer_id
    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({"message": "customer_id must be an integer"}), 400

        if customer_id <= 0:
            return jsonify({
                "message": "customer_id must be a positive integer"
            }), 400

    # Validate price_list_id
    if price_list_id:
        try:
            price_list_id = int(price_list_id)
        except ValueError:
            return jsonify({
                "message": "price_list_id must be an integer"
            }), 400

        if price_list_id <= 0:
            return jsonify({
                "message": "price_list_id must be a positive integer"
            }), 400

    conditions = []
    values = []

    # Name search
    if search:
        conditions.append("name LIKE %s")
        values.append(f"%{search}%")

    # Customer ID filter
    if customer_id is not None:
        conditions.append("customer_id = %s")
        values.append(customer_id)

    # Price list ID filter
    if price_list_id is not None:
        conditions.append("price_list_id = %s")
        values.append(price_list_id)

    # Build query
    query = "SELECT * FROM customers"

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += ";"

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(query, tuple(values))
    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(result)

# get one customer
@customers_bp.route("/customers/<id>", methods=["GET"])
def get_customer(id):
    """
Get a customer by ID
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the customer
responses:
  200:
    description: Customer found
  404:
    description: Customer not found
"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT name, price_list_id FROM customers WHERE customer_id = %s;"
    cursor.execute(query, (id,))
    result = cursor.fetchone()

    # If customer doesn't exist
    if result is None:
      cursor.close()
      connection.close()
      return jsonify({"message": "Customer not found"}), 404

    cursor.close()
    connection.close()

    return jsonify(result)

# add customer
@customers_bp.route("/customers", methods=["POST"])
def add_customer():
    """
Add a new customer
---
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        name:
          type: string
          example: Ahmed
        price_list_id:
          type: integer
          example: 1
responses:
  201:
    description: Customer added successfully
  400:
    description: Invalid customer data
  404:
    description: Price list not found
"""
    data = request.get_json()
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    name = data.get('name')
    price_list_id = data.get('price_list_id')

    if name is None or price_list_id is None :
      return jsonify({"message": "Name and price_list_id are required"}), 400 
    if not isinstance(name, str):
        return jsonify({"message": "Name must be a string"}), 400
    
    name = name.strip()
    if name=="":
      return jsonify({"message": "Name is required"}), 400

    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return jsonify({"message": "price_list_id must be a positive integer"}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # check if price list exists
    price_list_query = "SELECT price_list_id FROM `price list` WHERE price_list_id = %s;"
    cursor.execute(price_list_query, (price_list_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "Price list not found"}), 404

    query = "INSERT INTO customers (name, price_list_id) VALUES (%s, %s);"
    try:
        cursor.execute(query, (name, price_list_id))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()

    return jsonify({'message': 'Customer added successfully!'}), 201

# update customer
@customers_bp.route("/customers/<id>", methods=["PUT"])
def update_customer(id):
    """
Update a customer
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the customer
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        name:
          type: string
          example: Ahmed
        price_list_id:
          type: integer
          example: 1
responses:
  200:
    description: Customer updated successfully
  400:
    description: Invalid customer data
  404:
    description: Customer or price list not found
"""
    data = request.get_json()
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    name = data.get('name')
    price_list_id = data.get('price_list_id')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Get current customer
    query = "SELECT name, price_list_id FROM customers WHERE customer_id = %s;"
    cursor.execute(query, (id,))
    current_customer = cursor.fetchone()

    # If customer doesn't exist
    if current_customer is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "Customer not found"}), 404
    
    # Keep old value if it wasn't provided
    if name is None:
        name = current_customer["name"]
    else:
      if not isinstance(name, str):
        cursor.close()
        connection.close()
        return jsonify({"message": "Name must be a string"}), 400
      name = name.strip()
      if name=="":
        cursor.close()
        connection.close()
        return jsonify({"message": "Name is required"}), 400
      
    if price_list_id is None:
        price_list_id = current_customer["price_list_id"]
    else:
      if not isinstance(price_list_id, int) or price_list_id <= 0:
          cursor.close()
          connection.close()
          return jsonify({"message": "price_list_id must be a positive integer"}), 400
       
      # check if price list exists
      price_list_query = "SELECT price_list_id FROM `price list` WHERE price_list_id = %s;"
      cursor.execute(price_list_query, (price_list_id,))
      result = cursor.fetchone()
      if result is None:
          cursor.close()
          connection.close()
          return jsonify({"message": "Price list not found"}), 404
    
    # Update
    query = """
        UPDATE customers
        SET name = %s, price_list_id = %s
        WHERE customer_id = %s;
    """
    try:
        cursor.execute(query, (name, price_list_id, id))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()

    return jsonify({'message': 'Data updated successfully!'}), 200

# delete customer
@customers_bp.route("/customers/<id>", methods=["DELETE"])
def delete_customer(id):
    """
Delete a customer
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the customer
responses:
  200:
    description: Customer deleted successfully
  404:
    description: Customer not found
  409:
    description: Customer cannot be deleted because it is being used in existing records
"""
    query = "DELETE FROM customers WHERE customer_id = %s;"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, (id,))
        connection.commit()
    except Error as e:
            connection.rollback()
    
            if e.errno == 1451:
                cursor.close()
                connection.close()
                return jsonify({
                    "message": "Customer cannot be deleted because it is being used in existing records."
                }), 409
            cursor.close()
            connection.close()
            return jsonify({
                "message": "Database error"
            }), 500

    # check if there were any rows affected by the SQL query (if 0 rows were deleted)
    if cursor.rowcount == 0:
        cursor.close()
        connection.close()
        return jsonify({"message": "Customer not found"}), 404
    
    cursor.close()
    connection.close()

    return jsonify({"message": "Customer deleted successfully!"}), 200

