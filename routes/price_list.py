from flask import jsonify, request, Blueprint
from database import get_connection
from mysql.connector import Error

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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM `price list`"
    cursor.execute(query)
    result = cursor.fetchall()

    cursor.close()
    connection.close()

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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT price_list_type FROM `price list` WHERE price_list_id = %s;"
    cursor.execute(query, (id,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    # If price list doesn't exist
    if result is None:
      return jsonify({"message": "Price List not found"}), 404

    return jsonify(result)


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
    if data is None:
            return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    #price_list_id = data.get('price_list_id')
    price_list_type = data.get('price_list_type')
    
    if price_list_type is None:
      return jsonify({"message": "price_list_type is required"}), 400 
    if not isinstance(price_list_type, str):
        return jsonify({"message": "price_list_type must be a string"}), 400
    price_list_type = price_list_type.strip()
    if price_list_type=="":
      return jsonify({"message": "price_list_type is required"}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = "INSERT INTO `price list` (price_list_type) VALUES (%s);"
    try:
        cursor.execute(query, (price_list_type,))
        connection.commit()
    except Error:
        connection.rollback()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()
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
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    price_list_type = data.get('price_list_type')
    #price_list_id = data.get('price_list_id')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Get current price list
    query = "SELECT price_list_type FROM `price list` WHERE price_list_id = %s;"
    cursor.execute(query, (id,))
    current_list = cursor.fetchone()

    # If list doesn't exist
    if current_list is None:
        return jsonify({"message": "Price List not found"}), 404
    
    # Keep old value if it wasn't provided
    if price_list_type is None:
        price_list_type = current_list["price_list_type"]
    else:
      if not isinstance(price_list_type, str):
            return jsonify({"message": "price_list_type must be a string"}), 400
      price_list_type = price_list_type.strip()
      if price_list_type=="":
        return jsonify({"message": "price_list_type is required"}), 400
    
    # Update
    query = """
        UPDATE `price list`
        SET price_list_type = %s
        WHERE price_list_id = %s;
    """
    try:
        cursor.execute(query, (price_list_type, id))
        connection.commit()
    except Error:
        connection.rollback()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()

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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "DELETE FROM `price list` WHERE price_list_id = %s;"

    try:
        cursor.execute(query, (id,))
        connection.commit()
    except Error as e:
            connection.rollback()
    
            if e.errno == 1451:
                cursor.close()
                connection.close()
                return jsonify({
                    "message": "list cannot be deleted because it is being used in existing records."
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
        return jsonify({"message": "price list not found"}), 404
    cursor.close()
    connection.close()

    return jsonify({"message": "Price list deleted successfully!"}), 200
