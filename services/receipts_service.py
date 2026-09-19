from database import db
from sqlalchemy.exc import IntegrityError
from models.products import Product
from models.price_list_items import PriceListItem
from models.customers import Customer
from models.receipts import Receipt, ReceiptItem


def get_all_receipts(page, limit):
  # Validate page
  try:
      page = int(page)
  except ValueError:
      return {"message": "page must be an integer"}, 400

  if page <= 0:
      return {"message": "page must be a positive integer"}, 400

  # Validate limit
  try:
      limit = int(limit)
  except ValueError:
      return {"message": "limit must be an integer"}, 400

  if limit <= 0:
      return {"message": "limit must be a positive integer"}, 400

  # Get all receipts
  query = Receipt.query

  # Count receipts
  total = query.count()

  # Calculate where this page starts
  offset = (page - 1) * limit

  # Get only the receipts for this page
  receipts = query.offset(offset).limit(limit).all()

  result = []

  # Add Receipt Items to each receipt
  for receipt in receipts:

      receipt_items = ReceiptItem.query.filter(
          ReceiptItem.receipt_no == receipt.receipt_no
      ).all()

      result.append({
          "receipt#": receipt.receipt_no,
          "customer_id": receipt.customer_id,
          "date": receipt.date,
          "total": receipt.total,
          "status": receipt.status,
          "items": [
              {
                  "product_id": item.product_id,
                  "quantity": item.quantity,
                  "price": item.price
              }
              for item in receipt_items
          ]
      })

  return {
      "data": result,
      "page": page,
      "limit": limit,
      "total": total
  }, 200

def get_receipt(receipt_id):
  receipt = Receipt.query.get(receipt_id)
  
  if receipt is None:
    return {"message": "Receipt not found"}, 404

  # add Receipt Items to receipt
  receipt_items = ReceiptItem.query.filter(ReceiptItem.receipt_no == receipt.receipt_no).all()
  result= {
      "receipt#" : receipt.receipt_no,
      "customer_id" : receipt.customer_id,
      "date" : receipt.date,
      "total" : receipt.total,
      "status": receipt.status,
      "items" : [
          {
            "product_id" : item.product_id,
            "quantity" : item.quantity,
            "price" : item.price
          }
          for item in receipt_items
      ]
    }

  return result, 200

def add_receipt(customer_id, receipt_date, items):
  # validate required fields
  if not isinstance(items, list) or not items:
    return {"message": "items must be a non-empty list of dictionaries"}, 400

  if customer_id is None:
    return {"message": "customer_id is required"}, 400

  if not isinstance(customer_id, int) or customer_id <= 0:
    return {"message": "customer_id must be a positive integer"}, 400

  # check if customer exists
  customer = Customer.query.get(customer_id)

  if customer is None:
    return {"message": "Customer not found"}, 404

  # find customer price list
  price_list_id = customer.price_list_id

  # validate items
  for item in items:
    if not isinstance(item, dict):
      return {"message": "Each item must be a dictionary"}, 400

    if "product_id" not in item or "quantity" not in item:
      return {
        "message": "product_id and quantity are required for every item"
      }, 400

    product_id = item["product_id"]
    quantity = item["quantity"]

    if not isinstance(product_id, int) or product_id <= 0:
      return {"message": "product_id must be a positive integer"}, 400

    if not isinstance(quantity, int) or quantity <= 0:
      return {"message": "quantity must be a positive integer"}, 400

  # combine repeated products
  combined_items = {}

  for item in items:
    product_id = item["product_id"]
    quantity = item["quantity"]

    if product_id in combined_items:
      combined_items[product_id] += quantity
    else:
      combined_items[product_id] = quantity

  # check products, prices and stock
  total = 0
  prices = {}

  for product_id, quantity in combined_items.items():

    # check if product exists
    product = Product.query.get(product_id)

    if product is None:
      return {"message": "Product not found"}, 404

    # check if product is active
    if not product.is_active:
      return {"message": "Product is inactive"}, 400

    # check if product exists in the price list
    product_pl = PriceListItem.query.filter(
      PriceListItem.product_id == product_id,
      PriceListItem.price_list_id == price_list_id
    ).first()

    if product_pl is None:
      return {
        "message": "Product not found in the price list of this customer"
      }, 404

    # check stock
    if quantity > product.stock:
      return {"message": "Stock NOT enough"}, 400

    # save price for later
    prices[product_id] = product_pl.price

    # calculate total
    total += quantity * product_pl.price

  # create receipt
  receipt = Receipt(
    customer_id=customer_id,
    date=receipt_date,
    total=total,
    status="COMPLETED"
  )

  try:
    db.session.add(receipt)
    db.session.flush()

    receipt_no = receipt.receipt_no

    # create receipt items and reduce stock
    for product_id, quantity in combined_items.items():

      receipt_item = ReceiptItem(
        receipt_no=receipt_no,
        product_id=product_id,
        quantity=quantity,
        price=prices[product_id]
      )

      db.session.add(receipt_item)

      product = Product.query.get(product_id)
      product.stock -= quantity

    db.session.commit()

    return {"message": "Data added successfully!"}, 201

  except Exception as e:
    db.session.rollback()
    print("ERROR:", e)

    return {"message": "Failed to create receipt"}, 500