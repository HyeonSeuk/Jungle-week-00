from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('localhost',27017)
db = client.dbjungle


# HTML 화면 보여주기 
@app.route('/')
def home():
    all_events = list(db.user.find({}))
    print(all_events)
    return render_template('index.html', template_events= all_events)

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/favorite/<user_id>')
def favorite(user_id):
    return render_template('index.html')
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)