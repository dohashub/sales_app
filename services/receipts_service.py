from database import db
from sqlalchemy.exc import IntegrityError
from models.products import Product
from models.price_list_items import PriceListItem
from models.customers import Customer
from models.receipts import Receipt, ReceiptItem


def get_all_receipts():
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

  return result, 200

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
      return ({"message": "items must be a non-empty list of dictionaries"}), 400

  if customer_id is None:
    return ({"message": "customer_id is required"}), 400 

  if not isinstance(customer_id, int) or customer_id <= 0:
    return ({"message": "customer_id must be a positive integer"}), 400

  # check if customer exists
  customer = Customer.query.get(customer_id)
  if customer is None:
      return ({"message": "Customer not found"}), 404

  # find customer price list
  price_list_id = customer.price_list_id

  total=0
  for item in items:
    if not isinstance(item, dict):
        return ({"message": "Each item must be a dictionary"}), 400
    
    if "product_id" not in item or "quantity" not in item:
        return ( {"message": "product_id and quantity are required for every item"} ), 400
    
    product_id= item["product_id"]
    quantity = item["quantity"]

    if not isinstance(product_id, int) or product_id <= 0:
      return ({"message": "product_id must be a positive integer"}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        return ({"message": "quantity must be a positive integer"}), 400

    # check if product is active
    product = Product.query.get(product_id)
    if product is None:
      return ({"message": "Product not found"}), 404
    if not product.is_active:
      return ({"message": "Product is inactive"}), 400

    # check if product exists in the price list
    product_pl = PriceListItem.query.filter(PriceListItem.product_id == product_id, PriceListItem.price_list_id == price_list_id).first()
    if product_pl is None:
        return ({"message": "Product not found in the price list of this customer"}), 404
    
    item["price"]= product_pl.price

    # check stock
    stock= product.stock
    if quantity > stock:
      return ({"message": "Stock NOT enough"}), 400

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


    return ({'message': 'Data added successfully!'}), 201

  except Exception as e:
    db.session.rollback()
    print("ERROR:", e)
    return ({"message": "Failed to create receipt"}), 500


def update_receipt(receipt_id):...

def delete_receipt(receipt_id):...