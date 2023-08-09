from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash, make_response
from flask_bcrypt import Bcrypt
import requests, jwt, datetime, os, time
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
bcrypt = Bcrypt(app)
scheduler = BackgroundScheduler()
scheduler.configure({'apscheduler.daemonic':False})
app.secret_key = 'jungle7'

client = MongoClient('localhost', 27017)
db = client.dbjungle
SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")


## 메인 페이지
@app.route('/')
def home():
    page = int(request.args.get('page', "1"))
    tab = request.args.get('tab', "all")
    sort = request.args.get('sort', 'like')
    option = request.args.get('option', 'beforeDue')

    token = request.cookies.get('token', None)
    user_id = get_user_id(token)
    nickname = db.users.find_one({'_id': user_id})['nickname'] if user_id else None
    logged_in = nickname != None

    events = get_all_events(user_id) if tab == 'all' else get_fav_events(user_id)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    events = list(filter(lambda each: each['endDt'] > today, events)) if option == 'beforeDue' else events
     
    if sort == "like":
        events.sort(key=lambda x: x['fav_count'], reverse=True)
    elif sort == "date":
        events.sort(key=lambda x: x['endDt'])
    elif sort == "name":
        events.sort(key=lambda x: x['title'])
        
    return render_template('index.html', paging= paging(events, page), pageNo=page, tab=tab, sort=sort, nickname=nickname, loggedIn=logged_in, option=option)

## 회원가입 페이지
# form 입력(nickname, email, pwd, pwd2를 전달받는다.)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    nickname = request.form['nickname']
    email = request.form['email']
    pwd = request.form['password']
    pwd_confirm = request.form['password2']

    # 확인 pwd가 일치하지 않으면 에러메시지와 함께 [GET]'/signup'으로 리다이렉트
    if pwd != pwd_confirm:
        # flash('비밀번호와 확인 비밀번호가 일치하지 않습니다.', 'error')
        # return redirect(url_for('/signup'))
        return jsonify({'result':'fail','msg':'비밀번호가 일치하지 않습니다!'})

    # 이미 저장된 email이 있으면 반려함
    result = db.users.find_one({'email':email})
    if result:
        #flash('등록된 이메일이 이미 존재합니다.', 'error')
        #return redirect(url_for('signup'))
        return jsonify({'result':'fail','msg':'등록된 이메일이 이미 존재합니다.'})

    # pwd암호화 후 저장
    pwd_hash = bcrypt.generate_password_hash(pwd).decode('utf-8')
    db.users.insert_one({'nickname':nickname, 'email':email, 'password':pwd_hash})

    return jsonify({'result':'success','msg':'회원가입 성공'})

# 로그인 요청 API
@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form['email']
    password = request.form['password']
    result = db.users.find_one({'email':email})

    success = make_response(redirect(url_for('home')))
    failure = make_response(redirect(url_for('login')))

    # 일치하는 계정 없음
    if not result:
        flash('계정이 존재하지 않습니다.')
        return failure

    # pw가 일치하지 않음
    if not bcrypt.check_password_hash(result['password'], password):
        flash('아이디/비밀번호가 일치하지 않습니다.')
        return failure
        
    payload = {
        'id': str(result['_id']),
        # 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    # 쿠키 만료를 1분으로 설정하여 응답에 삽입, 반환
    expire_date = datetime.datetime.now() + datetime.timedelta(minutes=30)
    success.set_cookie('token', token, expires=expire_date) 
    return success

## 로그아웃 요청
@app.route('/api/logout')
def api_logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', '', expires=-1)
    return response

@app.route('/login')
def login():
    return render_template('login.html')
<<<<<<< HEAD

# get user id from token
def get_user_id(token):
    if not token:
        return ''
    return ObjectId(jwt.decode(token, SECRET_KEY, algorithms='HS256')['id'])

=======
    
>>>>>>> 3a282f8... refactor(app.py): 가독성을 위해 주석추가 및 코드 위치 이동
'''
tab 현재 탭 정보: all or fav
islike 좋아요 또는 좋아요 취소
event_id 행사 정보
page 페이징 넘버
'''
@app.route('/fav/<tab>/<islike>/<event_id>/<page>/<sort>/<option>')
def like(tab, islike, event_id, page, sort, option):
    token = request.cookies.get('token')
    user = get_user_id(token)
    if not user:
      flash("로그인이 필요한 기능입니다.")
      return redirect(url_for('home', page=page, tab=tab))
    if islike == "like": # like or dislike
      db.userevent.insert_one({'user_id': user, 'event_id': event_id})
    else:
      db.userevent.delete_one({'user_id': user, 'event_id': event_id})
    return redirect(url_for('home', page=page, tab=tab, sort=sort, option=option))

# get user id from token
def get_user_id(token):
    if not token:
        return ''
    return ObjectId(jwt.decode(token, SECRET_KEY, algorithms='HS256')['id'])

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

# 페이징에 필요한 값 연산
def paging(events, currPage):
    cardsPerPage = 4 # const
    dispageNum = 4
    totalCards = len(events)

    totalPage = ((totalCards - 1) // cardsPerPage) + 1
    endPage = (((currPage-1) // dispageNum) + 1) * dispageNum
    if totalPage < endPage: endPage = totalPage
    startPage = ((currPage-1)//dispageNum)* dispageNum + 1
    prev = not startPage == 1
    next = not endPage == totalPage

    startCard = cardsPerPage * (currPage-1)
    cards = events[startCard:] if currPage == totalPage else events[startCard: startCard+cardsPerPage]
    return {
        'totalPage': totalPage,
        'startPage': startPage,
        'endPage': endPage,
        'prev': prev,
        'next': next,
        'cards': cards
    }
    
# 웹 크롤링 수행
def perform_web_crawling():
    print(f'success : {time.strftime("%H:%M:%S")}')

    # open api 요청
    url = f'http://apis.data.go.kr/6300000/eventDataService/eventDataListJson'
    api_key = r'HF37SOzpRH8DBXxqviNM%2FxjayRLamasAPu7bsT%2F6hu5cK6KT4hRkoQAUVFJOqRxnpjBW4MZMNa5XCMIWRMDnPg%3D%3D'
    api_key_decode = requests.utils.unquote(api_key)
    pageNo = 1
    numOfRows = 30
    endDt = datetime.datetime.now().strftime('%Y-%m-%d')
    print(endDt)
    res = requests.get(url, params={'serviceKey':api_key_decode, 'pageNo': pageNo, 'numOfRows': numOfRows})

    # 결과를 db에 저장
    events = res.json()['msgBody']
    for e in events:
        # 이미 존재하면 넘어간다
        if db.events.find_one({
            'title':e['title'],
            'beginDt':e['beginDt'],
            'endDt':e['endDt'],
            'placeName':e['placeCdNm']
        }): continue

        db.events.insert_one({
            'title':e['title'],
            'beginDt':e['beginDt'],
            'endDt':e['endDt'],
            'placeName':e['placeCdNm']
        })
        print(e['title'])

if __name__ == '__main__':
    # 웹 크롤링 스케쥴러 시작
    scheduler.add_job(perform_web_crawling, 'interval', minutes=60)
    scheduler.start()

    app.run('0.0.0.0', port=5000, debug=True)
