"""
화면 캡처를 담당하는 모듈
"""

from mss import mss
import numpy as np

class ScreenCapture:
    def __init__(self, capture_size=(320, 320)):
        """화면 캡처 클래스 초기화"""
        self.sct = mss()
        self.capture_size = capture_size
        self.selected_monitor = 1  # 기본값: 주 모니터
        
    def get_monitors(self):
        """사용 가능한 모니터 목록 반환"""
        return self.sct.monitors[1:]  # 0번은 전체 화면이므로 제외
        
    def select_monitor(self, monitor_number):
        """캡처할 모니터 선택"""
        if 1 <= monitor_number <= len(self.sct.monitors):
            self.selected_monitor = monitor_number
            return True
        return False
        
    def capture(self):
        """선택된 모니터의 중앙 영역을 캡처하여 numpy 배열로 반환"""
        monitor = self.sct.monitors[self.selected_monitor]
        
        # 모니터 중앙 좌표 계산
        center_x = monitor["width"] // 2
        center_y = monitor["height"] // 2
        
        # 캡처 영역 계산
        half_width = self.capture_size[0] // 2
        half_height = self.capture_size[1] // 2
        
        # 캡처할 영역 정의
        region = {
            "top": monitor["top"] + center_y - half_height,
            "left": monitor["left"] + center_x - half_width,
            "width": self.capture_size[0],
            "height": self.capture_size[1],
            "mon": self.selected_monitor
        }
        
        # 영역 캡처 및 numpy 배열로 변환
        screen = self.sct.grab(region)
        return np.array(screen)
        
    def get_current_monitor_info(self):
        """현재 선택된 모니터 정보 반환"""
        monitor = self.sct.monitors[self.selected_monitor]
        return {
            "number": self.selected_monitor,
            "width": monitor["width"],
            "height": monitor["height"],
            "capture_size": self.capture_size
        }
        
    def __del__(self):
        """클래스 소멸자"""
        self.sct.close() 