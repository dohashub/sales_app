from flask import jsonify, request, Blueprint
from services.price_list_items_service import get_all_price_list_items, get_price_list_item, add_price_list_item, update_price_list_item, delete_price_list_item

price_list_items_bp = Blueprint("price_list_items", __name__)

# Price List Items API

# get all price list items
@price_list_items_bp.route("/price-list-items", methods=["GET"])
def get_price_list_items():
  """
Get all price list items
---
responses:
  200:
    description: A list of all price list items
    schema:
      type: array
      items:
        type: object
        properties:
          id:
            type: integer
          price_list_id:
            type: integer
          product_id:
            type: integer
          price:
            type: integer
"""
  result, status_code = get_all_price_list_items()

  return jsonify(result), status_code

# get one price list item
@price_list_items_bp.route("/price-list-items/<id>", methods=["GET"])
def get_price_list_item_route(id):
  """
Get a price list item by ID
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list item
responses:
  200:
    description: Price list item found
  404:
    description: Price list item not found
"""
  result, status_code = get_price_list_item(id)
  
  return jsonify(result), status_code


# add price list item
@price_list_items_bp.route("/price-list-items", methods=["POST"])
def add_price_list_item_route():
  """
Add a new price list item
---
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        product_id:
          type: integer
          example: 1
        price_list_id:
          type: integer
          example: 1
        price:
          type: integer
          example: 50
responses:
  201:
    description: Price list item added successfully
  400:
    description: Invalid price list item data
  404:
    description: Product or price list not found
  409:
    description: Product already exists in the price list
"""
  data = request.get_json()
  # Check request body
  if data is None:
      return jsonify({"message": "Request body is required"}), 400
  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  product_id = data.get('product_id')
  price_list_id = data.get('price_list_id')
  price = data.get('price')

  result, status_code = add_price_list_item(product_id, price_list_id, price)

  return jsonify(result), status_code


# update price list items
@price_list_items_bp.route("/price-list-items/<id>", methods=["PUT"])
def update_price_list_items_route(id):
  """
Update a price list item
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list item
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        price:
          type: integer
          example: 60
responses:
  200:
    description: Price list item updated successfully
  400:
    description: Invalid price
  404:
    description: Price list item not found
"""
  data = request.get_json()
  # Check request body
  if data is None:
      return jsonify({"message": "Request body is required"}), 400

  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  price = data.get('price')

  result, status_code = update_price_list_item(id, price)

  return jsonify(result), status_code


# delete price list item
@price_list_items_bp.route("/price-list-items/<id>", methods=["DELETE"])
def delete_price_list_item_route(id):
  """
Delete a price list item
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list item
responses:
  200:
    description: Price list item deleted successfully
  404:
    description: Price list item not found
  409:
    description: Price list item cannot be deleted because it is being used in existing records
"""
  result, status_code = delete_price_list_item(id)

  return jsonify(result), status_code