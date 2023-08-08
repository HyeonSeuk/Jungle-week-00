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
    tab = request.args.get('tab', "all")

    user = request.cookies.get('token')
    all_events = get_all_events(user)
    if(tab == 'fav'):
        all_events = get_fav_events(user)
    return render_template('index.html', template_events= chunk_events(all_events), pageNo=page, tab=tab)

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

'''
tab 현재 탭 정보: all or fav
islike 좋아요 또는 좋아요 취소
event_id 행사 정보
page 페이징 넘버
'''
@app.route('/<tab>/<islike>/<event_id>/<page>')
def like(tab, islike, event_id, page):
    print("TEST", tab, islike, event_id, page)
    # TODO token의 인증 과정을 거칩니다.
    token = request.cookies.get('token')
    user = token
    if islike == "like": # like or dislike
      db.userevent.insert_one({'user_id': user, 'event_id': event_id})
    else:
      db.userevent.delete_one({'user_id': user, 'event_id': event_id})
    return redirect(url_for('home', page=page, tab=tab))

# 행사 데이터를 가공
# 4개씩 페이징합니다.
def chunk_events(events):
    return [events[i:i+4] for i in range(0, len(events), 4)]

# fav_count, is_mine
def get_all_events(user):
    events = list(db.events.find({}))
    for event in events:
        event['fav_count'] = len(list(db.userevent.find({'event_id': str(event['_id'])})))
        event['is_mine'] = False
        if(user):
            event['is_mine'] = len(list(db.userevent.find({'user_id': user, 'event_id': str(event['_id'])}))) > 0
    return events

# 좋아요한 데이터만 가져옵니다.
def get_fav_events(user):
    events = get_all_events(user)
    all_favs = []
    for event in events:
        if(event['is_mine']): all_favs.append(event)
    return all_favs
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
