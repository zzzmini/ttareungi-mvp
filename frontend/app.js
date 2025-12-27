// API 기본 URL
const API_BASE = '/api/v1';

// 전역 변수
let allStations = [];
let updateInterval;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    loadStations();
    loadStats();

    // 5초마다 자동 새로고침
    updateInterval = setInterval(() => {
        loadStations();
        loadStats();
    }, 5000);

    // 검색 기능
    document.getElementById('search').addEventListener('input', (e) => {
        filterStations(e.target.value);
    });

    // 새로고침 버튼
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadStations();
        loadStats();
    });
});

// 대여소 목록 로드
async function loadStations() {
    try {
        const response = await fetch(`${API_BASE}/stations`);
        const data = await response.json();

        allStations = data.stations;
        displayStations(allStations);
        updateLastUpdate();

        // 로딩 숨기기
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'none';
    } catch (error) {
        console.error('Error loading stations:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
    }
}

// 통계 로드
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        document.getElementById('total-stations').textContent = data.total_stations;
        document.getElementById('total-bikes').textContent = data.total_bikes;
        document.getElementById('avg-bikes').textContent = data.average_bikes;
        document.getElementById('low-stock').textContent = data.low_stock_count;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// 대여소 표시
function displayStations(stations) {
    const grid = document.getElementById('stations-grid');

    grid.innerHTML = stations.map(station => {
        const current = station.current.parking_count;
        const predicted = station.prediction.predicted_count;
        const model = station.prediction.model || 'simple';  // 모델 정보
        const change = predicted - current;
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeSymbol = change >= 0 ? '▲' : '▼';

        return `
            <div class="station-card">
                <div class="station-name">${station.station_name}</div>

                <div class="bike-info">
                    <div class="info-box">
                        <span class="info-label">현재</span>
                        <span class="info-value">${current}대</span>
                    </div>
                    <div class="info-box">
                        <span class="info-label">10분 후 예측</span>
                        <span class="info-value">${predicted}대</span>
                    </div>
                </div>

                <div class="change${changeClass}">
${changeSymbol}${Math.abs(change)}대${change >= 0 ? '증가' : '감소'} 예상
                </div>

                <div class="model-badge${model}">
${model === 'xgboost' ? '🤖 ML 예측' : '📐 규칙 예측'}
                </div>

                <div class="timestamp">
${formatTime(station.current.timestamp)}
                </div>
            </div>
        `;
    }).join('');
}

// 검색 필터
function filterStations(searchText) {
    const filtered = allStations.filter(station =>
        station.station_name.toLowerCase().includes(searchText.toLowerCase())
    );
    displayStations(filtered);
}

// 시간 포맷
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('ko-KR', {
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 마지막 업데이트 시간
function updateLastUpdate() {
    const now = new Date();
    document.getElementById('last-update').textContent =
        `마지막 업데이트:${formatTime(now.toISOString())}`;
}