import redis
import json
import csv
from datetime import datetime
import time

# Redis 연결
redis_client = redis.Redis(
    host='redis',
    port=6379,
    decode_responses=True
)

def collect_historical_data(output_file='training_data.csv'):
    """Redis에서 과거 데이터 수집"""

    print("📊 데이터 수집 시작...")

    # CSV 파일 생성
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            'station_id',
            'timestamp',
            'parking_count',
            'hour',
            'day_of_week',
            'is_weekend'
        ])

        # 모든 station 키 조회
        keys = redis_client.keys('station:*:current')

        for key in keys:
            station_id = key.split(':')[1]
            current_data = redis_client.get(key)

            if current_data:
                data = json.loads(current_data)

                # 타임스탬프 파싱
                timestamp = datetime.fromisoformat(data['timestamp'])
                hour = timestamp.hour
                day_of_week = timestamp.weekday()  # 0=월, 6=일
                is_weekend = 1 if day_of_week >= 5 else 0

                writer.writerow([
                    station_id,
                    data['timestamp'],
                    data['parking_count'],
                    hour,
                    day_of_week,
                    is_weekend
                ])

        print(f"✅ 데이터 수집 완료:{output_file}")
        print(f"   총{len(keys)}개 대여소")

if __name__ == "__main__":
    # 실시간 수집 (1시간 동안 5분마다)
    print("🔄 1시간 동안 데이터 수집 시작...")

    for i in range(12):  # 12번 = 1시간
        collect_historical_data(f'data/snapshot_{i}.csv')
        print(f"{i+1}/12 완료")
        if i < 11:
            time.sleep(30)  # 5분 대기

    print("✅ 전체 데이터 수집 완료!")