from flask import Flask, jsonify

# Create a Flask Instance
app = Flask(__name__)

# Create a route decorator
@app.route('/', methods=['GET'])
def home():
    return jsonify({'data': 'hello world'})

# localhost:5000/home/2
@app.route('/home/<int:num>', methods=['GET'])
def disp(num):
    return jsonify({'data': num ** 2})

if __name__ == '__main__':
    app.run(debug=True)



