"""
Day 2: Spark 기본 문법 연습
- SparkSession 생성
- DataFrame 기본 조작
- 간단한 집계 연산
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, avg, count

# Windows 환경을 위한 Python 경로 설정
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

def main():
    # SparkSession 생성
    print("🚀 Spark 시작 중...")
    spark = SparkSession.builder \
        .appName("Day2-BasicSpark") \
        .master("local[*]") \
        .config("spark.driver.memory", "512m") \
        .config("spark.executor.memory", "512m") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print("✅ Spark 시작 완료!")
    print(f"🔹 Spark Version: {spark.version}")
    print(f"🔹 Master URL: {spark.sparkContext.master}\n")

    # 샘플 데이터 생성 (따릉이 스타일)
    print("📊 샘플 데이터 생성 중...")
    data = [
        ("강남역", 20, 15, "2024-12-25 10:00:00"),
        ("강남역", 20, 12, "2024-12-25 11:00:00"),
        ("강남역", 20, 8, "2024-12-25 12:00:00"),
        ("서울역", 15, 10, "2024-12-25 10:00:00"),
        ("서울역", 15, 7, "2024-12-25 11:00:00"),
        ("홍대입구", 25, 20, "2024-12-25 10:00:00"),
        ("홍대입구", 25, 18, "2024-12-25 11:00:00"),
    ]

    columns = ["stationName", "rackTotCnt", "parkingBikeTotCnt", "timestamp"]
    df = spark.createDataFrame(data, columns)

    print("\n📋 원본 데이터:")
    df.show(truncate=False)

    # 기본 집계
    print("\n📈 정거장별 평균 자전거 수:")
    df.groupBy("stationName") \
        .agg(
            avg("parkingBikeTotCnt").alias("평균_자전거"),
            sum("parkingBikeTotCnt").alias("총_자전거"),
            count("*").alias("측정_횟수")
        ) \
        .show(truncate=False)

    # 이용률 계산
    print("\n📊 정거장별 평균 이용률:")
    df.withColumn("usage_rate",
                  (col("parkingBikeTotCnt") / col("rackTotCnt") * 100)) \
        .groupBy("stationName") \
        .agg(
            avg("usage_rate").alias("평균_이용률_%")
        ) \
        .orderBy(col("평균_이용률_%").desc()) \
        .show(truncate=False)

    print("\n✅ 테스트 완료!")
    spark.stop()

if __name__ == "__main__":
    main()