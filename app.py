from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request
from bson import ObjectId
import requests

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle


# HTML 화면 보여주기
@app.route('/')
def home():
    # arg로 전달된 페이징을 확인, 없으면 1
    page = int(request.args.get('page', "1"))
    user = request.cookies.get('token')
    all_events = get_all_events(user)
    return render_template('index.html', template_events= all_events, pageNo=page)

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

# 인증
@app.route('/auth')
def auth():
    token = request.args.get('token')
    # TODO token의 인증 과정을 거칩니다.
    user_id = token
    return redirect(url_for('home', user=user_id))
        


# 좋아요 클릭 = like
# 좋아요 취소 = dislike
@app.route('/<islike>/<token>/<event_id>/<page>')
def like(islike, token, event_id, page):
    # TODO token의 인증 과정을 거칩니다.
    if islike == "like":
      db.userevent.insert_one({'user_id': token, 'event_id': event_id})
    else:
      db.userevent.delete_one({'user_id': token, 'event_id': event_id})
    return redirect(url_for('home', page=page))

# 행사 데이터를 가공하는 함수
# fav_count열을 포함합니다.
# 현재 로그인된 사용자가 좋아했는지 여부를 포함합니다.
# 6개씩 페이징합니다.
def get_all_events(user):
    events = list(db.events.find({}))
    def get_fav_count(event):
        event['fav_count'] = len(list(db.userevent.find({'event_id': str(event['_id'])})))
        # TODO 여기서 현재 로그인된 사용자가 즐겨찾기했는지 여부 t/f만 같이 반환
        is_mine = False
        if(user):
            is_mine = len(list(db.userevent.find({'user_id': user, 'event_id': str(event['_id'])}))) > 0
        event['is_mine'] = is_mine
        return event
    
    return [list(map(get_fav_count, events[i:i+4])) for i in range(0, len(events), 4)]
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
