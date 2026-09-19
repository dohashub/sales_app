from flask import jsonify, request, Blueprint
from datetime import date
from services.receipts_service import get_all_receipts, get_receipt, add_receipt

receipts_bp = Blueprint("receipts", __name__)

#--- Receipts API

# get all Receipts
@receipts_bp.route("/receipts", methods=["GET"])
def get_receipts():
  """
  Get all receipts
  ---
  parameters:
    - name: page
      in: query
      type: integer
      required: false
      default: 1
      description: Page number

    - name: limit
      in: query
      type: integer
      required: false
      default: 10
      description: Number of receipts per page

  responses:
    200:
      description: A list of receipts with their items
      schema:
        type: object
        properties:
          data:
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
                status:
                  type: string
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
      description: Invalid pagination value
      schema:
        type: object
        properties:
          message:
            type: string
  """

  page = request.args.get("page", 1)
  limit = request.args.get("limit", 10)

  result, status_code = get_all_receipts(page, limit)

  return jsonify(result), status_code

# get one Receipt
@receipts_bp.route("/receipts/<id>", methods=["GET"])
def get_receipt_route(id):
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
  result, status_code = get_receipt(id)
  
  return jsonify(result), status_code


# create new receipt
@receipts_bp.route("/receipts", methods=["POST"])
def create_receipt_route():
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
  items= data.get("items")

  result, status_code = add_receipt(customer_id, receipt_date, items)

  return jsonify(result), status_code
