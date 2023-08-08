from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
import requests, jwt, datetime, os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'jungle7'


client = MongoClient('localhost', 27017)
db = client.dbjungle
SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")

## 메인 페이지
@app.route('/')
def home():
    # arg로 전달된 페이징을 확인, 없으면 1
    page = int(request.args.get('page', "1"))
    all_events = get_all_events()
    return render_template('index.html', template_events= all_events, pageNo=page)

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
        pwd_hash = bcrypt.generate_password_hash(pwd)
        db.users.insert_one({'nickname':nickname, 'email':email, 'password':pwd_hash})
        
        return redirect(url_for('login'))
    
    return render_template('signup.html') 

@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form['email']
    password = request.form['password']
    
    pw_hash = bcrypt.generate_password_hash(password)
    result = db.users.find_one({'email':email, 'password':pw_hash})
    
    if result is not None:
        payload = {
            'email' : email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return redirect(url_for('home'))
    else:
        return jsonify({'result':'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.', 'token':token})

@app.route('/login')
def login():
    return render_template('login.html')
    
## 대구광역시 open API에 접근해서 데이터를 가져오는 페이지
@app.route('/refresh')
def refresh():
    url = f'http://apis.data.go.kr/6300000/eventDataService/eventDataListJson'
    api_key = r'HF37SOzpRH8DBXxqviNM%2FxjayRLamasAPu7bsT%2F6hu5cK6KT4hRkoQAUVFJOqRxnpjBW4MZMNa5XCMIWRMDnPg%3D%3D'
    api_key_decode = requests.utils.unquote(api_key)
    
    res = requests.get(url, params={'serviceKey':api_key_decode})
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
