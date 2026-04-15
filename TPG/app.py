import os
os.environ["PYTHONUTF8"] = "1"
import io
import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from dotenv import load_dotenv
from openpyxl import Workbook
import requests

from database import init_db, get_latest_data, get_history_data
from tpg261_serial import TPG261Reader

# 환경 변수 로드
load_dotenv()
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# TPG261 시리얼 리더 인스턴스 (3분마다 측정)
tpg_reader = TPG261Reader(port='COM3', baudrate=9600, interval_seconds=180)

def send_telegram_message(message):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

def start_ngrok():
    try:
        from pyngrok import ngrok
        ngrok_token = os.environ.get('NGROK_AUTHTOKEN')
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)
        
        public_url = ngrok.connect(5000).public_url
        print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:5000\"")
        
        send_telegram_message(f"TPG261 진공 모니터링 서버가 시작되었습니다!\n접속 주소: {public_url}")
    except Exception as e:
        print(f"ngrok 실행 실패: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data/current', methods=['GET'])
def current_data():
    data = get_latest_data()
    data['seconds_until_next'] = tpg_reader.seconds_until_next
    data['latest_pressure'] = tpg_reader.latest_pressure
    return jsonify(data)

@app.route('/api/data/history', methods=['POST'])
def history_data():
    req = request.json
    start_str = req.get('start')
    end_str = req.get('end')
    
    if not start_str or not end_str:
        return jsonify({"error": "잘못된 날짜 형식입니다."}), 400
        
    data = get_history_data(start_str, end_str)
    return jsonify(data)

@app.route('/api/export', methods=['GET'])
def export_excel():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    if not start_str or not end_str:
        return "Start and end dates are required", 400
        
    data = get_history_data(start_str, end_str)
    
    if not data:
        return "No data available for the selected period", 404

    wb = Workbook()
    ws = wb.active
    ws.title = 'Vacuum Data'
    ws.append(['측정시간', '진공도(Mbar/Torr)'])
    
    for row in data:
        ws.append([row['timestamp'], row['pressure']])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"vacuum_data_{start_str[:10]}_to_{end_str[:10]}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    init_db()
    tpg_reader.start()
    threading.Thread(target=start_ngrok, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
