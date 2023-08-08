from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from bson import ObjectId
import requests, hashlib

app = Flask(__name__)
app.secret_key = 'jungle7'

client = MongoClient('localhost', 27017)
db = client.dbjungle


## 메인 페이지
@app.route('/')
def home():
    all_events = list(db.events.find({}))
    print(all_events)
    return render_template('index.html', template_events= all_events)

## 회원가입 페이지
# form 입력(nickname, email, pwd, pwd2를 전달받는다.)
# 
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        nickname = request.form['nickname']
        email = request.form['email']
        pwd = request.form['password']
        pwd_confirm = request.form['password2']

        # 확인 pwd가 일치하지 않으면 에러메시지와 함께 [GET]'/signup'으로 리다이렉트
        if pwd != pwd_confirm:
            flash('비밀번호와 확인 비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('signup'))

        # pwd암호화 후 저장
        pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
        db.users.insert_one({'nickname':nickname, 'email':email, 'password':pwd_hash})
        
        return redirect(url_for('login'))
    
    return render_template('signup.html') 

## 로그인 페이지
@app.route('/login')
def login():
    return render_template('login.html')

## 특정 사용자의 좋아요 표시한 카드만 출력해주는 페이지
@app.route('/favorite/<user_id>')
def favorite(user_id):
    users_events = list(db.events.find({'_id':user_id}))
    print(users_events)
    return render_template('index.html', template_events=users_events)
    
## 대구광역시 open API에 접근해서 데이터를 가져오는 페이지
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
