from pymongo import MongoClient
from flask import Flask, render_template, jsonify
from bson import ObjectId
import requests

app = Flask(__name__)

client = MongoClient('localhost',27017)
db = client.dbjungle


# HTML 화면 보여주기 
@app.route('/')
def home():
    all_events = list(db.events.find({}))
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
    
@app.route('/refresh')
def refresh():
    url = f'http://apis.data.go.kr/6300000/eventDataService/eventDataListJson?serviceKey=HF37SOzpRH8DBXxqviNM%2FxjayRLamasAPu7bsT%2F6hu5cK6KT4hRkoQAUVFJOqRxnpjBW4MZMNa5XCMIWRMDnPg%3D%3D'
    res = requests.get(url)
    events = res.json()['msgBody']

    for e in events:
        db.events.insert_one({'title':e['title'], 'beginDt':e['beginDt'], 'endDt':e['endDt'], 'placeName':e['placeCdNm'], 'fav_count':0})

    return 'ok'

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)