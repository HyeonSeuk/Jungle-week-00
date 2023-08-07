import requests, json
from pymongo import MongoClient

client = MongoClient('mongodb://test:test@localhost',27017)
db = client.dbjungle

url = f'http://apis.data.go.kr/6300000/eventDataService/eventDataListJson?serviceKey=HF37SOzpRH8DBXxqviNM%2FxjayRLamasAPu7bsT%2F6hu5cK6KT4hRkoQAUVFJOqRxnpjBW4MZMNa5XCMIWRMDnPg%3D%3D'
res = requests.get(url)

json_object = json.loads(res.content)
events = json_object.get('msgBody')

for e in events:
    db.user.insert_one({'title':e['title'], 'beginDt':e['beginDt'], 'endDt':e['endDt'], 'placeName':e['placeCdNm'], 'fav_count':0})


