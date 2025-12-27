import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count

# Windows 환경을 위한 Python 경로 설정
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

def main():
    spark = SparkSession.builder \
        .appName("MyFirstSparkApp") \
        .config("spark.driver.memory","512m") \
        .config("spark.executor.memory","512m") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

# 데이터 생성: (group, name, age, height, birth, role)
    data = [
        ("IVE","장원영",21,173,"2004-08-31","보컬, 비주얼"),
        ("IVE","안유진",22,172,"2003-09-01","리더, 보컬"),
        ("IVE","이서",18,166,"2007-02-21","보컬, 비주얼"),

        ("BLACKPINK","제니",29,163,"1996-01-16","랩, 보컬"),
        ("BLACKPINK","리사",28,167,"1997-03-27","메인 댄서, 랩"),
        ("BLACKPINK","로제",28,168,"1997-02-11","메인 보컬"),
    ]

    columns = ["group","name","age","height","birth","role"]
    idol_df = spark.createDataFrame(data, columns)

    # 출력
    idol_df.show(truncate=False)

    # 그룹/이름/역할만 보기
    print("그룹/이름/역할만 보기")
    idol_df.select("group", "name", "role").show(truncate=False)

    # (1) 나이가 20 이하인 멤버
    print("(1) 나이가 20 이하인 멤버")
    idol_df.filter(col("age") <= 20).show(truncate=False)

    # (2) 나이가 20~22세 사이인 멤버
    print("(2) 나이가 20~22세 사이인 멤버")
    idol_df.filter((col("age") >= 20) & (col("age") <= 22)).show(truncate=False)

    # (3) SQL 스타일
    print("(3) SQL 스타일")
    idol_df.filter("age BETWEEN 20 AND 22").show(truncate=False)

    # (4) role에 '보컬' 포함한 멤버
    print("(4) role에 '보컬' 포함한 멤버")
    idol_df.filter(col("role").contains("보컬")).show(truncate=False)

    # (5) role에 '랩' 포함한 멤버 (SQL LIKE)
    print("(5) role에 '랩' 포함한 멤버 (SQL LIKE)")
    idol_df.filter("role LIKE '%랩%'").show(truncate=False)

    # (6) 특정 그룹만 보기
    print("(6) 특정 그룹만 보기")
    idol_df.filter(col("group") == "IVE").show(truncate=False)

    # (7) 그룹별 평균 나이 / 평균 키 / 멤버 수
    print("(7) 그룹별 평균 나이 / 평균 키 / 멤버 수")
    idol_df.groupBy("group") \
        .agg(
        avg("age").alias("avg_age"),
        avg("height").alias("avg_height"),
        count("*").alias("member_count")
    ).show(truncate=False)

    # (8) 키가 170 이상이면 'tall' 표시 컬럼 추가
    print("(8) 키가 170 이상이면 'tall' 표시 컬럼 추가")
    idol_df2 = idol_df.withColumn("is_tall", col("height") >= 170)
    idol_df2.select("group", "name", "height", "is_tall").show(truncate=False)

    # (9) 키가 큰 순서대로 정렬
    print("(9) 키가 큰 순서대로 정렬")
    idol_df.orderBy(col("height").desc()).show(truncate=False)

    print("임시 테이블로 SQL 실행")
    idol_df.createOrReplaceTempView("idol")

    spark.sql("""
              SELECT
              group, COUNT (*) AS cnt
              FROM idol
              GROUP BY
              group
              ORDER BY cnt DESC
              """).show(truncate=False)
if __name__ =="__main__":
    main()