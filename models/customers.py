from database import db

class Customer(db.Model):
  __tablename__ = "customers"

  customer_id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False)
  price_list_id = db.Column(db.Integer, db.ForeignKey("price list.price_list_id"))