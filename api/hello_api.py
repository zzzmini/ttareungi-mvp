from fastapi import FastAPI

# FastAPI 앱 생성
app = FastAPI(
    title="따릉이 API",
    description="실시간 따릉이 대여소 현황 API",
    version="1.0.0"
)

# 기본 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Hello, Ttareungi!"}

# Health Check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 실행 (터미널에서)
# uvicorn main:app --reload