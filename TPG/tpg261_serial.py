import serial
import time
import threading
import traceback
from database import insert_data

class TPG261Reader:
    def __init__(self, port='COM6', baudrate=9600, interval_seconds=180):
        self.port = port
        self.baudrate = baudrate
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.latest_pressure = 0.0
        self.seconds_until_next = interval_seconds

    def parse_value(self, data_str):
        try:
            lines = data_str.split('\n')
            for line in reversed(lines):
                parts = line.split(',')
                if len(parts) >= 2:
                    value_str = parts[1].strip()
                    value_str = value_str.replace('*', 'E')
                    return float(value_str)
        except Exception as e:
            print(f"데이터 파싱 에러: {e}")
        return None

    def _open_port_with_timeout(self, timeout=5):
        result = [None]
        error = [None]

        def _open():
            try:
                ser = serial.Serial(self.port, self.baudrate, timeout=2)
                result[0] = ser
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=_open)
        t.daemon = True
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            print(f"[read] 포트 열기 타임아웃 ({timeout}초)")
            return None
        if error[0]:
            print(f"[read] 포트 열기 실패: {error[0]}")
            return None
        return result[0]

    def read_pressure_once(self):
        print(f"[read] 측정 시도 시작 (포트: {self.port})")
        for attempt in range(3):
            ser = None
            try:
                print(f"[read] 시도 {attempt+1}/3 - 포트 열기...")
                ser = self._open_port_with_timeout(timeout=5)
                if ser is None:
                    print(f"[read] 시도 {attempt+1}/3 - 포트 열기 실패, 건너뜀")
                    if attempt < 2:
                        time.sleep(5)
                    continue

                print(f"[read] 포트 열기 성공")
                ser.setDTR(True)
                ser.setRTS(True)
                print(f"[read] DTR/RTS 설정 완료")
                time.sleep(1)

                print(f"[read] ESC 전송...")
                ser.write(b'\x1B\r\n')
                time.sleep(0.3)
                esc_resp = ser.read_all()
                print(f"[read] ESC 응답: {esc_resp}")

                print(f"[read] PR1 전송...")
                ser.write(b'PR1\r\n')
                time.sleep(0.3)
                resp = ser.read_all()
                print(f"[read] PR1 응답: {resp}")

                if b'\x06' in resp:
                    ser.write(b'\x05')
                    time.sleep(0.3)
                    data_bytes = ser.read_all()
                    data_str = data_bytes.decode('ascii', errors='ignore').strip()
                    print(f"[read] ENQ 응답: {data_bytes}")
                    pressure = self.parse_value(data_str)
                    if pressure is not None:
                        print(f"[read] 파싱 성공: {pressure:.3e}")
                        return pressure
                    print(f"[read] 파싱 실패: {data_bytes}")
                else:
                    print(f"[read] ACK 없음: {resp}")

            except Exception as e:
                print(f"[read] 시도 {attempt+1}/3 예외: {e}")
                traceback.print_exc()
            finally:
                if ser and ser.is_open:
                    try:
                        ser.setDTR(False)
                        ser.setRTS(False)
                    except:
                        pass
                    ser.close()
                    print(f"[read] 포트 닫음")

            if attempt < 2:
                print(f"[read] 5초 대기 후 재시도...")
                time.sleep(5)

        print(f"[read] 3회 모두 실패")
        return None

    def _loop(self):
        first_read = True
        last_insert_time = 0

        while self.running:
            try:
                print("[루프] 측정 시작...")
                pressure = self.read_pressure_once()

                if pressure is not None:
                    self.latest_pressure = pressure
                    current_time = time.time()

                    if first_read or (current_time - last_insert_time >= self.interval):
                        insert_data(pressure)
                        last_insert_time = current_time
                        first_read = False
                        print(f"[DB 저장] {pressure:.3e} Mbar")
                    else:
                        print(f"[측정 성공] {pressure:.3e} Mbar")

                    self.seconds_until_next = self.interval
                    while self.seconds_until_next > 0 and self.running:
                        time.sleep(1)
                        self.seconds_until_next -= 1
                else:
                    print("측정 실패, 20초 후 재시도...")
                    self.seconds_until_next = 20
                    while self.seconds_until_next > 0 and self.running:
                        time.sleep(1)
                        self.seconds_until_next -= 1

            except Exception as e:
                print(f"[루프 에러] {e}")
                traceback.print_exc()
                print("[루프] 20초 후 재시도...")
                self.seconds_until_next = 20
                while self.seconds_until_next > 0 and self.running:
                    time.sleep(1)
                    self.seconds_until_next -= 1

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print(f"TPG261 모니터링 시작 (포트: {self.port}, 간격: {self.interval}초)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("TPG261 모니터링 종료")
