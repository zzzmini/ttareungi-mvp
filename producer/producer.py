import os
import time
import json
import requests
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from datetime import datetime

# 환경 변수 (Docker에서 자동으로 읽음)
SEOUL_API_KEY = os.getenv('SEOUL_API_KEY')
KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')  # ← Docker 내부 주소
INTERVAL = int(os.getenv('INTERVAL_SECONDS', 30))


def create_producer():
    """Kafka Producer 생성 (재시도 포함)"""
    max_retries = 10

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[PRODUCER] Kafka 연결 시도 ({attempt}/{max_retries}) - {KAFKA_SERVERS}")
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                acks='all',
                retries=3
            )
            print(f"[PRODUCER] ✅ Kafka 연결 성공!")
            return producer
        except NoBrokersAvailable:
            if attempt < max_retries:
                print(f"[PRODUCER] ❌ 연결 실패, 3초 후 재시도...")
                time.sleep(3)
            else:
                print(f"[PRODUCER] ❌ Kafka 연결 실패 - 종료")
                raise


def fetch_station_data():
    """따릉이 API 호출 (역 주변만 필터링)"""
    if not SEOUL_API_KEY:
        print("[ERROR] SEOUL_API_KEY가 설정되지 않았습니다!")
        return []

    url = f'http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/bikeList/1/1000/'

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'rentBikeStatus' not in data or 'row' not in data['rentBikeStatus']:
            print(f"[ERROR] 예상치 못한 API 응답")
            return []

        # 역 주변만 필터링
        stations = [
            {
                'station_id': s['stationId'],
                'station_name': s['stationName'],
                'parking_count': int(s['parkingBikeTotCnt']),
                'rack_total': int(s['rackTotCnt']),
                'timestamp': datetime.now().isoformat()
            }
            for s in data['rentBikeStatus']['row']
            if '역' in s['stationName']
        ]

        return stations

    except Exception as e:
        print(f"[ERROR] API 호출 실패: {e}")
        return []


def main():
    print("=" * 60)
    print("[PRODUCER] 따릉이 실시간 데이터 수집 (지하철역 주변)")
    print("=" * 60)
    print(f"📡 Kafka: {KAFKA_SERVERS}")
    print(f"⏱️  주기: {INTERVAL}초")
    print(f"🔑 API Key: {'✅ 설정됨' if SEOUL_API_KEY else '❌ 없음'}")
    print(f"🎯 필터: 지하철역 주변 대여소")
    print("=" * 60)

    if not SEOUL_API_KEY:
        print("[ERROR] 환경 변수 SEOUL_API_KEY를 설정하세요!")
        return

    # Kafka 준비 대기
    print("[PRODUCER] Kafka 준비 대기 중...")
    time.sleep(10)

    try:
        producer = create_producer()
    except Exception as e:
        print(f"[ERROR] Producer 초기화 실패: {e}")
        return

    count = 0

    try:
        while True:
            count += 1
            print(f"\n[{count}회차] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            stations = fetch_station_data()

            if stations:
                for station in stations:
                    # JSON으로 변환 후 UTF-8 인코딩
                    value = json.dumps(station, ensure_ascii=False).encode('utf-8')
                    producer.send('ttareungi-realtime', value=value)

                producer.flush()
                print(f"  ✅ {len(stations)}개 역 주변 대여소 전송 완료")
            else:
                print(f"  ⚠️  수집된 데이터 없음")

            print(f"  ⏳ {INTERVAL}초 대기...")
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 종료 (Ctrl+C)")
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {e}")
    finally:
        producer.close()
        print("👋 Producer 종료\n")


if __name__ == "__main__":
    main()