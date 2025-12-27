import os
import json
import redis
import pickle
import numpy as np
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# 환경 변수
KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'ttareungi-realtime')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Redis 클라이언트
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# ML 모델 로드
with open('/models/xgboost_model.pkl', 'rb') as f:
    ml_model = pickle.load(f)

with open('/models/feature_cols.pkl', 'rb') as f:
    feature_cols = pickle.load(f)

print("✅ ML 모델 로드 완료")

def get_lag_value(station_id, lag):
    """과거 값 조회"""
    key = f"station:{station_id}:history:{lag}"
    value = redis_client.get(key)
    return int(value) if value else 0

def save_history(station_id, current_count):
    """현재 값을 히스토리로 저장"""
    # 이전 값들을 shift
    for i in range(5, 0, -1):
        old_key = f"station:{station_id}:history:{i}"
        new_key = f"station:{station_id}:history:{i+1}"
        value = redis_client.get(old_key)
        if value:
            redis_client.set(new_key, value)

    # 현재 값 저장
    redis_client.set(f"station:{station_id}:history:1", current_count)

def create_features(station_id, current_count, timestamp):
    """피처 생성"""
    dt = datetime.fromisoformat(timestamp)

    hour = dt.hour
    day_of_week = dt.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    is_rush_hour = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    dow_sin = np.sin(2 * np.pi * day_of_week / 7)
    dow_cos = np.cos(2 * np.pi * day_of_week / 7)

    lag_1 = get_lag_value(station_id, 1)
    lag_2 = get_lag_value(station_id, 2)
    lag_3 = get_lag_value(station_id, 3)

    ma_3 = (current_count + lag_1 + lag_2) / 3
    ma_6 = (current_count + lag_1 + lag_2 + lag_3 +
            get_lag_value(station_id, 4) + get_lag_value(station_id, 5)) / 6

    diff_1 = current_count - lag_1

    return [
        current_count, hour, day_of_week, is_weekend, is_rush_hour,
        hour_sin, hour_cos, dow_sin, dow_cos,
        lag_1, lag_2, lag_3, ma_3, ma_6, diff_1
    ]

def predict_with_ml(station_id, current_count, timestamp):
    """ML 예측"""
    try:
        features = create_features(station_id, current_count, timestamp)
        features_array = np.array(features).reshape(1, -1)
        predicted = ml_model.predict(features_array)[0]
        return max(0, int(predicted))
    except Exception as e:
        print(f"[ML 예측 실패]{e}")
        return int(current_count * 0.85)

def save_to_redis(batch_df, batch_id):
    """Redis 저장"""
    if batch_df.isEmpty():
        return

    rows = batch_df.collect()

    for row in rows:
        station_id = row['station_id']
        current_count = row['parking_count']
        timestamp = row['timestamp']

        # ML 예측
        predicted_count = predict_with_ml(station_id, current_count, timestamp)

        # 현재 상태
        current_data = {
            'station_id': station_id,
            'station_name': row['station_name'],
            'parking_count': current_count,
            'timestamp': timestamp
        }
        redis_client.set(
            f'station:{station_id}:current',
            json.dumps(current_data)
        )

        # ML 예측값
        prediction_data = {
            'station_id': station_id,
            'predicted_count': predicted_count,
            'model': 'xgboost',
            'timestamp': timestamp
        }
        redis_client.set(
            f'station:{station_id}:prediction',
            json.dumps(prediction_data)
        )

        # 히스토리 저장
        save_history(station_id, current_count)

    print(f"[BATCH{batch_id}] ✅{len(rows)}개 저장 (ML 예측)")

def main():
    print("[CONSUMER] ML 모드 시작")

    spark = SparkSession.builder \
        .appName("TtareungiML") \
        .config("spark.driver.memory", "512m") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("parking_count", IntegerType(), True),
        StructField("timestamp", StringType(), True)
    ])

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    cleaned_df = parsed_df.filter(
        (col("station_id").isNotNull()) &
        (col("parking_count").isNotNull()) &
        (col("parking_count") >= 0)
    )

    query = cleaned_df \
        .writeStream \
        .foreachBatch(save_to_redis) \
        .outputMode("append") \
        .trigger(processingTime='30 seconds') \
        .start()

    print("✅ ML Streaming 시작!")
    query.awaitTermination()

if __name__ == "__main__":
    main()