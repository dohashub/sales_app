from database import db
from models.price_list import PriceList
from sqlalchemy.exc import IntegrityError

def get_all_price_lists():
  price_lists = PriceList.query.all()
  
  result =[
    {
        "price_list_id" : price_list.price_list_id,
        "price_list_type" : price_list.price_list_type
    }
    for price_list in price_lists
  ]

  return result, 200

def get_price_list(price_list_id):
  price_list = PriceList.query.get(price_list_id)
  
  # If price list doesn't exist
  if price_list is None:
    return ({"message": "Price List not found"}), 404

  return{
  "price_list_id": price_list.price_list_id,
  "price_list_type": price_list.price_list_type
  }, 200

def add_price_list(price_list_type):
  # Check & Validate required fields
  if price_list_type is None:
    return ({"message": "price_list_type is required"}), 400 
  if not isinstance(price_list_type, str):
      return ({"message": "price_list_type must be a string"}), 400
  price_list_type = price_list_type.strip()
  if price_list_type=="":
    return ({"message": "price_list_type is required"}), 400

  # create price list object
  price_list= PriceList(price_list_type=price_list_type)
  try:
      db.session.add(price_list)
      db.session.commit()
  except Exception:
      db.session.rollback()
      return ({"message": "Database error"}), 500

  return ({'message': 'Data added successfully!'}), 201

def update_price_list(price_list_id, price_list_type):
  # Get price list
  price_list = PriceList.query.get(price_list_id)

  # If list doesn't exist
  if price_list is None:
      return ({"message": "Price List not found"}), 404
  
  # Keep old value if it wasn't provided
  if price_list_type is None:
      price_list_type = price_list.price_list_type
  else:
    # Validate price list type
    if not isinstance(price_list_type, str):
          return ({"message": "price_list_type must be a string"}), 400
    price_list_type = price_list_type.strip()
    if price_list_type=="":
      return ({"message": "price_list_type is required"}), 400
  
  # Update
  price_list.price_list_type = price_list_type

  try:
      db.session.commit()
  except Exception:
      db.session.rollback()
      return ({"message": "Database error"}), 500

  return ({'message': 'Data updated successfully!'}), 200


def delete_price_list(price_list_id):
  price_list = PriceList.query.get(price_list_id)
  if price_list is None:
    return ({"message": "Price List not found"}), 404

  try:
    db.session.delete(price_list)
    db.session.commit()
  except IntegrityError as e:
    db.session.rollback()

    if e.orig.errno == 1451:
        return ({
            "message": "list cannot be deleted because it is being used in existing records."
        }), 409
    return ({
        "message": "Database error"
    }), 500

  return ({"message": "Price list deleted successfully!"}), 200