from database import db
from sqlalchemy.exc import IntegrityError
from models.price_list_items import PriceListItem
from models.price_list import PriceList
from models.products import Product

def get_all_price_list_items():
  price_list_items = PriceListItem.query.all()
  
  result =[
    {
      "id" : item.id,
      "price_list_id" : item.price_list_id,
      "product_id" : item.product_id,
      "price" : item.price
    }
    for item in price_list_items
  ]

  return result, 200

def get_price_list_item(item_id):
  item = PriceListItem.query.get(item_id)

  if item is None:
    return {"message": "Price List Item not found"}, 404

  return {
    "id" : item.id,
    "price_list_id" : item.price_list_id,
    "product_id" : item.product_id,
    "price" : item.price   
  }, 200
  

def add_price_list_item(product_id, price_list_id, price):
  # Check required fields
    if product_id is None or price_list_id is None or price is None :
      return ({"message": "product_id, price_list_id and price are required"}), 400 
    # Validate required fields
    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return ({"message": "price_list_id must be a positive integer"}), 400
    if not isinstance(product_id, int) or product_id <= 0:
      return ({"message": "product_id must be a positive integer"}), 400
    if not isinstance(price, int) or price < 0:
      return ({"message": "price must be a non-negative integer"}), 400
  
    # check if price list exists
    price_list = PriceList.query.get(price_list_id)
    if price_list is None:
        return ({"message": "Price list not found"}), 404
  
    # check if product exists
    product = Product.query.get(product_id)
    if product is None:
        return ({"message": "Product not found"}), 404
  
    # check if product already exists in price list
    item = PriceListItem.query.filter(PriceListItem.product_id==product_id, PriceListItem.price_list_id==price_list_id).first()
    if item:
        return ({"message": "This Product already exists in the price list"}), 409
  
    price_list_item = PriceListItem(
        product_id=product_id,
        price_list_id=price_list_id, 
        price = price
    )
    try:
        db.session.add(price_list_item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return{"message": "Database error"}, 500
    
    return {'message': 'Price List Item added successfully!'}, 201


def update_price_list_item(item_id, price):
  # Get price list item
  price_list_item = PriceListItem.query.get(item_id)

  # If item doesn't exist
  if price_list_item is None:
    return ({"message": "price list item not found"}), 404
  

  if price is None:
    price = price_list_item.price
  else:
    # validate price
    if not isinstance(price, int) or price < 0:
      return ({"message": "price must be a non-negative integer"}), 400
    
  # Update
  price_list_item.price = price

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return ({"message": "Database error"}), 500

  return ({'message': 'Data updated successfully!'}), 200


def delete_price_list_item(item_id):
  price_list_item = PriceListItem.query.get(item_id)
  if price_list_item is None:
    return ({"message": "price list item not found"}), 404
  try:
    db.session.delete(price_list_item)
    db.session.commit()
  except IntegrityError as e:
    db.session.rollback()

    if e.orig.errno == 1451:
        return ({
            "message": "item cannot be deleted because it is being used in existing records."
        }), 409
    
    return ({
        "message": "Database error"
    }), 500

  return ({"message": "Price List Item deleted successfully!"}), 200