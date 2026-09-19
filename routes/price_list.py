from flask import jsonify, request, Blueprint
from services.price_lists_service import get_all_price_lists, get_price_list, add_price_list, update_price_list, delete_price_list

price_list_bp = Blueprint("price_list", __name__)

# --- Price List API

#get all price lists
@price_list_bp.route("/price-list", methods=["GET"])
def get_price_lists():
  """
Get all price lists
---
responses:
  200:
    description: A list of all price lists
    schema:
      type: array
      items:
        type: object
        properties:
          price_list_id:
            type: integer
          price_list_type:
            type: string
"""
  result, status_code = get_all_price_lists()

  return jsonify(result), status_code


# get one price list
@price_list_bp.route("/price-list/<id>", methods=["GET"])
def get_price_list_route(id):
  """
Get a price list by ID
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list
responses:
  200:
    description: Price list found
  404:
    description: Price list not found
"""
  result, status_code = get_price_list(id)

  return jsonify(result), status_code


# add price list
@price_list_bp.route("/price-list", methods=["POST"])
def add_price_list_route():
  """
Add a new price list
---
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        price_list_type:
          type: string
          example: Retail
responses:
  201:
    description: Price list added successfully
  400:
    description: Invalid price list data
"""
  data = request.get_json()
  # Check request body
  if data is None:
          return jsonify({"message": "Request body is required"}), 400
  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  price_list_type = data.get('price_list_type')

  result, status_code = add_price_list(price_list_type)

  return jsonify(result), status_code


# update price list
@price_list_bp.route("/price-list/<id>", methods=["PUT"])
def update_price_list_route(id):
  """
Update a price list
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        price_list_type:
          type: string
          example: Wholesale
responses:
  200:
    description: Price list updated successfully
  400:
    description: Invalid price list data
  404:
    description: Price list not found
"""
  data = request.get_json()
  # Check request body
  if data is None:
      return jsonify({"message": "Request body is required"}), 400
  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  price_list_type = data.get('price_list_type')

  result, status_code = update_price_list(id, price_list_type)

  return jsonify(result), status_code


# delete price list
@price_list_bp.route("/price-list/<id>", methods=["DELETE"])
def delete_price_list_route(id):
  """
Delete a price list
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list
    
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        replacement_price_list_id:
          type: integer
          example: 2
      required:
        - replacement_price_list_id

responses:
  200:
    description: Price list deleted successfully
  404:
    description: Price list not found
  409:
    description: Price list cannot be deleted because it is being used in existing records
"""
  data = request.get_json()
  if data is None:
    return jsonify({"message": "Request body is required"}), 400
  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  replacement_price_list_id = data.get("replacement_price_list_id")

  result, status_code = delete_price_list(id, replacement_price_list_id)

  return jsonify(result), status_code
