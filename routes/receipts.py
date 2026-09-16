from flask import jsonify, request, Blueprint
from database import db
from datetime import date
from sqlalchemy.exc import IntegrityError
from models.products import Product
from models.price_list import PriceList
from models.price_list_items import PriceListItem
from models.customers import Customer
from models.receipts import Receipt, ReceiptItem

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
    receipts = Receipt.query.all()
    result=[]
    # add Receipt Items to receipt
    for receipt in receipts:
      receipt_items = ReceiptItem.query.filter(ReceiptItem.receipt_no == receipt.receipt_no).all()
      result.append({
          "receipt#" : receipt.receipt_no,
          "customer_id" : receipt.customer_id,
          "date" : receipt.date,
          "total" : receipt.total,
          "items" : [
             {
                "product_id" : item.product_id,
                "quantity" : item.quantity,
                "price" : item.price
             }
             for item in receipt_items
          ]
       })

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
  receipt = Receipt.query.get(id)

  if receipt is None:
    return jsonify({"message": "Receipt not found"}), 404

  # add Receipt Items to receipt
  receipt_items = ReceiptItem.query.filter(ReceiptItem.receipt_no == receipt.receipt_no).all()
  result= {
      "receipt#" : receipt.receipt_no,
      "customer_id" : receipt.customer_id,
      "date" : receipt.date,
      "total" : receipt.total,
      "items" : [
          {
            "product_id" : item.product_id,
            "quantity" : item.quantity,
            "price" : item.price
          }
          for item in receipt_items
      ]
    }

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
  # check request body
  if data is None:
    return jsonify({"message": "Request body is required"}), 400

  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400
  
  customer_id = data.get("customer_id")
  receipt_date  = date.today()
  total = 0
  items= data.get("items")

  # validate required fields
  if not isinstance(items, list) or not items:
      return jsonify({"message": "items must be a non-empty list of dictionaries"}), 400

  if customer_id is None:
    return jsonify({"message": "customer_id is required"}), 400 

  if not isinstance(customer_id, int) or customer_id <= 0:
    return jsonify({"message": "customer_id must be a positive integer"}), 400

  # check if customer exists
  customer = Customer.query.get(customer_id)
  if customer is None:
      return jsonify({"message": "Customer not found"}), 404

  # find customer price list
  price_list_id = customer.price_list_id

  for item in items:
    if not isinstance(item, dict):
        return jsonify({"message": "Each item must be a dictionary"}), 400
    
    if "product_id" not in item or "quantity" not in item:
        return jsonify( {"message": "product_id and quantity are required for every item"} ), 400
    
    product_id= item["product_id"]
    quantity = item["quantity"]

    if not isinstance(product_id, int) or product_id <= 0:
      return jsonify({"message": "product_id must be a positive integer"}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"message": "quantity must be a positive integer"}), 400

    # check if product is active
    product = Product.query.get(product_id)
    if product is None:
      return jsonify({"message": "Product not found"}), 404
    if not product.is_active:
      return jsonify({"message": "Product is inactive"}), 400

    # check if product exists in the price list
    product_pl = PriceListItem.query.filter(PriceListItem.product_id == product_id, PriceListItem.price_list_id == price_list_id).first()
    if product_pl is None:
        return jsonify({"message": "Product not found in the price list of this customer"}), 404
    
    item["price"]= product_pl.price

    # check stock
    stock= product.stock
    if quantity > stock:
      return jsonify({"message": "Stock NOT enough"}), 400

    # calculate total
    total+= quantity * item["price"]

  # create receipt
  receipt = Receipt(
        customer_id = customer_id,
        date = receipt_date,
        total = total 
  )

  try:
    db.session.add(receipt)
    db.session.flush()
    
    receipt_no = receipt.receipt_no

    # create receipt item    
    for item in items:
        product_id= item["product_id"]
        receipt_item = ReceiptItem(
            receipt_no = receipt_no,
            product_id = product_id,
            quantity = item["quantity"],
            price = item["price"]
        )
        db.session.add(receipt_item)

        # reduce stock
        product= Product.query.get(product_id)
        stock= product.stock
        stock-= item["quantity"]
        product.stock = stock

    db.session.commit()


    return jsonify({'message': 'Data added successfully!'}), 201

  except Exception as e:
     db.session.rollback()
     print("ERROR:", e)
     return jsonify({"message": "Failed to create receipt"}), 500
