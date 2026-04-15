import serial
import time

def try_command(ser, name, cmd):
    print(f"\n--- Testing: {name} ---")
    ser.reset_input_buffer()
    ser.write(cmd)
    time.sleep(0.3)
    resp = ser.read_all()
    print(f"[{name}] Response: {resp}")
    
    # 만약 ACK(0x06)가 오면 ENQ(0x05) 전송
    if b'\x06' in resp:
        print("  -> ACK received! Sending ENQ...")
        ser.write(b'\x05')
        time.sleep(0.3)
        data = ser.read_all()
        print(f"  -> Data: {data}")
    # 만약 데이터가 먼저 오면 출력
    elif len(resp) > 2 and b',' in resp:
        print("  -> Data received directly!")

def test_all():
    print("Opening COM6...")
    try:
        ser = serial.Serial('COM6', 9600, timeout=1)
        ser.setDTR(True)  # 케이블 전원 확보
        ser.setRTS(True)
        time.sleep(0.5)
    except Exception as e:
        print(f"Serial port error: {e}")
        return

    # 잔여 데이터 청소용 ENQ 및 버퍼 플러시
    ser.write(b'\x05')
    time.sleep(0.2)
    print("Initial flush:", ser.read_all())

    # 여러 가지 케이스 테스트
    commands = [
        ("ENQ only", b'\x05'),
        ("PR1 with CR LF", b'PR1\r\n'),
        ("PR1 with CR only", b'PR1\r'),
        ("PRX with CR LF", b'PRX\r\n'),
        ("PR2 with CR LF", b'PR2\r\n'),
        ("COM,0 (Stop continuous mode)", b'COM,0\r\n'),
        ("RES (Reset gauge)", b'RES\r\n'),
    ]

    for name, cmd in commands:
        try_command(ser, name, cmd)
        time.sleep(1)

    ser.close()
    print("\nTest completed.")

if __name__ == '__main__':
    test_all()
