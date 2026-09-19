from database import db

class Return(db.Model):
    __tablename__ = "returns"

    return_id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.Integer,db.ForeignKey("receipts.receipt#"),nullable=False)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Integer, nullable=False)

from database import db


class ReturnItem(db.Model):
    __tablename__ = "return items"

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(
        db.Integer,
        db.ForeignKey("returns.return_id"),
        nullable=False
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.product_id"),
        nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)