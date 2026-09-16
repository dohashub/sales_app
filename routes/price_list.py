from flask import jsonify, request, Blueprint
from database import db
from models.price_list import PriceList
from sqlalchemy.exc import IntegrityError

price_list_bp = Blueprint("price_list", __name__)

# Price List API

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
    price_lists = PriceList.query.all()

    result =[
        {
            "price_list_id" : price_list.price_list_id,
            "price_list_type" : price_list.price_list_type
        }
        for price_list in price_lists
    ]

    return jsonify(result)


# get one price list
@price_list_bp.route("/price-list/<id>", methods=["GET"])
def get_price_list(id):
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
    price_list = PriceList.query.get(id)

    # If price list doesn't exist
    if price_list is None:
      return jsonify({"message": "Price List not found"}), 404

    return jsonify({
    "price_list_id": price_list.price_list_id,
    "price_list_type": price_list.price_list_type
    })


# add price list
@price_list_bp.route("/price-list", methods=["POST"])
def add_price_list():
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
    # Check & Validate required fields
    if price_list_type is None:
      return jsonify({"message": "price_list_type is required"}), 400 
    if not isinstance(price_list_type, str):
        return jsonify({"message": "price_list_type must be a string"}), 400
    price_list_type = price_list_type.strip()
    if price_list_type=="":
      return jsonify({"message": "price_list_type is required"}), 400

    # create price list object
    price_list= PriceList(price_list_type=price_list_type)
    try:
        db.session.add(price_list)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

    return jsonify({'message': 'Data added successfully!'}), 201


# update price list
@price_list_bp.route("/price-list/<id>", methods=["PUT"])
def update_price_list(id):
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

    # Get price list
    price_list = PriceList.query.get(id)

    # If list doesn't exist
    if price_list is None:
        return jsonify({"message": "Price List not found"}), 404
    
    # Keep old value if it wasn't provided
    if price_list_type is None:
        price_list_type = price_list.price_list_type
    else:
      # Validate price list type
      if not isinstance(price_list_type, str):
            return jsonify({"message": "price_list_type must be a string"}), 400
      price_list_type = price_list_type.strip()
      if price_list_type=="":
        return jsonify({"message": "price_list_type is required"}), 400
    
    # Update
    price_list.price_list_type = price_list_type

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

    return jsonify({'message': 'Data updated successfully!'}), 200


# delete price list
@price_list_bp.route("/price-list/<id>", methods=["DELETE"])
def delete_price_list(id):
    """
Delete a price list
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The ID of the price list
responses:
  200:
    description: Price list deleted successfully
  404:
    description: Price list not found
  409:
    description: Price list cannot be deleted because it is being used in existing records
"""
    price_list = PriceList.query.get(id)
    if price_list is None:
        return jsonify({"message": "Price List not found"}), 404

    try:
        db.session.delete(price_list)
        db.session.commit()
    except IntegrityError as e:
            db.session.rollback()
    
            if e.orig.errno == 1451:
                return jsonify({
                    "message": "list cannot be deleted because it is being used in existing records."
                }), 409
            return jsonify({
                "message": "Database error"
            }), 500

    return jsonify({"message": "Price list deleted successfully!"}), 200
