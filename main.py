"""
HSV 기반 객체 탐지 프로그램 메인 스크립트
"""

import cv2
import numpy as np
from src.capture.screen_capture import ScreenCapture
from src.detection.hsv_detector import HSVDetector
from src.ui.control_window import ControlWindow

def draw_objects(frame, detected_objects):
    """감지된 객체를 프레임에 표시"""
    for obj in detected_objects:
        x, y, w, h = obj['x'], obj['y'], obj['width'], obj['height']
        # 경계 상자 그리기
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # 면적 표시
        cv2.putText(frame, f'Area: {int(obj["area"])}', (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

def main():
    # 화면 캡처 객체 초기화
    screen_capture = ScreenCapture(capture_size=(320, 320))
    
    # 사용 가능한 모니터 수 확인
    monitors = screen_capture.get_monitors()
    monitor_count = len(monitors)
    
    # 객체 초기화
    hsv_detector = HSVDetector()
    control_window = ControlWindow(monitor_count=monitor_count)
    
    # 모니터 정보 출력
    print(f"Available Monitors: {monitor_count}")
    for i, monitor in enumerate(monitors, 1):
        print(f"Monitor {i}: {monitor['width']}x{monitor['height']}")
    
    try:
        while True:
            # 선택된 모니터 업데이트
            selected_monitor = control_window.get_selected_monitor()
            if screen_capture.select_monitor(selected_monitor):
                # 화면 캡처
                frame = screen_capture.capture()
                
                # HSV 범위 업데이트
                hsv_range = control_window.get_hsv_range()
                hsv_detector.set_hsv_range(hsv_range)
                
                # 객체 탐지
                result = hsv_detector.detect(frame)
                
                # 결과 표시
                draw_objects(frame, result['objects'])
                
                # 창 표시
                cv2.imshow('Original', frame)
                cv2.imshow('Mask', result['mask'])
                cv2.imshow('Result', cv2.bitwise_and(frame, frame, mask=result['mask']))
            
            # 'q' 키를 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # 리소스 정리
        cv2.destroyAllWindows()
        control_window.destroy()

if __name__ == '__main__':
    main() 