from database import db

class Product(db.Model):
  __tablename__ = "products"

  product_id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False)
  stock = db.Column(db.Integer, nullable=False)
  is_active = db.Column(db.Boolean, nullable=False, default=True)