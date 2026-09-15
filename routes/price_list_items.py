from flask import jsonify, request, Blueprint
from database import get_connection
from mysql.connector import Error

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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM `price list items`"
    cursor.execute(query)
    result = cursor.fetchall()

    cursor.close()
    connection.close()

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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT price_list_id, product_id, price FROM `price list items` where id=%s;"
    cursor.execute(query, (id,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result is None:
      return jsonify({"message": "Price List Item not found"}), 404

    return jsonify(result)


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
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    product_id = data.get('product_id')
    price_list_id = data.get('price_list_id')
    price = data.get('price')

    if product_id is None or price_list_id is None or price is None :
      return jsonify({"message": "product_id, price_list_id and price are required"}), 400 

    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return jsonify({"message": "price_list_id must be a positive integer"}), 400
    if not isinstance(product_id, int) or product_id <= 0:
      return jsonify({"message": "product_id must be a positive integer"}), 400
    if not isinstance(price, int) or price < 0:
      return jsonify({"message": "price must be a non-negative integer"}), 400

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

    # check if product exists
    product_query = "SELECT product_id FROM `products` WHERE product_id = %s;"
    cursor.execute(product_query, (product_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "Product not found"}), 404


    # check if product already exists in price list
    query2='''
        SELECT price
        FROM `price list items`
        WHERE price_list_id = %s
        AND product_id = %s;
    '''
    cursor.execute(query2, (price_list_id, product_id,))
    result=cursor.fetchone()
    if result:
       cursor.close()
       connection.close()
       return jsonify({"message": " This Product already exists in the price list"}), 409

    query = "INSERT INTO `price list items` (product_id, price_list_id, price) VALUES (%s, %s, %s);"
    try:
        cursor.execute(query, (product_id, price_list_id, price))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()
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
    if data is None:
        return jsonify({"message": "Request body is required"}), 400

    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    #product_id = data.get('product_id')
    #price_list_id = data.get('price_list_id')
    price = data.get('price')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Get current price list item
    query = "SELECT product_id, price_list_id, price FROM `price list items` WHERE id = %s;"
    cursor.execute(query, (id,))
    current_list = cursor.fetchone()

    # If item doesn't exist
    if current_list is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "price list item not found"}), 404
    '''
    # Keep old value if it wasn't provided
    if product_id is None:
        product_id = current_list["product_id"]
    else:
      if not isinstance(product_id, int) or product_id <= 0:
          return jsonify({"message": "product_id must be a positive integer"}), 400
      # check if product exists
      product_query = "SELECT product_id FROM `products` WHERE product_id = %s;"
      cursor.execute(product_query, (product_id,))
      result = cursor.fetchone()
      if result is None:
          return jsonify({"message": "Product not found"}), 404
      
    if price_list_id is None:
        price_list_id = current_list["price_list_id"]
    else:
      if not isinstance(price_list_id, int) or price_list_id <= 0:
          return jsonify({"message": "price_list_id must be a positive integer"}), 400
      # check if price list exists
      price_list_query = "SELECT price_list_id FROM `price list` WHERE price_list_id = %s;"
      cursor.execute(price_list_query, (price_list_id,))
      result = cursor.fetchone()
      if result is None:
          return jsonify({"message": "Price list not found"}), 404
      '''

    if price is None:
      price = current_list["price"]
    else:
      if not isinstance(price, int) or price < 0:
            cursor.close()
            connection.close()
            return jsonify({"message": "price must be a non-negative integer"}), 400
      
    
    # Update
    query = """
        UPDATE `price list items`
        SET price = %s
        WHERE id = %s;
    """
    try:
        cursor.execute(query, (price, id))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500
    
    cursor.close()
    connection.close()
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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "DELETE FROM `price list items` WHERE id = %s;"

    try:
        cursor.execute(query, (id,))
        connection.commit()
    except Error as e:
            connection.rollback()
    
            if e.errno == 1451:
                cursor.close()
                connection.close()
                return jsonify({
                    "message": "item cannot be deleted because it is being used in existing records."
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
        return jsonify({"message": "Price List Item not found"}), 404
    
    cursor.close()
    connection.close()
    return jsonify({"message": "Price List Item deleted successfully!"}), 200