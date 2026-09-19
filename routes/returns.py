from flask import jsonify, request, Blueprint
from datetime import date

from services.returns_service import (
    add_return,
    get_all_returns,
    get_return
)


returns_bp = Blueprint("returns", __name__)


@returns_bp.route("/returns", methods=["GET"])
def get_returns():
  """
  Get all returns
  ---
  tags:
    - Returns

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
      description: Number of returns per page

  responses:
    200:
      description: List of returns
      schema:
        type: object
        properties:
          data:
            type: array
            items:
              type: object
              properties:
                return_id:
                  type: integer
                  example: 1
                receipt_no:
                  type: integer
                  example: 5
                date:
                  type: string
                  format: date
                  example: "2026-09-19"
                total:
                  type: integer
                  example: 200
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      product_id:
                        type: integer
                        example: 3
                      quantity:
                        type: integer
                        example: 2
                      price:
                        type: integer
                        example: 100
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

  result, status_code = get_all_returns(page, limit)

  return jsonify(result), status_code


@returns_bp.route("/returns/<id>", methods=["GET"])
def get_return_route(id):
  """
  Get a return by ID
  ---
  tags:
    - Returns
  parameters:
    - name: id
      in: path
      required: true
      type: integer
      description: Return ID
      example: 1
  responses:
    200:
      description: Return found successfully
      schema:
        type: object
        properties:
          return_id:
            type: integer
            example: 1
          receipt_no:
            type: integer
            example: 5
          date:
            type: string
            format: date
            example: "2026-09-19"
          total:
            type: integer
            example: 200
          items:
            type: array
            items:
              type: object
              properties:
                product_id:
                  type: integer
                  example: 3
                quantity:
                  type: integer
                  example: 2
                price:
                  type: integer
                  example: 100
    404:
      description: Return not found
      schema:
        type: object
        properties:
          message:
            type: string
            example: "Return not found"
  """
  result, status_code = get_return(id)

  return jsonify(result), status_code


@returns_bp.route("/returns", methods=["POST"])
def create_return_route():
  """
  Create a return
  ---
  tags:
    - Returns
  parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        required:
          - receipt_no
          - items
        properties:
          receipt_no:
            type: integer
            example: 5
          items:
            type: array
            items:
              type: object
              required:
                - product_id
                - quantity
              properties:
                product_id:
                  type: integer
                  example: 3
                quantity:
                  type: integer
                  example: 2
  responses:
    201:
      description: Return created successfully
      schema:
        type: object
        properties:
          message:
            type: string
            example: "Return added successfully!"
    400:
      description: Invalid return data
      schema:
        type: object
        properties:
          message:
            type: string
    404:
      description: Receipt or product not found
      schema:
        type: object
        properties:
          message:
            type: string
    409:
      description: Receipt has already been fully returned
      schema:
        type: object
        properties:
          message:
            type: string
  """
  data = request.get_json()

  if data is None:
      return jsonify({"message": "Request body is required"}), 400

  if not isinstance(data, dict):
      return jsonify({"message": "Request body must be a JSON object"}), 400

  receipt_no = data.get("receipt_no")
  return_date = date.today()
  items = data.get("items")

  result, status_code = add_return(
      receipt_no,
      return_date,
      items
  )

  return jsonify(result), status_code