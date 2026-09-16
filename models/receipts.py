from database import db

class Receipt(db.Model):
  __tablename__ = "receipts"

  receipt_no = db.Column("receipt#", db.Integer, primary_key=True)
  customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=False)
  date = db.Column(db.Date, nullable=False)
  total = db.Column(db.Integer, nullable=False)



class ReceiptItem(db.Model):
  __tablename__ = "receipt item"

  id = db.Column(db.Integer, primary_key=True)
  receipt_no = db.Column("receipt#", db.Integer, db.ForeignKey("receipts.receipt#"), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  price = db.Column(db.Integer, nullable=False)