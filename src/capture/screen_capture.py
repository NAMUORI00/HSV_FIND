"""
화면 캡처를 담당하는 모듈
"""

from mss import mss
import numpy as np

class ScreenCapture:
    def __init__(self):
        """화면 캡처 클래스 초기화"""
        self.sct = mss()
        
    def capture(self):
        """현재 화면을 캡처하여 numpy 배열로 반환"""
        screen = self.sct.grab(self.sct.monitors[1])  # 주 모니터 캡처
        return np.array(screen)
        
    def __del__(self):
        """클래스 소멸자"""
        self.sct.close() 