from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('mongodb://test:test@3.34.94.133',27017)
db = client.dbjungle


# HTML 화면 보여주기 
@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)