import cv2
import numpy as np
from mss import mss
import time

def nothing(x):
    pass

# MSS 초기화
sct = mss()

# 윈도우 생성 및 트랙바 설정
cv2.namedWindow('HSV 조정')
cv2.createTrackbar('H Lower', 'HSV 조정', 0, 179, nothing)
cv2.createTrackbar('H Upper', 'HSV 조정', 179, 179, nothing)
cv2.createTrackbar('S Lower', 'HSV 조정', 0, 255, nothing)
cv2.createTrackbar('S Upper', 'HSV 조정', 255, 255, nothing)
cv2.createTrackbar('V Lower', 'HSV 조정', 0, 255, nothing)
cv2.createTrackbar('V Upper', 'HSV 조정', 255, 255, nothing)

try:
    while True:
        # 화면 캡처
        screen = sct.grab(sct.monitors[1])  # 주 모니터 캡처
        
        # 이미지를 numpy 배열로 변환
        frame = np.array(screen)
        
        # BGR에서 HSV로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 트랙바에서 값 읽기
        h_lower = cv2.getTrackbarPos('H Lower', 'HSV 조정')
        h_upper = cv2.getTrackbarPos('H Upper', 'HSV 조정')
        s_lower = cv2.getTrackbarPos('S Lower', 'HSV 조정')
        s_upper = cv2.getTrackbarPos('S Upper', 'HSV 조정')
        v_lower = cv2.getTrackbarPos('V Lower', 'HSV 조정')
        v_upper = cv2.getTrackbarPos('V Upper', 'HSV 조정')
        
        # HSV 범위 설정
        lower_bound = np.array([h_lower, s_lower, v_lower])
        upper_bound = np.array([h_upper, s_upper, v_upper])
        
        # 마스크 생성
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # 원본 이미지에 마스크 적용
        result = cv2.bitwise_and(frame, frame, mask=mask)
        
        # 윤곽선 찾기
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 감지된 객체 표시
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 노이즈 필터링
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f'Area: {int(area)}', (x, y - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 결과 표시
        cv2.imshow('원본', frame)
        cv2.imshow('마스크', mask)
        cv2.imshow('결과', result)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
finally:
    cv2.destroyAllWindows() 