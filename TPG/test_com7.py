import serial
import time

PORT = 'COM7'

print(f"1. {PORT} 포트 열기 시도...")
try:
    ser = serial.Serial(PORT, 9600, timeout=2, write_timeout=2)
    ser.setDTR(True)
    ser.setRTS(True)
    time.sleep(1)
    print("   포트 열기 성공!")
except Exception as e:
    print(f"   포트 열기 실패: {e}")
    exit()

ser.reset_input_buffer()
ser.reset_output_buffer()

print("2. ESC 전송 시도...")
try:
    ser.write(b'\x1B\r\n')
    time.sleep(0.3)
    esc_resp = ser.read_all()
    print(f"   ESC 응답: {esc_resp}")
except Exception as e:
    print(f"   ESC 전송 실패: {e}")
    ser.close()
    exit()

print("3. PR1 전송 시도...")
try:
    ser.write(b'PR1\r\n')
    time.sleep(0.3)
    pr1_resp = ser.read_all()
    print(f"   PR1 응답: {pr1_resp}")
except Exception as e:
    print(f"   PR1 전송 실패: {e}")
    ser.close()
    exit()

if b'\x06' in pr1_resp:
    print("4. ACK 확인! ENQ 전송...")
    ser.write(b'\x05')
    time.sleep(0.3)
    enq_resp = ser.read_all()
    print(f"   ENQ 응답: {enq_resp}")
else:
    print(f"   ACK 없음 (응답: {pr1_resp})")

ser.close()
print("완료!")
