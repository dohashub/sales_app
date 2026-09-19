from flask import Flask, jsonify, request, Blueprint
from services.customers_service import get_all_customers, get_customer, add_customer, update_customer, delete_customer

customers_bp = Blueprint("customers", __name__)

#-- Customers API 
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

    - name: page
      in: query
      type: integer
      required: false
      default: 1
      description: Page number

    - name: limit
      in: query
      type: integer
      required: false
      default: 10
      description: Number of customers per page

  responses:
    200:
      description: A list of customers
      schema:
        type: object
        properties:
          data:
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
          page:
            type: integer
            example: 1
          limit:
            type: integer
            example: 10
          total:
            type: integer
            example: 25

    400:
      description: Invalid filter value
  """

  search = request.args.get("search")
  customer_id = request.args.get("customer_id")
  price_list_id = request.args.get("price_list_id")
  page = request.args.get("page", 1)
  limit = request.args.get("limit", 10)

  result, status_code = get_all_customers(
    search, customer_id, price_list_id, page, limit
  )

  return jsonify(result), status_code

    

# get one customer
@customers_bp.route("/customers/<id>", methods=["GET"])
def get_customer_route(id):
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
  result, status_code = get_customer(id)

  return jsonify(result), status_code

# add customer
@customers_bp.route("/customers", methods=["POST"])
def add_customer_route():
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

  result, status_code = add_customer(name, price_list_id)

  return jsonify(result), status_code


# update customer
@customers_bp.route("/customers/<id>", methods=["PUT"])
def update_customer_route(id):
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

  result, status_code = update_customer(id, name, price_list_id)

  return jsonify(result), status_code

# delete customer
@customers_bp.route("/customers/<id>", methods=["DELETE"])
def delete_customer_route(id):
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
  result, status_code = delete_customer(id)

  return jsonify(result), status_code

