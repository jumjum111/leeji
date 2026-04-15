import serial
import time

def test_communication():
    print("Opening COM7...")
    try:
        # write_timeout을 제거하여 드라이버 잠김을 방지합니다.
        ser = serial.Serial('COM7', 9600, timeout=2)
        ser.setDTR(True)
        ser.setRTS(True)
        time.sleep(1)
    except Exception as e:
        print(f"포트 연결 에러: {e}")
        return

    # 잔여 버퍼를 완전히 비웁니다.
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("1. ESC(통신 전체 리셋) 전송...")
    ser.write(b'\x1B\r\n')
    time.sleep(0.3)
    print("ESC 응답:", ser.read_all())

    print("2. PR1 전송...")
    ser.write(b'PR1\r\n')
    time.sleep(0.3)
    resp = ser.read_all()
    print("PR1 응답:", resp)

    if b'\x06' in resp:
        print("ACK 확인! ENQ 전송...")
        ser.write(b'\x05')
        time.sleep(0.3)
        print("ENQ 응답:", ser.read_all())
    elif b'\x15' in resp:
        print("NAK 수신. 파라미터 확인 명령(PRX) 전송해봄...")
        ser.write(b'PRX\r\n')
        time.sleep(0.3)
        print("PRX 응답:", ser.read_all())

    ser.close()

if __name__ == '__main__':
    test_communication()
