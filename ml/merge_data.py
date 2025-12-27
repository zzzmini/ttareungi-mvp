import pandas as pd
import glob

# 모든 CSV 파일 읽기
csv_files = glob.glob('data/snapshot_*.csv')

# 병합
dfs = [pd.read_csv(f) for f in csv_files]
df = pd.concat(dfs, ignore_index=True)

# 중복 제거 (같은 station_id + timestamp)
df = df.drop_duplicates(subset=['station_id', 'timestamp'])

# 정렬
df = df.sort_values(['station_id', 'timestamp'])

# 저장
df.to_csv('training_data_merged.csv', index=False)

print(f"✅ 병합 완료:{len(df)}개 레코드")