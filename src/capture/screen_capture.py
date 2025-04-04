"""
화면 캡처를 담당하는 모듈
"""

from mss import mss
import numpy as np
import threading

# 스레드 로컬 저장소 생성
_thread_local = threading.local()

def get_sct():
    """스레드별 mss 인스턴스 반환"""
    if not hasattr(_thread_local, 'sct'):
        _thread_local.sct = mss()
    return _thread_local.sct

class ScreenCapture:
    def __init__(self, capture_size=(320, 320)):
        """화면 캡처 클래스 초기화"""
        # self.sct = mss() # 제거: 스레드별 인스턴스 사용
        self.capture_size = capture_size
        
        # 모니터 정보는 초기화 시 한 번만 가져옴
        with mss() as sct: # 임시 mss 인스턴스 사용
            self.monitors = sct.monitors[1:]
            
        self.selected_monitor_index = 0 # 기본값: 첫 번째 모니터 (인덱스 기준)
        if not self.monitors:
             raise Exception("No monitors found (excluding primary)")
        
    def get_monitors(self):
        """사용 가능한 모니터 목록 반환"""
        return self.monitors # 저장된 정보 반환
        
    def select_monitor(self, monitor_index):
        """캡처할 모니터 선택 (인덱스 기준)"""
        if 0 <= monitor_index < len(self.monitors):
            self.selected_monitor_index = monitor_index
            return True
        return False
        
    def capture(self):
        """선택된 모니터의 중앙 영역을 캡처하여 numpy 배열로 반환"""
        sct = get_sct() # 스레드별 mss 인스턴스 가져오기
        
        try:
            monitor = self.monitors[self.selected_monitor_index]
        except IndexError:
             print(f"Error: Invalid monitor index {self.selected_monitor_index}")
             return None # 또는 기본 모니터 사용
             
        # 모니터 중앙 좌표 계산
        center_x = monitor["left"] + monitor["width"] // 2
        center_y = monitor["top"] + monitor["height"] // 2
        
        # 캡처 영역 계산
        half_width = self.capture_size[0] // 2
        half_height = self.capture_size[1] // 2
        
        # 캡처할 영역 정의 (전체 화면 좌표 기준)
        region = {
            "top": center_y - half_height,
            "left": center_x - half_width,
            "width": self.capture_size[0],
            "height": self.capture_size[1],
            # "mon" 키는 grab에 직접 monitor 딕셔너리를 전달할 때는 불필요
        }
        
        # 영역 캡처 및 numpy 배열로 변환
        # grab() 메서드는 monitor 딕셔너리를 직접 받을 수 있음
        try:
             # 선택된 모니터의 실제 번호 (mss 기준) 찾기
             # self.monitors는 0번(전체)을 제외했으므로 인덱스 + 1
             monitor_number_for_mss = self.selected_monitor_index + 1
             capture_monitor = sct.monitors[monitor_number_for_mss]
             
             # grab 영역 좌표는 전체 화면 기준이어야 함
             grab_region = { 
                 "top": center_y - half_height, 
                 "left": center_x - half_width, 
                 "width": self.capture_size[0], 
                 "height": self.capture_size[1], 
                 "mon": monitor_number_for_mss # 어떤 모니터에서 가져올지 명시
             }
             screen = sct.grab(grab_region)
             # BGR 순서로 반환되도록 처리 (mss는 BGRA 반환)
             return np.array(screen)[:, :, :3][:, :, ::-1] # BGRA -> BGR -> RGB (RGB로 반환해야 함)
        except Exception as e:
             print(f"Error capturing screen: {e}")
             return None
        
    def get_current_monitor_info(self):
        """현재 선택된 모니터 정보 반환"""
        try:
            monitor = self.monitors[self.selected_monitor_index]
            return {
                "index": self.selected_monitor_index,
                "width": monitor["width"],
                "height": monitor["height"],
                "capture_size": self.capture_size
            }
        except IndexError:
             return None
        
    # __del__ 메서드는 스레드별 인스턴스 관리 시 불필요 (자동 정리됨) 