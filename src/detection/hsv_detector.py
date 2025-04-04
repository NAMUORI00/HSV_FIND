"""
HSV 색상 공간을 이용한 객체 탐지 모듈
"""

import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class HSVRange:
    """HSV 색상 범위를 저장하는 데이터 클래스"""
    h_lower: int
    h_upper: int
    s_lower: int
    s_upper: int
    v_lower: int
    v_upper: int

class HSVDetector:
    def __init__(self, min_area=500):
        """HSV 객체 탐지 클래스 초기화"""
        self.min_area = min_area
        self.hsv_range = HSVRange(0, 179, 0, 255, 0, 255)
    
    def set_hsv_range(self, hsv_range: HSVRange):
        """HSV 범위 설정"""
        self.hsv_range = hsv_range
    
    def detect(self, frame):
        """프레임에서 객체 탐지"""
        # BGR에서 HSV로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # HSV 범위로 마스크 생성
        lower_bound = np.array([
            self.hsv_range.h_lower,
            self.hsv_range.s_lower,
            self.hsv_range.v_lower
        ])
        upper_bound = np.array([
            self.hsv_range.h_upper,
            self.hsv_range.s_upper,
            self.hsv_range.v_upper
        ])
        
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # 윤곽선 찾기
        contours, _ = cv2.findContours(
            mask, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 감지된 객체 정보 수집
        detected_objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                detected_objects.append({
                    'area': area,
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'contour': contour
                })
        
        return {
            'mask': mask,
            'objects': detected_objects
        } 