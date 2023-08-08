from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request
from bson import ObjectId
import requests, hashlib

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle


# HTML 화면 보여주기
@app.route('/')
def home():
    # arg로 전달된 페이징을 확인, 없으면 1
    page = int(request.args.get('page', "1"))
    all_events = get_all_events()
    return render_template('index.html', template_events= all_events, pageNo=page)

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
        db.events.insert_one({
            'title':e['title'],
            'beginDt':e['beginDt'],
            'endDt':e['endDt'],
            'placeName':e['placeCdNm'],
            })

    return 'ok'

# 좋아요 클릭 = like
# 좋아요 취소 = dislike
@app.route('/like/<token>/<event_id>/<page>')
def like(token, event_id, page):
    # TODO token -> user_id
    db.userevent.insert_one({'user_id': token, 'event_id': event_id})
    print("THIS IS ALL LIKES DATA" + token, event_id, page)
    return redirect(url_for('home', page=page))

# 행사 데이터를 가공하는 함수
# fav_count열을 포함합니다.
# 현재 로그인된 사용자가 좋아했는지 여부를 포함합니다.
# 6개씩 페이징합니다.
def get_all_events():
    events = list(db.events.find({}))
    def get_fav_count(event):
        event['fav_count'] = len(list(db.userevent.find({'event_id': str(event['_id'])})))
        # TODO 여기서 현재 로그인된 사용자가 즐겨찾기했는지 여부 t/f만 같이 반환
        # event['is_mine'] = len(list(db.userevent.find({'user_id': '____', 'event_id': str(event['_id'])})))
        return event
    
    return [list(map(get_fav_count, events[i:i+4])) for i in range(0, len(events), 4)]
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
