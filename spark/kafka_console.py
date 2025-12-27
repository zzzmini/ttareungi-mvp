from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql import SparkSession
# 따릉이 데이터 스키마
schema = StructType([
    StructField("station_id", StringType(), True),
    StructField("station_name", StringType(), True),
    StructField("parking_count", IntegerType(), True),
    StructField("timestamp", StringType(), True)
])

# SparkSession 생성
spark = SparkSession.builder \
    .appName("KafkaSparkIntegration") \
    .config("spark.driver.memory", "512m") \
    .config("spark.executor.extraJavaOptions", "-Dfile.encoding=UTF-8") \
    .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Kafka 스트림 읽기
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "ttareungi-realtime") \
    .option("startingOffsets", "latest") \
    .load()

print("✅ Kafka 연결 완료!")

from pyspark.sql.functions import from_json, col

# value를 String으로 변환 후 JSON 파싱
parsed_df = df.select(
    from_json(
        col("value").cast("string"),  # binary → string 변환
        schema                          # 스키마 적용
    ).alias("data")
).select("data.*")  # data 안의 모든 컬럼 추출

# 결과 확인
parsed_df.printSchema()

# 출력:
# root
#  |-- station_id: string (nullable = true)
#  |-- station_name: string (nullable = true)
#  |-- parking_count: integer (nullable = true)
#  |-- timestamp: string (nullable = true)

# 5. Console로 출력
query = parsed_df \
    .writeStream \
    .format("console") \
    .outputMode("append") \
    .option("truncate", False) \
    .start()

print("✅ Streaming 시작! Ctrl+C로 종료")

# 기존 parsed_df에서 필터링
low_bikes_df = parsed_df.filter(col("parking_count") < 10)

# Console 출력
query = low_bikes_df \
    .writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

# 예측값 추가 (현재 * 0.85)
df_with_prediction = parsed_df.withColumn(
    "predicted_count",
    (col("parking_count") * 0.85).cast("int")
)

# 필요한 컬럼만 선택
result_df = df_with_prediction.select(
    "station_id",
    "station_name",
    "parking_count",
    "predicted_count"
)

# Console 출력
query = result_df \
    .writeStream \
    .format("console") \
    .outputMode("append") \
    .start()
# 종료될 때까지 대기
query.awaitTermination()