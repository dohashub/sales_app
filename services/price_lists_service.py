from database import db
from models.price_list import PriceList
from models.customers import Customer
from models.price_list_items import PriceListItem
from sqlalchemy.exc import IntegrityError

def get_all_price_lists(page, limit):
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

    # Get all price lists
    query = PriceList.query

    # Count price lists
    total = query.count()

    # Calculate where this page starts
    offset = (page - 1) * limit

    # Get only the price lists for this page
    price_lists = query.offset(offset).limit(limit).all()

    result = [
        {
            "price_list_id": price_list.price_list_id,
            "price_list_type": price_list.price_list_type
        }
        for price_list in price_lists
    ]

    return {
        "data": result,
        "page": page,
        "limit": limit,
        "total": total
    }, 200

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


def delete_price_list(price_list_id, replacement_price_list_id):
  # Validate replacement ID
  if replacement_price_list_id is None:
      return {"message": "replacement_price_list_id is required"}, 400

  try:
      replacement_price_list_id = int(replacement_price_list_id)
  except ValueError:
      return {"message": "replacement_price_list_id must be an integer"}, 400

  if replacement_price_list_id <= 0:
      return {"message": "replacement_price_list_id must be a positive integer"}, 400

  if price_list_id == replacement_price_list_id:
      return {
          "message": "Replacement price list must be different from the price list being deleted"
      }, 409

  # Get price list
  price_list = PriceList.query.get(price_list_id)

  if price_list is None:
      return {"message": "Price List not found"}, 404

  # Get replacement price list
  replacement_price_list = PriceList.query.get(replacement_price_list_id)

  if replacement_price_list is None:
      return {"message": "Replacement price list not found"}, 404

  # Reassign customers
  customers = Customer.query.filter(
      Customer.price_list_id == price_list_id
  ).all()

  for customer in customers:
      customer.price_list_id = replacement_price_list_id

  # Delete price list items
  price_list_items = PriceListItem.query.filter(PriceListItem.price_list_id == price_list_id).all()

  for item in price_list_items:
      db.session.delete(item)

  try:
      db.session.delete(price_list)
      db.session.commit()
  except IntegrityError as e:
      db.session.rollback()

      if e.orig.errno == 1451:
          return {
              "message": "Price list cannot be deleted because it is being used in existing records."
          }, 409

      return {"message": "Database error"}, 500

  return {"message": "Price list deleted successfully!"}, 200