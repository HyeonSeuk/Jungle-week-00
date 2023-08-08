from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request
from flask_bcrypt import Bcrypt
import requests, hashlib, jwt, datetime, os

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('localhost', 27017)
db = client.dbjungle
SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")

# HTML 화면 보여주기
@app.route('/')
def home():
    all_events = list(db.events.find({}))
    print(all_events)
    return render_template('index.html', template_events= all_events)

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        nickname = request.form['nickname']
        email = request.form['email']
        password = request.form['password']

        pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        db.users.insert_one({'nickname':nickname, 'email':email, 'password':pw_hash})
        
        return redirect(url_for('login', msg="회원가입에 성공하였습니다."))

@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form['email']
    password = request.form['password']
    
    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    result = db.users.find_one({'email':email, 'password':pw_hash})
    
    if result is not None:
        payload = {
            'email' : email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return redirect(url_for('home'))
    else:
        return jsonify({'result':'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})



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
