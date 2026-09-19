from flask import Flask, jsonify, request, Blueprint
from services.products_service import get_all_products, get_product, add_product, update_product, delete_product

products_bp = Blueprint("products", __name__)

#-- Products API
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

    - name: product_id
      in: query
      type: integer
      required: false

    - name: min_stock
      in: query
      type: integer
      required: false

    - name: max_stock
      in: query
      type: integer
      required: false
    
    - name: page
      in: query
      type: integer
      required: false
      default: 1

    - name: limit
      in: query
      type: integer
      required: false
      default: 10

  responses:
    200:
      description: A list of products
      schema:
        type: object
        properties:
          data:
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
                  type: boolean
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
  product_id = request.args.get("product_id")
  min_stock = request.args.get("min_stock")
  max_stock = request.args.get("max_stock")

  page = request.args.get("page", 1)
  limit = request.args.get("limit", 10)

  result, status_code = get_all_products(search, product_id, min_stock, max_stock, page, limit)

  return jsonify(result), status_code

# get one product
@products_bp.route("/products/<id>", methods=["GET"])
def get_product_route(id):
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
  result, status_code = get_product(id)

  return jsonify(result), status_code
    

# add product
@products_bp.route("/products", methods=["POST"])
def add_product_route():
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

  result, status_code = add_product(name, stock)

  return jsonify(result), status_code

# update product
@products_bp.route("/products/<id>", methods=["PUT"])
def update_product_route(id):
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
  # Check request body
  if data is None:
    return jsonify({"message": "Request body is required"}), 400
  
  if not isinstance(data, dict):
    return jsonify({"message": "Request body must be a JSON object"}), 400
  
  name = data.get('name') 
  stock = data.get('stock')
  is_active = data.get('is_active')

  result, status_code = update_product(id, name, stock, is_active)

  return jsonify(result), status_code

# delete product
@products_bp.route("/products/<id>", methods=["DELETE"])
def delete_product_route(id):
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
  result, status_code = delete_product(id)

  return jsonify(result), status_code
