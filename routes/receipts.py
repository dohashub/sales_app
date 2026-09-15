from flask import jsonify, request, Blueprint
from database import get_connection
from datetime import date
from mysql.connector import Error

receipts_bp = Blueprint("receipts", __name__)

# Receipts API

# get all Receipts
@receipts_bp.route("/receipts", methods=["GET"])
def get_receipts():
    """
Get all receipts
---
responses:
  200:
    description: A list of all receipts with their items
    schema:
      type: array
      items:
        type: object
        properties:
          receipt#:
            type: integer
          customer_id:
            type: integer
          date:
            type: string
            format: date
          total:
            type: integer
          items:
            type: array
            items:
              type: object
              properties:
                product_id:
                  type: integer
                quantity:
                  type: integer
                price:
                  type: integer
"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM receipts"
    cursor.execute(query)
    result = cursor.fetchall()

    # add Receipt Items to receipt
    item_query="SELECT product_id, quantity, price FROM `receipt item` WHERE `receipt#`=%s"

    for item in result:
       receipt_no = item["receipt#"]
       cursor.execute(item_query, (receipt_no,))
       item_query_result= cursor.fetchall()
       item["items"]=item_query_result

    cursor.close()
    connection.close()

    return jsonify(result)

# get one Receipt
@receipts_bp.route("/receipts/<id>", methods=["GET"])
def get_receipt(id):
  """
Get a receipt by ID
---
parameters:
  - name: id
    in: path
    type: integer
    required: true
    description: The receipt number
responses:
  200:
    description: Receipt found with its items
  404:
    description: Receipt not found
"""
  connection = get_connection()
  cursor = connection.cursor(dictionary=True)

  query = "SELECT `receipt#`, customer_id, date, total FROM receipts where `receipt#`=%s;"
  cursor.execute(query, (id,))
  result = cursor.fetchone()

  if result is None:
    cursor.close()
    connection.close()
    return jsonify({"message": "Receipt not found"}), 404

  # add Receipt Items to receipt
  item_query="SELECT product_id, quantity, price FROM `receipt item` WHERE `receipt#`=%s"
  receipt_no = result["receipt#"]
  cursor.execute(item_query, (receipt_no,))
  item_query_result= cursor.fetchall()
  result["items"]=item_query_result

  cursor.close()
  connection.close()

  return jsonify(result)


# create new receipt
@receipts_bp.route("/receipts", methods=["POST"])
def create_receipt():
  """
Create a new receipt
---
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      properties:
        customer_id:
          type: integer
          example: 1
        items:
          type: array
          items:
            type: object
            properties:
              product_id:
                type: integer
                example: 1
              quantity:
                type: integer
                example: 2
responses:
  201:
    description: Receipt created successfully
  400:
    description: Invalid receipt data or insufficient stock
  404:
    description: Customer or product not found
  500:
    description: Failed to create receipt
"""
  data= request.get_json()
  if data is None:
    return jsonify({"message": "Request body is required"}), 400

  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  customer_id = data.get("customer_id")
  receipt_date  = date.today()
  total = 0
  items= data.get("items")

  if not isinstance(items, list) or not items:
      return jsonify({"message": "items must be a list of dictionaries"}), 400

  if customer_id is None:
    return jsonify({"message": "customer_id is required"}), 400 

  if not isinstance(customer_id, int) or customer_id <= 0:
    return jsonify({"message": "customer_id must be a positive integer"}), 400


  connection = get_connection()
  cursor = connection.cursor(dictionary=True)

  # check if customer exists
  customer_query = "SELECT customer_id FROM `customers` WHERE customer_id = %s;"
  cursor.execute(customer_query, (customer_id,))
  result = cursor.fetchone()
  if result is None:
      cursor.close()
      connection.close()
      return jsonify({"message": "Customer not found"}), 404

  # find customer price list
  price_list_query = "SELECT price_list_id FROM customers WHERE customer_id = %s;"
  cursor.execute(price_list_query, (customer_id,))
  result_pl = cursor.fetchone()
  price_list_id = result_pl["price_list_id"]

  for item in items:
    if not isinstance(item, dict):
        cursor.close()
        connection.close()
        return jsonify({"message": "Each item must be a dictionary"}), 400
    
    if "product_id" not in item or "quantity" not in item:
        cursor.close()
        connection.close()
        return jsonify( {"message": "product_id and quantity are required for every item"} ), 400
    
    product_id= item["product_id"]
    quantity = item["quantity"]
    if not isinstance(product_id, int) or product_id <= 0:
      cursor.close()
      connection.close()
      return jsonify({"message": "product_id must be a positive integer"}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        cursor.close()
        connection.close()
        return jsonify({"message": "quantity must be a positive integer"}), 400

    # check if product is active
    product_query = "SELECT is_active FROM products WHERE product_id = %s;"
    cursor.execute(product_query, (product_id,))
    product_result = cursor.fetchone()
    if product_result is None:
      cursor.close()
      connection.close()
      return jsonify({"message": "Product not found"}), 404
    if product_result["is_active"] == 0:
      cursor.close()
      connection.close()
      return jsonify({"message": "Product is inactive"}), 400

    # check if product exists in the price list
    product_query = "SELECT price FROM `price list items` WHERE product_id = %s AND price_list_id = %s;"
    cursor.execute(product_query, (product_id, price_list_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.close()
        connection.close()
        return jsonify({"message": "Product not found in the price list of this customer"}), 404
    
    item["price"]= result["price"]

    # check stock
    product_query = "SELECT stock FROM `products` WHERE product_id = %s;"
    cursor.execute(product_query, (product_id,))
    result = cursor.fetchone()
    stock= result["stock"]
    if quantity > stock:
      cursor.close()
      connection.close()
      return jsonify({"message": "Stock NOT enough"}), 400

    # calculate total
    total+= quantity * item["price"]

  try:
    # create receipt
    query = "INSERT INTO `receipts` (customer_id, date, total) VALUES (%s, %s, %s);"
    cursor.execute(query, (customer_id, receipt_date , total))
    receipt_no = cursor.lastrowid

    # create receipt item
    item_query="INSERT INTO `receipt item` (`receipt#`, product_id, quantity, price) VALUES (%s, %s, %s, %s);"

    for item in items:
        product_id= item["product_id"]
        cursor.execute(item_query, (receipt_no, product_id, item["quantity"], item["price"]))
        # reduce stock
        product_query = "SELECT stock FROM `products` WHERE product_id = %s;"
        cursor.execute(product_query, (product_id,))
        result = cursor.fetchone()
        stock= result["stock"]
        query= "UPDATE products SET stock=%s WHERE product_id=%s;"
        stock-= item["quantity"]
        cursor.execute(query, (stock, product_id))

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'Data added successfully!'}), 201

  except Error as e:
     connection.rollback()
     cursor.close()
     connection.close()
     return jsonify({"message": "Failed to create receipt"}), 500

'''
{
"customer_id": 1,
"date": "Wed, 02 Sep 2026 00:00:00 GMT",
"items": [
    {
        "price": 500,
        "product_id": 2,
        "quantity": 2
    },
    {
        "price": 1000,
        "product_id": 3,
        "quantity": 1
    }
],
"receipt#": 1,
"total": 2000
}


1. Find customer #1
2. Find their price list
3. Find prices

4. Check stock

5. Calculate total

6. Create receipt

7. Reduce stock
'''