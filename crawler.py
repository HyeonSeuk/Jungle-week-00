import datetime
import time
import requests

from pymongo import MongoClient

client = MongoClient('localhost',27017)
db = client.dbjungle
event_db = db['events']

url = f'http://apis.data.go.kr/6300000/eventDataService/eventDataListJson'
api_key = r'HF37SOzpRH8DBXxqviNM%2FxjayRLamasAPu7bsT%2F6hu5cK6KT4hRkoQAUVFJOqRxnpjBW4MZMNa5XCMIWRMDnPg%3D%3D'
api_key_decode = requests.utils.unquote(api_key)
numOfRows = 10
max_page = 45


# 같은 내용의 데이터가 있는지 판단
# 공연명, 시작일자, 종료일자, 장소명
def find_same_contents(new):
    return event_db.find_one({
        'title': new['title'],
        'beginDt': new['beginDt'],
        'endDt': new['endDt'],
        'placeName': new['placeCdNm']
    })


def insert_api_record(e):
    event_db.insert_one({
        'eventSeq': e['eventSeq'],
        'title': e['title'],
        'beginDt': e['beginDt'],
        'endDt': e['endDt'],
        'placeName': e['placeCdNm'],
        'dataStnDt': e['dataStnDt']
    })


def insert_if_validate_data(new) -> None:
    # 같은 일련번호 있는지 검증
    same_seq = event_db.find_one({
        'eventSeq': new['eventSeq']
    })

    # case1: 일련번호가 같다
    if same_seq:
        if find_same_contents(new):
            return

        # 새로 들어올 내용의 기준일자가 더 빠르므로 스킵
        if same_seq['dataStnDt'] >= new['dataStnDt']:
            return

        # 일련번호는 같지만 내용이 다르므로 최신 내용을 기록한다.
        event_db.delete_one({'eventSeq': same_seq['eventSeq']})
        insert_api_record(new)
        print("{}: {}".format(new['eventSeq', new['title']]))
        return

    # case2: 일련번호가 다르다
    if find_same_contents(new):
        # 기존에 저장된 데이터의 기준일이 더 최신이라면 기존데이터 유지
        if same_seq['dateStnDt'] >= new['dateStnDt']:
            return

        # 내용이 같지만 새로 받은 데이터의 기준일이 더 최신이므로 갱신
        event_db.delete_one(find_same_contents(new))
        insert_api_record(new)
        print("{}: {}".format(new['eventSeq', new['title']]))

# 웹 크롤링 수행
def perform_web_crawling():
    # open api 요청
    for pageNo in range(1, max_page):
        res = requests.get(url, params={'serviceKey':api_key_decode, 'pageNo': pageNo, 'numOfRows': numOfRows})
        events = res.json()['msgBody']
        # 각 event의 데이터 검증
        for e in events:
            insert_if_validate_data(e)


def insert_all_api_data():
    for pageNo in range(1, max_page):
        res = requests.get(url, params={'serviceKey':api_key_decode, 'pageNo': pageNo, 'numOfRows': numOfRows})
        events = res.json()['msgBody']

        for i, e in enumerate(events):
            insert_api_record(e)
            print('{}: {}'.format(i + pageNo*10, e['title']))


if __name__ == '__main__':
    perform_web_crawling()
    #insert_all_api_data()