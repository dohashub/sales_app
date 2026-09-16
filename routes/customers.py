from flask import Flask, jsonify, request, Blueprint
from database import db
from sqlalchemy.exc import IntegrityError
from models.customers import Customer
from models.price_list import PriceList

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

    query = Customer.query

    # Name search
    if search:
        query = query.filter(Customer.name.like(f"%{search}%"))

    # Customer ID filter
    if customer_id is not None:
        query = query.filter(Customer.customer_id == customer_id)

    # Price list ID filter
    if price_list_id is not None:
        query = query.filter(Customer.price_list_id == price_list_id)

    customers = query.all()

    result = [
        {
            "customer_id" : customer.customer_id,
            "name" : customer.name,
            "price_list_id" : customer.price_list_id
        }
        for customer in customers
    ]

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
    customer = Customer.query.get(id)
    if customer is None:
      return jsonify({"message": "Customer not found"}), 404

    result = {
            "customer_id" : customer.customer_id,
            "name" : customer.name,
            "price_list_id" : customer.price_list_id
    }
    

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
    # check if there's a json body
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    
    name = data.get('name')
    price_list_id = data.get('price_list_id')
    # Check required fields
    if name is None or price_list_id is None :
      return jsonify({"message": "Name and price_list_id are required"}), 400

    # Validate name
    if not isinstance(name, str):
        return jsonify({"message": "Name must be a string"}), 400
    
    name = name.strip()
    if name=="":
      return jsonify({"message": "Name is required"}), 400
    
    # Validate price list ID
    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return jsonify({"message": "price_list_id must be a positive integer"}), 400

    # check if price list exists
    price_list_query = PriceList.query.get(price_list_id)

    if price_list_query is None:
        return jsonify({"message": "Price list not found"}), 404

    # Create customer object
    customer = Customer(
        name=name,
        price_list_id=price_list_id
    )

    try:
        db.session.add(customer)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

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
    # Check request body
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    
    name = data.get('name')
    price_list_id = data.get('price_list_id')

    # Get customer
    customer = Customer.query.get(id)

    # If customer doesn't exist
    if customer is None:
        return jsonify({"message": "Customer not found"}), 404
    
    # Keep old value if it wasn't provided
    if name is None:
        name = customer.name
    else:
      # Validate name
      if not isinstance(name, str):
        return jsonify({"message": "Name must be a string"}), 400
      name = name.strip()
      if name=="":
        return jsonify({"message": "Name is required"}), 400
      
    if price_list_id is None:
        price_list_id = customer.price_list_id
    else:
      # Validate price list ID
      if not isinstance(price_list_id, int) or price_list_id <= 0:
          return jsonify({"message": "price_list_id must be a positive integer"}), 400
       
      # check if price list exists
      price_list_query = PriceList.query.get(price_list_id)
      if price_list_query is None:
          return jsonify({"message": "Price list not found"}), 404
    
    # Update
    customer.name=name
    customer.price_list_id=price_list_id
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

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
    # Get customer
    customer = Customer.query.get(id)
    if customer is None:
        return jsonify({"message": "Customer not found"}), 404
    
    try:
        db.session.delete(customer)
        db.session.commit()
    except IntegrityError as e:
          db.session.rollback()
    
          if e.orig.errno == 1451:
              return jsonify({
                  "message": "Customer cannot be deleted because it is being used in existing records."
              }), 409
          
          return jsonify({
              "message": "Database error"
          }), 500

    return jsonify({"message": "Customer deleted successfully!"}), 200

