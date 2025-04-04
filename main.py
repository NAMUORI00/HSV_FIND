"""
HSV 기반 객체 탐지 프로그램
"""

import sys
import threading
import tkinter as tk
import time
import queue
from src.capture.screen_capture import ScreenCapture
from src.ui.control_window import ControlWindow
from src.detection.custom_detector import CustomDetector

# 종료 플래그
exit_flag = False

def main():
    """메인 함수"""
    global exit_flag
    
    # 화면 캡처 객체 생성
    screen_capture = ScreenCapture()
    
    # 객체 검출기 생성
    detector = CustomDetector()
    
    # 컨트롤 윈도우 생성 (루트 Tk 객체 및 큐 포함)
    control_window = ControlWindow(screen_capture, detector)
    data_queue = control_window.queue # 컨트롤 윈도우의 큐 참조
    
    def update_monitor_thread():
        """화면 캡처 및 객체 검출 스레드 함수"""
        while not exit_flag:
            try:
                frame = screen_capture.capture()
                if frame is None:
                    time.sleep(0.01) 
                    continue
                
                result = detector.detect(frame)
                
                original_frame = frame 
                mask_image = result['mask']
                bbox_frame = result['bbox_frame']
                
                # 현재 HSV 범위 가져오기
                hsv_ranges = (
                    (detector.lower_color[0], detector.upper_color[0]),
                    (detector.lower_color[1], detector.upper_color[1]),
                    (detector.lower_color[2], detector.upper_color[2])
                )
                
                # 데이터를 큐에 넣음 (UI 스레드에서 처리)
                try:
                    data_queue.put_nowait((original_frame, mask_image, bbox_frame, hsv_ranges))
                except queue.Full:
                    # 큐가 가득 차면 이전 데이터 무시 (선택적)
                    pass 
                    
                time.sleep(0.01) # CPU 사용률 제어

            except Exception as e:
                if not exit_flag: # 종료 중이 아닐 때만 오류 출력
                     print(f"Error in update_monitor_thread: {e}")
                     # 필요한 경우 여기서 스레드 종료 처리
                     # exit_flag = True 
                time.sleep(0.1) 
        print("Update monitor thread finished.")

    # 모니터링 스레드 시작
    monitor_thread = threading.Thread(target=update_monitor_thread, daemon=True)
    monitor_thread.start()
    
    # 컨트롤 윈도우 시작 (Tkinter 메인 루프)
    try:
        print("Starting main application...")
        control_window.start() # 메인 루프 시작
    except KeyboardInterrupt:
         print("KeyboardInterrupt caught. Initiating shutdown...")
         exit_flag = True 
    finally:
        # --- 메인 루프 종료 후 처리 --- 
        print("Main loop finished. Cleaning up application...")
        if not exit_flag:
            exit_flag = True 
        
        print("Signaling monitor thread to exit...")
        # 큐에 종료 신호를 보내거나 exit_flag 확인으로 충분할 수 있음
        try:
             data_queue.put_nowait(None) # 큐 처리 루프 종료 신호
        except queue.Full:
             pass 
             
        print("Waiting for monitor thread to complete...")
        monitor_thread.join(timeout=2.0) 
        if monitor_thread.is_alive():
             print("Warning: Monitor thread did not complete gracefully.")
             
        # ControlWindow의 start 메서드 finally 블록에서 Tk 윈도우 destroy 처리
            
        print("Application shutdown complete.")

if __name__ == "__main__":
    main() 