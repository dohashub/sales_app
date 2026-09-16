from flask import jsonify, request, Blueprint
from database import db
from sqlalchemy.exc import IntegrityError
from models.price_list_items import PriceListItem
from models.price_list import PriceList
from models.products import Product

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
    price_list_items = PriceListItem.query.all()

    result =[
        {
            "id" : item.id,
            "price_list_id" : item.price_list_id,
            "product_id" : item.product_id,
            "price" : item.price
        }
        for item in price_list_items
    ]

    return jsonify(result)

# get one price list item
@price_list_items_bp.route("/price-list-items/<id>", methods=["GET"])
def get_price_list_item(id):
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
    item = PriceListItem.query.get(id)

    if item is None:
      return jsonify({"message": "Price List Item not found"}), 404

    return jsonify(
      {
        "id" : item.id,
        "price_list_id" : item.price_list_id,
        "product_id" : item.product_id,
        "price" : item.price   
      }
    )


# add price list item
@price_list_items_bp.route("/price-list-items", methods=["POST"])
def add_price_list_item():
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

    # Check required fields
    if product_id is None or price_list_id is None or price is None :
      return jsonify({"message": "product_id, price_list_id and price are required"}), 400 
    # Validate required fields
    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return jsonify({"message": "price_list_id must be a positive integer"}), 400
    if not isinstance(product_id, int) or product_id <= 0:
      return jsonify({"message": "product_id must be a positive integer"}), 400
    if not isinstance(price, int) or price < 0:
      return jsonify({"message": "price must be a non-negative integer"}), 400

    # check if price list exists
    price_list = PriceList.query.get(price_list_id)
    if price_list is None:
        return jsonify({"message": "Price list not found"}), 404

    # check if product exists
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"message": "Product not found"}), 404

    # check if product already exists in price list
    item = PriceListItem.query.filter(PriceListItem.product_id==product_id, PriceListItem.price_list_id==price_list_id).first()
    if item:
       return jsonify({"message": " This Product already exists in the price list"}), 409

    price_list_item = PriceListItem(
        product_id=product_id,
        price_list_id=price_list_id, 
        price = price
    )
    try:
        db.session.add(price_list_item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500
    
    return jsonify({'message': 'Price List Item added successfully!'}), 201


# update price list items
@price_list_items_bp.route("/price-list-items/<id>", methods=["PUT"])
def update_price_list_items(id):
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
    
    #product_id = data.get('product_id')
    #price_list_id = data.get('price_list_id')
    price = data.get('price')

    # Get price list item
    price_list_item = PriceListItem.query.get(id)

    # If item doesn't exist
    if price_list_item is None:
        return jsonify({"message": "price list item not found"}), 404
    

    if price is None:
      price = price_list_item.price
    else:
      # validate price
      if not isinstance(price, int) or price < 0:
            return jsonify({"message": "price must be a non-negative integer"}), 400
      
    # Update
    price_list_item.price = price

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Database error"}), 500

    return jsonify({'message': 'Data updated successfully!'}), 200


# delete price list item
@price_list_items_bp.route("/price-list-items/<id>", methods=["DELETE"])
def delete_price_list_item(id):
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
    price_list_item = PriceListItem.query.get(id)
    if price_list_item is None:
        return jsonify({"message": "price list item not found"}), 404
    try:
        db.session.delete(price_list_item)
        db.session.commit()
    except IntegrityError as e:
            db.session.rollback()
    
            if e.orig.errno == 1451:
                return jsonify({
                    "message": "item cannot be deleted because it is being used in existing records."
                }), 409
            
            return jsonify({
                "message": "Database error"
            }), 500

    return jsonify({"message": "Price List Item deleted successfully!"}), 200