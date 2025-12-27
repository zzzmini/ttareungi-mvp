import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# 1. 데이터 로드
# ============================================================
df = pd.read_csv('training_data_merged.csv')

# 타임스탬프를 datetime 형식으로 변환
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ============================================================
# 2. 기본 시간 피처 생성
# ============================================================

# 시간 (0-23)
df['hour'] = df['timestamp'].dt.hour

# 요일 (0=월요일, 6=일요일)
df['day_of_week'] = df['timestamp'].dt.dayofweek

# 주말 여부 (토요일=5, 일요일=6)
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

# 러시아워 여부 (출근: 7-9시, 퇴근: 17-19시)
df['is_rush_hour'] = ((df['hour'] >= 7) & (df['hour'] <= 9) |
                       (df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)

# ============================================================
# 3. 순환 인코딩 (Cyclic Encoding)
# ============================================================
# 시간은 연속적! (23시 → 0시로 연결)
# Sin/Cos 변환으로 순환성 표현

# 시간 순환 인코딩 (0-23시를 원형으로)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# 요일 순환 인코딩 (일요일-토요일을 원형으로)
df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

print("✅ 기본 피처 생성 완료")

# ============================================================
# 4. 시계열 피처 생성 (대여소별 그룹화)
# ============================================================

# 대여소별로 데이터 그룹화 (각 역의 시계열 패턴 추출)
grouped = df.groupby('station_id')

# Lag 피처 (과거 값)
df['parking_count_lag_1'] = grouped['parking_count'].shift(1)
df['parking_count_lag_2'] = grouped['parking_count'].shift(2)
df['parking_count_lag_3'] = grouped['parking_count'].shift(3)

# 이동 평균 (Moving Average) - transform 사용!
df['parking_count_ma_3'] = grouped['parking_count'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean()
)
df['parking_count_ma_6'] = grouped['parking_count'].transform(
    lambda x: x.rolling(window=6, min_periods=1).mean()
)

# 변화율 (Diff)
df['parking_count_diff_1'] = grouped['parking_count'].diff(1)
df['parking_count_diff_2'] = grouped['parking_count'].diff(2)

# shift/rolling으로 생긴 결측치 제거
df = df.dropna()

print("✅ 시계열 피처 생성 완료")
print(f"   레코드 수: {len(df)}")

# ============================================================
# 5. 타겟 변수 생성 (예측 목표)
# ============================================================

# 10분 후 예측
# 30초 간격 수집 → 10분 후 = 20회 후
# 하지만 코드에서는 2회 후 (1분 후)로 설정됨
# → 실제로는 5분 간격 수집인 것으로 추정
# 5분 간격 × 2 = 10분 후

# 2회 후의 parking_count를 예측 타겟으로 설정
df['target'] = grouped['parking_count'].shift(-2)

# shift(-2)로 생긴 결측치 제거 (마지막 2개 행)
df = df.dropna(subset=['target'])

print(f"✅ 타겟 변수 생성 완료")
print(f"   최종 레코드: {len(df)}")

# ============================================================
# 결과 확인
# ============================================================
print(f"\n📊 최종 데이터 정보:")
print(f"   전체 행: {len(df)}")
print(f"   전체 컬럼: {df.shape[1]}")
print(f"   피처 컬럼: {df.shape[1] - 1}개 (target 제외)")

# 입력 피처
feature_cols = [
    'parking_count',           # 현재 대수
    'hour',                    # 시간
    'day_of_week',             # 요일
    'is_weekend',              # 주말 여부
    'is_rush_hour',            # 출퇴근 시간
    'hour_sin', 'hour_cos',    # 시간 순환
    'dow_sin', 'dow_cos',      # 요일 순환
    'parking_count_lag_1',     # 1개 전
    'parking_count_lag_2',     # 2개 전
    'parking_count_lag_3',     # 3개 전
    'parking_count_ma_3',      # 3개 평균
    'parking_count_ma_6',      # 6개 평균
    'parking_count_diff_1',    # 변화량 1
]

# 타겟
target_col = 'target'

X = df[feature_cols]
y = df[target_col]

print(f"✅ 피처{len(feature_cols)}개")
print(f"✅ 샘플{len(X)}개")

from sklearn.model_selection import train_test_split

# 80% 학습, 20% 테스트
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

print(f"✅ 데이터 분리 완료")
print(f"   학습:{len(X_train)}")
print(f"   테스트:{len(X_test)}")

import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

# XGBoost 모델 생성
model = xgb.XGBRegressor(
    n_estimators=100,        # 트리 개수
    max_depth=5,             # 트리 깊이
    learning_rate=0.1,       # 학습률
    subsample=0.8,           # 샘플링 비율
    colsample_bytree=0.8,    # 피처 샘플링
    random_state=42
)

# 학습
print("🔄 모델 학습 중...")
model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    verbose=10
)

print("✅ 학습 완료!")

# 예측
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

# 평가 지표
train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

train_mae = mean_absolute_error(y_train, y_pred_train)
test_mae = mean_absolute_error(y_test, y_pred_test)

print("\n📊 모델 성능")
print(f"{'='*40}")
print(f"Train RMSE:{train_rmse:.2f}")
print(f"Test RMSE:{test_rmse:.2f}")
print(f"Train MAE:{train_mae:.2f}")
print(f"Test MAE:{test_mae:.2f}")
print(f"{'='*40}")

# 간단한 예측 (0.85) 비교
simple_pred = X_test['parking_count'] * 0.85
simple_mae = mean_absolute_error(y_test, simple_pred)

print(f"\n📈 예측 비교")
print(f"{'='*40}")
print(f"XGBoost MAE:{test_mae:.2f}")
print(f"Simple MAE:{simple_mae:.2f}")
print(f"개선율:{((simple_mae - test_mae) / simple_mae * 100):.1f}%")
print(f"{'='*40}")

import matplotlib.pyplot as plt

# 피처 중요도
importance = model.feature_importances_
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importance
}).sort_values('importance', ascending=False)

print("\n🎯 피처 중요도 Top 5")
print(feature_importance.head())

# 시각화
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'][:10],
         feature_importance['importance'][:10])
plt.xlabel('Importance')
plt.title('Top 10 Feature Importance')
plt.tight_layout()
plt.savefig('feature_importance.png')
print("✅ 저장: feature_importance.png")

import pickle

# 모델 저장
with open('models/xgboost_model.pkl', 'wb') as f:
    pickle.dump(model, f)

# 피처 목록도 저장
with open('models/feature_cols.pkl', 'wb') as f:
    pickle.dump(feature_cols, f)

print("✅ 모델 저장 완료")
print("   - xgboost_model.pkl")
print("   - feature_cols.pkl")