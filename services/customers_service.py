from models.customers import Customer
from models.price_list import PriceList
from database import db
from sqlalchemy.exc import IntegrityError

def get_all_customers(search, customer_id, price_list_id, page, limit):
  # Clean search text
  if search:
    search = search.strip()

  # Validate customer_id
  if customer_id:
    try:
      customer_id = int(customer_id)
    except ValueError:
      return ({"message": "customer_id must be an integer"}), 400

    if customer_id <= 0:
      return ({
          "message": "customer_id must be a positive integer"
      }), 400

  # Validate price_list_id
  if price_list_id:
    try:
      price_list_id = int(price_list_id)
    except ValueError:
      return ({
          "message": "price_list_id must be an integer"
      }), 400

    if price_list_id <= 0:
      return ({
          "message": "price_list_id must be a positive integer"
      }), 400

  query = Customer.query

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

  # Name search
  if search:
    query = query.filter(Customer.name.like(f"%{search}%"))

  # Customer ID filter
  if customer_id is not None:
    query = query.filter(Customer.customer_id == customer_id)

  # Price list ID filter
  if price_list_id is not None:
    query = query.filter(Customer.price_list_id == price_list_id)

  # Count customers after applying filters
  total = query.count()

  # Calculate where this page starts
  offset = (page - 1) * limit

  # Get only the customers for this page
  customers = query.offset(offset).limit(limit).all()

  result = [
    {
        "customer_id" : customer.customer_id,
        "name" : customer.name,
        "price_list_id" : customer.price_list_id
    }
    for customer in customers
  ]

  return {
    "data": result,
    "page": page,
    "limit": limit,
    "total": total
  }, 200


def get_customer(customer_id):
  customer = Customer.query.get(customer_id)
  if customer is None:
    return ({"message": "Customer not found"}), 404

  result = {
    "customer_id" : customer.customer_id,
    "name" : customer.name,
    "price_list_id" : customer.price_list_id
  }
  
  return result, 200


def add_customer(name, price_list_id):
  # Check required fields
  if name is None or price_list_id is None :
    return ({"message": "Name and price_list_id are required"}), 400
  # Validate name
  if not isinstance(name, str):
    return ({"message": "Name must be a string"}), 400

  name = name.strip()
  if name=="":
    return ({"message": "Name is required"}), 400

  # Validate price list ID
  if not isinstance(price_list_id, int) or price_list_id <= 0:
    return ({"message": "price_list_id must be a positive integer"}), 400

  # check if price list exists
  price_list_query = PriceList.query.get(price_list_id)

  if price_list_query is None:
    return ({"message": "Price list not found"}), 404

  # Create customer object
  customer = Customer(
    name=name,
    price_list_id=price_list_id
  )

  try:
    db.session.add(customer)
    db.session.commit()
  except Exception:
    db.session.rollback()
    return ({"message": "Database error"}), 500

  return ({'message': 'Customer added successfully!'}), 201


def update_customer(customer_id, name, price_list_id):
  # Get customer
  customer = Customer.query.get(customer_id)

  # If customer doesn't exist
  if customer is None:
    return ({"message": "Customer not found"}), 404
  
  # Keep old value if it wasn't provided
  if name is None:
    name = customer.name
  else:
    # Validate name
    if not isinstance(name, str):
      return ({"message": "Name must be a string"}), 400
    name = name.strip()
    if name=="":
      return ({"message": "Name is required"}), 400
    
  if price_list_id is None:
    price_list_id = customer.price_list_id
  else:
    # Validate price list ID
    if not isinstance(price_list_id, int) or price_list_id <= 0:
      return ({"message": "price_list_id must be a positive integer"}), 400
      
    # check if price list exists
    price_list_query = PriceList.query.get(price_list_id)
    if price_list_query is None:
      return ({"message": "Price list not found"}), 404
  
  # Update
  customer.name=name
  customer.price_list_id=price_list_id
  
  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return ({"message": "Database error"}), 500

  return ({'message': 'Data updated successfully!'}), 200


def delete_customer(customer_id):
  # Get customer
  customer = Customer.query.get(customer_id)
  if customer is None:
    return ({"message": "Customer not found"}), 404
  
  try:
    db.session.delete(customer)
    db.session.commit()
  except IntegrityError as e:
    db.session.rollback()

    if e.orig.errno == 1451:
      return ({
          "message": "Customer cannot be deleted because it is being used in existing records."
      }), 409
    
    return ({
      "message": "Database error"
    }), 500

  return ({"message": "Customer deleted successfully!"}), 200