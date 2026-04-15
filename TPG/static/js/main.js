let myChart = null;
let countdownInterval = null;

const UPDATE_INTERVAL = 10000; // 10초마다 서버 동기화

function initChart() {
    const ctx = document.getElementById('pressureChart').getContext('2d');
    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: '진공도 (Mbar)',
                data: [],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                fill: true,
                stepped: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute',
                        displayFormats: { minute: 'HH:mm' }
                    },
                    title: { display: true, text: '시간' }
                },
                y: {
                    type: 'logarithmic',
                    title: { display: true, text: 'Pressure' }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toExponential(3) + ' Mbar';
                        }
                    }
                }
            }
        }
    });
}

function updateCurrentValue() {
    fetch('/api/data/current')
        .then(res => res.json())
        .then(data => {
            // latest_pressure(실시간) 우선, 없으면 DB값 사용
            const val = (data.latest_pressure && data.latest_pressure !== 0)
                ? data.latest_pressure
                : data.pressure;

            if (val && val !== 0) {
                document.getElementById('pressure-val').textContent = Number(val).toExponential(3);
                document.getElementById('last-update').textContent = data.timestamp;
            }

            if (data.seconds_until_next !== undefined) {
                updateCountdown(data.seconds_until_next);
            }
        })
        .catch(err => console.error("현재 값 가져오기 실패:", err));
}

function updateCountdown(seconds) {
    if (countdownInterval) clearInterval(countdownInterval);
    let rem = Math.max(0, Math.round(seconds));

    const updateText = () => {
        const m = Math.floor(rem / 60);
        const s = rem % 60;
        document.getElementById('countdown').textContent = `${m}분 ${s}초`;
        if (rem > 0) rem -= 1;
    };

    updateText();
    countdownInterval = setInterval(updateText, 1000);
}

function queryHistory() {
    const startDate = document.getElementById('start-date').value;
    const startTime = document.getElementById('start-time').value;
    const endDate = document.getElementById('end-date').value;
    const endTime = document.getElementById('end-time').value;

    if (!startDate || !endDate) {
        alert("시작일과 종료일을 선택해주세요.");
        return;
    }

    const startStr = `${startDate} ${startTime}:00`;
    const endStr = `${endDate} ${endTime}:59`;

    fetch('/api/data/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start: startStr, end: endStr })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) { alert(data.error); return; }
        const chartData = data.map(row => ({
            x: new Date(row.timestamp),
            y: row.pressure
        }));
        myChart.data.datasets[0].data = chartData;
        myChart.update();
    })
    .catch(err => console.error("히스토리 데이터 조회 실패:", err));
}

function exportExcel() {
    const startDate = document.getElementById('start-date').value;
    const startTime = document.getElementById('start-time').value;
    const endDate = document.getElementById('end-date').value;
    const endTime = document.getElementById('end-time').value;

    if (!startDate || !endDate) {
        alert("시작일과 종료일을 선택해주세요.");
        return;
    }

    const startStr = encodeURIComponent(`${startDate} ${startTime}:00`);
    const endStr = encodeURIComponent(`${endDate} ${endTime}:59`);
    window.location.href = `/api/export?start=${startStr}&end=${endStr}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start-date').value = today;
    document.getElementById('end-date').value = today;

    initChart();
    updateCurrentValue();
    setInterval(updateCurrentValue, UPDATE_INTERVAL);

    document.getElementById('btn-query').addEventListener('click', queryHistory);
    document.getElementById('btn-export').addEventListener('click', exportExcel);

    setTimeout(queryHistory, 500);
});
