FROM python:3.11-slim

WORKDIR /app

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY producer.py .

# unbuffered 모드로 실행 (로그 즉시 출력)
CMD ["python", "-u", "producer.py"]