from database import db

class PriceListItem(db.Model):
  __tablename__="price list items"

  id = db.Column(db.Integer, primary_key=True)
  price_list_id = db.Column(db.Integer, db.ForeignKey("price list.price_list_id"), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
  price = db.Column(db.Integer, nullable=False)