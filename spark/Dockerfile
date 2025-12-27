FROM public.ecr.aws/bitnami/spark:3.5.1

USER root

# ML 패키지 추가
RUN pip install --no-cache-dir redis numpy scikit-learn xgboost

WORKDIR /app

COPY consumer.py /app/consumer.py

USER 1001

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1", "/app/consumer.py"]