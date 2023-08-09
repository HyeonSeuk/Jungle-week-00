from pymongo import MongoClient
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash, make_response, Response
from flask_bcrypt import Bcrypt
import requests, jwt, datetime, os, time, re
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
import crawler, json

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

# 회원가입 페이지/API
# form 입력(nickname, email, pwd, pwd2를 전달받는다.)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  # 사용자가 회원가입 페이지에 접근할 경우
  if request.method == 'GET':
      if is_logged_in(request):
        # 이미 로그인된 사용자는 리디렉션
        return redirect(url_for('home'))
      return render_template('signup.html')

  if request.method == 'POST':

    nickname = request.form['nickname']
    email = request.form['email']
    password = request.form['password']
    password2 = request.form['password2']

    # 닉네임 길이 검증
    if len(nickname) < 4 or len(nickname) > 10:
      return jsonify({'result': 'fail', 'input': 'nickname', 'msg': '닉네임은 4~10자 입니다'}) 
    
    # 이메일 빈칸 검증
    if not email:
      return jsonify({'result': 'fail', 'input': 'email', 'msg': '이메일을 입력하세요'})
    
    # 이메일 형식 검증 TODO 중복코드 -> 함수
    email_re = re.compile('[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]$')
    if not email_re.match(email):
      return jsonify({'result': 'fail', 'input': 'email', 'msg': '이메일 형식으로 입력하세요'})
    
    # 이메일 중복 검증
    result = db.users.find_one({'email':email})
    if result:
      return jsonify({'result':'fail','input': 'email','msg':'등록된 이메일이 이미 존재합니다. 로그인하세요'})
    
    # 비밀번호 길이 검증
    if len(password) < 10 or len(password) > 20:
       return jsonify({'result': 'fail', 'input': 'password','msg': '비밀번호는 10~20자리 입니다'})
    
    # 비밀번호 확인 일치여부 검증
    if password != password2:
       return jsonify({'result': 'fail', 'input': 'password2','msg': '비밀번호 확인이 불일치합니다'})
    
    # 성공 시나리오: password를 암호화하여 db에 저장합니다.
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    db.users.insert_one({'nickname':nickname, 'email':email, 'password':password_hash})
    return jsonify({'result': 'success', 'msg': '회원가입에 성공했습니다.'})

# 로그인 페이지/API
@app.route('/login', methods=['GET', 'POST'])
def login():
  # 사용자가 로그인 페이지에 접속할 경우
  if request.method == 'GET':
    if is_logged_in(request):
       # 이미 로그인된 사용자는 리디렉션
       return redirect(url_for('home'))
    msg = request.args.get('msg', None)
    if msg: flash(msg)
    return render_template('login.html')
  
  # 사용자가 로그인을 요청할 경우
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    # 아이디/비밀번호가 없음
    if not email or not password:
        return jsonify({'result': 'fail', 'msg': '이메일/비밀번호를 모두 입력하세요'})
        
    # 이메일 형식인지 확인
    email_re = re.compile('[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]$')
    if not email_re.match(email):
        return jsonify({'result': 'fail', 'msg': '이메일 형식으로 입력하세요'})
    
    # 비밀번호 길이 확인
    if len(password) < 10:
        return jsonify({'result': 'fail', 'msg': '비밀번호는 10자 이상입니다'})

    # 일치하는 계정 없음
    result = db.users.find_one({'email': email})
    if not result:        
        return jsonify({'result': "fail", "msg": "계정이 존재하지 않습니다."})

    # 비밀번호가 일치하지 않음
    chk_pwd = bcrypt.check_password_hash(result['password'], password)
    if not chk_pwd:
        return jsonify({'result': "fail", "msg": "이메일/비밀번호가 일치하지 않습니다."})
    
    # 로그인 성공, 토큰 발행, string 인코딩  
    payload = {'id': str(result['_id'])}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

    # 리디렉션 주소, 토큰 반환
    return jsonify({'result': 'success', 'token': token, 'redirect': url_for('home')})

# 로그아웃 API
@app.route('/logout')
def logout():
    if not is_logged_in(request):
      return '로그아웃할 수 없음'
    response = make_response(redirect(url_for('home')))
    response.set_cookie('token', '', expires=-1)
    return response

@app.route('/crawler', methods=["POST", "GET"])
def test_crawler():
    dummy = [
          {'case': 1, 'eventSeq': '001', 'title': '0주차 프로젝트', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-08-01 00:00:00", 'result': '새로운 데이터 삽입'},
          {'case': 2, 'eventSeq': '001', 'title': '0주차 프로젝트', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-08-01 00:00:00", 'result': '중복된 데이터 스킵'},
          {'case': 3, 'eventSeq': '001', 'title': '입학테스트 공부', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-07-01 00:00:00", 'result': '이전 데이터 스킵'},
          {'case': 4, 'eventSeq': '001', 'title': '1주차 알고리즘', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-08-10 00:00:00", 'result': '최근 데이터로 업데이트'},
          {'case': 5, 'eventSeq': '002', 'title': '1주차 알고리즘', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-08-11 00:00:00", 'result': '최근 데이터로 업데이트'},
          {'case': 6, 'eventSeq': '002', 'title': '입학테스트 공부', 'beginDt': '2023-08-07', 'endDt': '2023-08-10', 'placeCdNm': '카이스트 문지캠퍼스', 'beginTm': '1200', 'endTm': '1300', "dataStnDt": "2023-08-10 00:00:00", 'result': '이전 데이터 스킵'},
      ]
    if request.method == "GET":
      db.events.delete_one({'eventSeq': '001'})
      db.events.delete_one({'eventSeq': '002'})
      return render_template('crawler.html', dummy=dummy)
    if request.method == "POST":
        test_case = int(request.form['case'])
        crawler.insert_if_validate_data(dummy[test_case-1])
        all_events = json.dumps(get_all_events(None))
        return Response(all_events, mimetype="application/json", status=200)

# get user id from token
def get_user_id(token):
    if not token:
        return ''
    return ObjectId(jwt.decode(token, SECRET_KEY, algorithms='HS256')['id'])

# 좋아요
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

# 유틸: 토큰 -> 사용자 아이디
def get_user_id(token):
    if not token:
        return ''
    return ObjectId(jwt.decode(token, SECRET_KEY, algorithms='HS256')['id'])

# 유틸: 사용자 로그인 여부
def is_logged_in(request):
    token = request.cookies.get('token', None)
    return get_user_id(token)

# 유틸: 데이터 가공 함수
def get_all_events(user):
    events = list(db.events.find({}))
    for event in events:
        event["_id"] = str(event['_id'])
        event['fav_count'] = len(list(db.userevent.find({'event_id': str(event['_id'])})))
        event['is_mine'] = False
        if(user):
            event['is_mine'] = len(list(db.userevent.find({'user_id': user, 'event_id': str(event['_id'])}))) > 0
    return events

# 유틸: 좋아요한 데이터만
def get_fav_events(user):
    events = get_all_events(user)
    all_favs = []
    for event in events:
        if(event['is_mine']): all_favs.append(event)
    return all_favs

# 유틸: 페이징에 필요한 값 연산
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

    # 결과 db에 저장
    events = res.json()['msgBody']
    for e in events:
        # 이미 존재하면 넘어간다
        if db.events.find_one({
            'title':e['title'],
            'beginDt':e['beginDt'],
            'endDt':e['endDt'],
            'placeName':e['placeCdNm']
        }):
            continue

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
