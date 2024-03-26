from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, origins='*')

@app.route("/api/users", methods=["GET"])
def users():
    return jsonify(
        {
            "users": [
                'Alice',
                'Bob',
                'Charlie' 
            ]      
        }
                 
    )

if __name__ == "__main__":
    app.run(debug=True, port=8080)