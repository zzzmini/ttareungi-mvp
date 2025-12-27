import os
import json
import redis
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 환경 변수
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Redis 클라이언트
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# FastAPI 앱
app = FastAPI(
    title="따릉이 실시간 API",
    description="서울시 따릉이 대여소 실시간 현황 및 예측 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """서버 상태 확인"""
    try:
        redis_client.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": "disconnected", "error": str(e)}

@app.get("/api/v1/stations")
def get_all_stations() -> Dict[str, Any]:
    """전체 대여소 목록 조회"""
    try:
        keys = redis_client.keys("station:*:current")
        stations = []

        for key in keys:
            station_id = key.split(':')[1]
            current_data = redis_client.get(f"station:{station_id}:current")
            prediction_data = redis_client.get(f"station:{station_id}:prediction")

            if current_data and prediction_data:
                current = json.loads(current_data)
                prediction = json.loads(prediction_data)

                stations.append({
                    "station_id": station_id,
                    "station_name": current.get("station_name"),
                    "current": {
                        "parking_count": current.get("parking_count"),
                        "timestamp": current.get("timestamp")
                    },
                    "prediction": {
                        "predicted_count": prediction.get("predicted_count"),
                        "timestamp": prediction.get("timestamp")
                    }
                })

        return {"total": len(stations), "stations": stations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stations/{station_id}")
def get_station(station_id: str) -> Dict[str, Any]:
    """특정 대여소 상세 정보"""
    try:
        current_data = redis_client.get(f"station:{station_id}:current")
        prediction_data = redis_client.get(f"station:{station_id}:prediction")

        if not current_data or not prediction_data:
            raise HTTPException(status_code=404, detail=f"Station{station_id} not found")

        current = json.loads(current_data)
        prediction = json.loads(prediction_data)
        change = prediction.get("predicted_count") - current.get("parking_count")

        return {
            "station_id": station_id,
            "station_name": current.get("station_name"),
            "current": {
                "parking_count": current.get("parking_count"),
                "timestamp": current.get("timestamp")
            },
            "prediction": {
                "predicted_count": prediction.get("predicted_count"),
                "timestamp": prediction.get("timestamp"),
                "change": change
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
def get_stats() -> Dict[str, Any]:
    """전체 통계"""
    try:
        keys = redis_client.keys("station:*:current")
        total_stations = len(keys)
        total_bikes = 0
        low_stock_count = 0

        for key in keys:
            station_id = key.split(':')[1]
            current_data = redis_client.get(f"station:{station_id}:current")

            if current_data:
                current = json.loads(current_data)
                bikes = current.get("parking_count", 0)
                total_bikes += bikes
                if bikes < 5:
                    low_stock_count += 1

        avg_bikes = total_bikes / total_stations if total_stations > 0 else 0

        return {
            "total_stations": total_stations,
            "total_bikes": total_bikes,
            "average_bikes": round(avg_bikes, 1),
            "low_stock_count": low_stock_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))