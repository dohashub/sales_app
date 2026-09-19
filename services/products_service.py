from models.products import Product
from database import db
from sqlalchemy.exc import IntegrityError

# get all products
def get_all_products(search, product_id, min_stock, max_stock, page, limit):
  # Clean search text
  if search:
    search = search.strip()

  # Validate product_id
  if product_id:
    try:
      product_id = int(product_id)
    except ValueError:
      return ({"message": "product_id must be an integer"}), 400

    if product_id <= 0:
      return ({"message": "product_id must be a positive integer"}), 400

  # Validate min_stock
  if min_stock:
    try:
      min_stock = int(min_stock)
    except ValueError:
      return ({"message": "min_stock must be an integer"}), 400

    if min_stock < 0:
      return ({"message": "min_stock cannot be negative"}), 400

  # Validate max_stock
  if max_stock:
    try:
      max_stock = int(max_stock)
    except ValueError:
      return ({"message": "max_stock must be an integer"}), 400

    if max_stock < 0:
      return ({"message": "max_stock cannot be negative"}), 400

  # Make sure min_stock is not greater than max_stock
  if min_stock is not None and max_stock is not None:
    if min_stock > max_stock:
      return ({
          "message": "min_stock cannot be greater than max_stock"
      }), 400

  # Start with all products
  query = Product.query

  # Name search
  if search:
    query = query.filter(Product.name.like(f"%{search}%"))

  # Product ID filter
  if product_id is not None:
    query = query.filter(Product.product_id == product_id)

  # Minimum stock filter
  if min_stock is not None:
    query = query.filter(Product.stock >= min_stock)

  # Maximum stock filter
  if max_stock is not None:
    query = query.filter(Product.stock <= max_stock)

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

  # Count products after applying filters
  total = query.count()

  # Calculate where this page starts
  offset = (page - 1) * limit

  # Get only the products for this page
  products = query.offset(offset).limit(limit).all()

  # Convert Product objects to JSON
  result = [
      {
          "product_id": product.product_id,
          "name": product.name,
          "stock": product.stock,
          "is_active": product.is_active
      }
      for product in products
  ]

  return {
    "data": result,
    "page": page,
    "limit": limit,
    "total": total
  }, 200

# get one product
def get_product(product_id):
  product = Product.query.get(product_id)
  
  if product is None:
    return ({"message": "Product not found"}), 404

  return {
    "product_id": product.product_id,
    "name": product.name,
    "stock": product.stock,
    "is_active": product.is_active
  }, 200

# add product
def add_product(name, stock):
  # Check required fields
  if name is None or stock is None :
    return {"message": "Name and Stock are required"}, 400 

  # Validate name
  if not isinstance(name, str):
    return {"message": "Name must be a string"}, 400

  name = name.strip()
  if name=="":
    return {"message": "Name is required"}, 400

  # Validate stock
  if not isinstance(stock, int) or stock < 0:
    return {"message": "Stock must be a non-negative integer"}, 400

  # Create product object
  product = Product(
    name=name,
    stock=stock,
    is_active=True
  )

  try:
    db.session.add(product)
    db.session.commit()
  except Exception:
    db.session.rollback()
    return {"message": "Database error"}, 500

  return {'message': 'Data added successfully!'}, 201


#update
def update_product(product_id, name, stock, is_active):
  # get product
  product = Product.query.get(product_id)

  # If product doesn't exist
  if product is None:
    return {"message": "Product not found"}, 404
  
  # Keep old value if it wasn't provided
  if name is None:
    name = product.name
  else:
    # Validate name
    if not isinstance(name, str):
      return ({"message": "Name must be a string"}), 400
    
    name = name.strip()
    if name=="":
      return ({"message": "Name is required"}), 400
    
  if stock is None:
    stock = product.stock
  else:
    # Validate stock
    if not isinstance(stock, int) or stock < 0:
      return ({"message": "Stock must be a non-negative integer"}), 400

  if is_active is None:
    is_active = product.is_active
  if is_active is not None and (not isinstance(is_active, int) or is_active not in (0, 1)):
    return ({"message": "is_active must be 0 or 1"}), 400
  
  # Update
  product.name = name
  product.stock = stock
  product.is_active = is_active

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return ({"message": "Database error"}), 500

  return ({'message': 'Data updated successfully!'}), 200

#delete
def delete_product(product_id):
  product = Product.query.get(product_id)
  if product is None:
    return ({"message": "Product not found"}), 404

  try:
    db.session.delete(product)
    db.session.commit()
  except IntegrityError as e:
    db.session.rollback()

    if e.orig.errno == 1451:
      return({
          "message": "Product cannot be deleted because it is being used in existing records. Set is_active to 0 instead."
      }), 409

    return({
      "message": "Database error"
    }), 500

  return ({"message": "Product deleted successfully!"}), 200