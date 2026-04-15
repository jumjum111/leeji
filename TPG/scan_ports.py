import serial.tools.list_ports

def scan_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("현재 인식된 COM 포트가 하나도 없습니다! 케이블이 제대로 꽂혀있지 않거나 드라이버 문제입니다.")
        return
        
    print("--- [현재 살아있는 실제 USB 포트 목록] ---")
    for p in ports:
        print(f"포트: {p.device} | 설명: {p.description}")
        
if __name__ == '__main__':
    scan_ports()
