from flask import Flask, jsonify, request, Blueprint
from database import get_connection
from mysql.connector import Error

products_bp = Blueprint("products", __name__)

#------------------------- Products API ----------------------------
# get all products
@products_bp.route("/products", methods=["GET"])
def get_products():
    """
    Get all products or filter products
    ---
    parameters:
      - name: search
        in: query
        type: string
        required: false
        description: Search products by name
        example: Pen

      - name: product_id
        in: query
        type: integer
        required: false
        description: Filter by product ID
        example: 5

      - name: min_stock
        in: query
        type: integer
        required: false
        description: Filter products with stock greater than or equal to this value
        example: 10

      - name: max_stock
        in: query
        type: integer
        required: false
        description: Filter products with stock less than or equal to this value
        example: 20

    responses:
      200:
        description: A list of products
        schema:
          type: array
          items:
            type: object
            properties:
              product_id:
                type: integer
              name:
                type: string
              stock:
                type: integer
              is_active:
                type: integer

      400:
        description: Invalid filter value
    """

    search = request.args.get("search")
    product_id = request.args.get("product_id")
    min_stock = request.args.get("min_stock")
    max_stock = request.args.get("max_stock")

    # Clean search text
    if search:
        search = search.strip()

    # Validate product_id
    if product_id:
        try:
            product_id = int(product_id)
        except ValueError:
            return jsonify({"message": "product_id must be an integer"}), 400

        if product_id <= 0:
            return jsonify({"message": "product_id must be a positive integer"}), 400

    # Validate min_stock
    if min_stock:
        try:
            min_stock = int(min_stock)
        except ValueError:
            return jsonify({"message": "min_stock must be an integer"}), 400

        if min_stock < 0:
            return jsonify({"message": "min_stock cannot be negative"}), 400

    # Validate max_stock
    if max_stock:
        try:
            max_stock = int(max_stock)
        except ValueError:
            return jsonify({"message": "max_stock must be an integer"}), 400

        if max_stock < 0:
            return jsonify({"message": "max_stock cannot be negative"}), 400

    # Make sure min_stock is not greater than max_stock
    if min_stock is not None and max_stock is not None:
        if min_stock > max_stock:
            return jsonify({
                "message": "min_stock cannot be greater than max_stock"
            }), 400

    conditions = []
    values = []

    # Name search
    if search:
        conditions.append("name LIKE %s")
        values.append(f"%{search}%")

    # Product ID filter
    if product_id is not None:
        conditions.append("product_id = %s")
        values.append(product_id)

    # Minimum stock filter
    if min_stock is not None:
        conditions.append("stock >= %s")
        values.append(min_stock)

    # Maximum stock filter
    if max_stock is not None:
        conditions.append("stock <= %s")
        values.append(max_stock)

    # Build query
    query = "SELECT * FROM products"

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

# get one product
@products_bp.route("/products/<id>", methods=["GET"])
def get_product(id):
    """
    Get a product by ID
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the product
    responses:
      200:
        description: Product found
      404:
        description: Product not found
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT name, stock FROM products WHERE product_id = %s;"
    cursor.execute(query, (id,))
    result = cursor.fetchone()

    # If product doesn't exist
    if result is None:
      cursor.close()
      connection.close()
      return jsonify({"message": "Product not found"}), 404
    
    cursor.close()
    connection.close()
    return jsonify(result)

# add product
@products_bp.route("/products", methods=["POST"])
def add_product():
    """
    Add a new product
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
              example: Pen
            stock:
              type: integer
              example: 20
    responses:
      201:
        description: Product added successfully
      400:
        description: Invalid product data
    """
    data = request.get_json()
    # check if there's a json body
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    name = data.get('name')
    stock = data.get('stock')
    #is_active= data.get('is_active')

    if name is None or stock is None :
      return jsonify({"message": "Name and Stock are required"}), 400 
    if not isinstance(name, str):
        return jsonify({"message": "Name must be a string"}), 400

    name = name.strip()
    if name=="":
      cursor.close()
      connection.close()
      return jsonify({"message": "Name is required"}), 400

    if not isinstance(stock, int) or stock < 0:
      return jsonify({"message": "Stock must be a non-negative integer"}), 400

    query = "INSERT INTO products (name, stock, is_active) VALUES (%s, %s, 1);"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, (name, stock,))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500

    cursor.close()
    connection.close()

    return jsonify({'message': 'Data added successfully!'}), 201



# update product
@products_bp.route("/products/<id>", methods=["PUT"])
def update_product(id):
    """
    Update a product
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the product

      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Pen
            stock:
              type: integer
              example: 25
            is_active:
              type: integer
              example: 1

    responses:
      200:
        description: Product updated successfully
      400:
        description: Invalid product data
      404:
        description: Product not found
    """
    data = request.get_json()
    if data is None:
        return jsonify({"message": "Request body is required"}), 400
    if not isinstance(data, dict):
        return jsonify({"message": "Request body must be a JSON object"}), 400
    name = data.get('name') 
    stock = data.get('stock')
    is_active = data.get('is_active')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Get current product
    query = "SELECT name, stock, is_active FROM products WHERE product_id = %s;"
    cursor.execute(query, (id,))
    current_product = cursor.fetchone()

    # If product doesn't exist
    if current_product is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "Product not found"}), 404
    
    # Keep old value if it wasn't provided
    if name is None:
        name = current_product["name"]
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
      
    if stock is None:
        stock = current_product["stock"]
    else:
       if not isinstance(stock, int) or stock < 0:
          cursor.close()
          connection.close()
          return jsonify({"message": "Stock must be a non-negative integer"}), 400

    if is_active is None:
       is_active = current_product["is_active"]
    if is_active is not None and (not isinstance(is_active, int) or is_active not in (0, 1)):
      cursor.close()
      connection.close()
      return jsonify({"message": "is_active must be 0 or 1"}), 400
    
    # Update
    query = """
        UPDATE products
        SET name = %s, stock = %s, is_active = %s
        WHERE product_id = %s;
    """
    try:
        cursor.execute(query, (name, stock, is_active, id))
        connection.commit()
    except Error:
        connection.rollback()
        cursor.close()
        connection.close()
        return jsonify({"message": "Database error"}), 500
    
    cursor.close()
    connection.close()

    return jsonify({'message': 'Data updated successfully!'}), 200

# delete product
@products_bp.route("/products/<id>", methods=["DELETE"])
def delete_product(id):
    """
    Delete a product
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The ID of the product

    responses:
      200:
        description: Product deleted successfully
      404:
        description: Product not found
      409:
        description: Product cannot be deleted because it is being used in existing records
    """
    query = "DELETE FROM products WHERE product_id = %s;"

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
                "message": "Product cannot be deleted because it is being used in existing records. Set is_active to 0 instead."
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
        return jsonify({"message": "Product not found"}), 404
    
    cursor.close()
    connection.close()

    return jsonify({"message": "Product deleted successfully!"}), 200


