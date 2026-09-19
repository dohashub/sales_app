from flask import Flask, jsonify, request
from database import get_connection
from flasgger import Swagger
from flask_cors import CORS
from dotenv import load_dotenv
import os

from database import db

from models.products import Product

from routes.products import products_bp
from routes.customers import customers_bp
from routes.price_list import price_list_bp
from routes.price_list_items import price_list_items_bp
from routes.receipts import receipts_bp
from routes.returns import returns_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqlconnector://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

swagger = Swagger(app)

app.register_blueprint(products_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(price_list_bp)
app.register_blueprint(price_list_items_bp)
app.register_blueprint(receipts_bp)
app.register_blueprint(returns_bp)

@app.route('/')
def home():
    return "Sales Management API"

# Receipt Item API
@app.route("/receipt item", methods=["GET"])
def get_receipt_item():
    """
Get all receipt items
---
responses:
  200:
    description: A list of all receipt items
    schema:
      type: array
      items:
        type: object
        properties:
          id:
            type: integer
          receipt#:
            type: integer
          product_id:
            type: integer
          quantity:
            type: integer
          price:
            type: integer
"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM `receipt item`"
    cursor.execute(query)
    result = cursor.fetchall()

    cursor.close()
    connection.close()
    
    return jsonify(result)

# Run Application
if __name__ == "__main__":
    app.run(debug=True)