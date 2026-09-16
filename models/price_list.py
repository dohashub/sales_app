from database import db

class PriceList(db.Model):
  __tablename__ = "price list"

  price_list_id = db.Column(db.Integer, primary_key=True)
  price_list_type = db.Column(db.String(255), nullable=False)