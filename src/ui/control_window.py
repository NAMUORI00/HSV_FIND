"""
HSV 값 조정을 위한 컨트롤 창 모듈
"""

import cv2
from ..detection.hsv_detector import HSVRange

class ControlWindow:
    def __init__(self, window_name="HSV Control", monitor_count=1):
        """컨트롤 창 초기화"""
        self.window_name = window_name
        cv2.namedWindow(self.window_name)
        
        # 모니터 선택 트랙바
        self.monitor_count = monitor_count
        if monitor_count > 1:
            cv2.createTrackbar('Monitor', self.window_name, 1, monitor_count, lambda x: None)
        
        # HSV 트랙바 생성
        cv2.createTrackbar('H Lower', self.window_name, 0, 179, lambda x: None)
        cv2.createTrackbar('H Upper', self.window_name, 179, 179, lambda x: None)
        cv2.createTrackbar('S Lower', self.window_name, 0, 255, lambda x: None)
        cv2.createTrackbar('S Upper', self.window_name, 255, 255, lambda x: None)
        cv2.createTrackbar('V Lower', self.window_name, 0, 255, lambda x: None)
        cv2.createTrackbar('V Upper', self.window_name, 255, 255, lambda x: None)
    
    def get_selected_monitor(self) -> int:
        """현재 선택된 모니터 번호 반환"""
        if self.monitor_count > 1:
            return cv2.getTrackbarPos('Monitor', self.window_name)
        return 1
    
    def get_hsv_range(self) -> HSVRange:
        """현재 설정된 HSV 범위 반환"""
        return HSVRange(
            h_lower=cv2.getTrackbarPos('H Lower', self.window_name),
            h_upper=cv2.getTrackbarPos('H Upper', self.window_name),
            s_lower=cv2.getTrackbarPos('S Lower', self.window_name),
            s_upper=cv2.getTrackbarPos('S Upper', self.window_name),
            v_lower=cv2.getTrackbarPos('V Lower', self.window_name),
            v_upper=cv2.getTrackbarPos('V Upper', self.window_name)
        )
    
    def set_hsv_range(self, hsv_range: HSVRange):
        """HSV 범위 설정"""
        cv2.setTrackbarPos('H Lower', self.window_name, hsv_range.h_lower)
        cv2.setTrackbarPos('H Upper', self.window_name, hsv_range.h_upper)
        cv2.setTrackbarPos('S Lower', self.window_name, hsv_range.s_lower)
        cv2.setTrackbarPos('S Upper', self.window_name, hsv_range.s_upper)
        cv2.setTrackbarPos('V Lower', self.window_name, hsv_range.v_lower)
        cv2.setTrackbarPos('V Upper', self.window_name, hsv_range.v_upper)
    
    def destroy(self):
        """컨트롤 창 제거"""
        cv2.destroyWindow(self.window_name) 