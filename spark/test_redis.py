import redis
import json

# Redis 연결
redis_client = redis.Redis(
    host='redis',
    port=6379,
    decode_responses=True  # 문자열로 자동 변환
)

# 연결 확인
redis_client.ping()  # True 반환

# 데이터 저장 (String)
redis_client.set('station:ST-120:current', '{"bikes": 15}')

# 데이터 조회
data = redis_client.get('station:ST-120:current')
print(data)  # {"bikes": 15}

# JSON 파싱
station_data = json.loads(data)
print(station_data['bikes'])  # 15

# 여러 키 조회
keys = redis_client.keys('station:*')
print(keys)  # ['station:ST-120:current', ...]