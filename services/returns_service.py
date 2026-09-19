from database import db
from models.returns import Return, ReturnItem
from models.receipts import Receipt, ReceiptItem
from models.products import Product

def get_all_returns(page, limit):
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

    # Get all returns
    query = Return.query

    # Count returns
    total = query.count()

    # Calculate where this page starts
    offset = (page - 1) * limit

    # Get only the returns for this page
    returns = query.offset(offset).limit(limit).all()

    result = []

    # Add Return Items to each return
    for return_record in returns:

        return_items = ReturnItem.query.filter(
            ReturnItem.return_id == return_record.return_id
        ).all()

        result.append({
            "return_id": return_record.return_id,
            "receipt_no": return_record.receipt_no,
            "date": return_record.date,
            "total": return_record.total,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price
                }
                for item in return_items
            ]
        })

    return {
        "data": result,
        "page": page,
        "limit": limit,
        "total": total
    }, 200

def get_return(return_id):
  return_record = Return.query.get(return_id)

  if return_record is None:
      return {"message": "Return not found"}, 404

  return_items = ReturnItem.query.filter(
      ReturnItem.return_id == return_record.return_id
  ).all()

  result = {
      "return_id": return_record.return_id,
      "receipt_no": return_record.receipt_no,
      "date": return_record.date,
      "total": return_record.total,
      "items": [
          {
              "product_id": item.product_id,
              "quantity": item.quantity,
              "price": item.price
          }
          for item in return_items
      ]
  }

  return result, 200


def add_return(receipt_no, return_date, items):
  receipt = Receipt.query.get(receipt_no)

  # validation
  if receipt is None:
      return {"message": "Receipt not found"}, 404

  if receipt.status == "FULLY_RETURNED":
      return {"message": "Receipt has already been fully returned"}, 409

  if not isinstance(items, list) or not items:
      return {"message": "items must be a non-empty list of dictionaries"}, 400

  # Validate each item
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

  # Combine repeated products in the return request
  combined_items = {}

  for item in items:
      product_id = item["product_id"]
      quantity = item["quantity"]

      if product_id in combined_items:
          combined_items[product_id] += quantity
      else:
          combined_items[product_id] = quantity

  # Check returned quantities and calculate total
  total = 0
  prices = {}

  for product_id, quantity in combined_items.items():

      # Find the product in the original receipt
      receipt_item = ReceiptItem.query.filter(
          ReceiptItem.receipt_no == receipt_no,
          ReceiptItem.product_id == product_id
      ).first()

      if receipt_item is None:
          return {
              "message": "Product was not found in the original receipt"
          }, 404

      # Find how much of this product was already returned
      returned_items = ReturnItem.query.join(
          Return
      ).filter(
          Return.receipt_no == receipt_no,
          ReturnItem.product_id == product_id
      ).all()

      already_returned_quantity = sum(
          item.quantity for item in returned_items
      )

      # Calculate how much can still be returned
      remaining_quantity = (
          receipt_item.quantity - already_returned_quantity
      )

      if quantity > remaining_quantity:
          return {
              "message": "Return quantity exceeds the remaining quantity"
          }, 400

      # Use the original price from the receipt
      prices[product_id] = receipt_item.price

      # Calculate refund total
      total += quantity * receipt_item.price

  try:

    # Create the return record
    return_record = Return(
        receipt_no=receipt_no,
        date=return_date,
        total=total
    )

    db.session.add(return_record)
    db.session.flush()

    return_id = return_record.return_id

    # Create return items and restore stock
    for product_id, quantity in combined_items.items():

        return_item = ReturnItem(
            return_id=return_id,
            product_id=product_id,
            quantity=quantity,
            price=prices[product_id]
        )

        db.session.add(return_item)

        product = Product.query.get(product_id)
        product.stock += quantity

    # Check the overall receipt status
    fully_returned = True
    some_returned = False

    for receipt_item in ReceiptItem.query.filter(
        ReceiptItem.receipt_no == receipt_no
    ).all():

        returned_items = ReturnItem.query.join(
            Return
        ).filter(
            Return.receipt_no == receipt_no,
            ReturnItem.product_id == receipt_item.product_id
        ).all()

        already_returned_quantity = sum(
            item.quantity for item in returned_items
        )

        if already_returned_quantity > 0:
            some_returned = True

        if already_returned_quantity < receipt_item.quantity:
            fully_returned = False

    if fully_returned:
        receipt.status = "FULLY_RETURNED"

    elif some_returned:
        receipt.status = "PARTIALLY_RETURNED"

    db.session.commit()

    return {"message": "Return added successfully!"}, 201

  except Exception as e:

    db.session.rollback()
    print("ERROR:", e)

    return {"message": "Failed to create return"}, 500