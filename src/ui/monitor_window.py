"""
실시간 모니터링을 위한 Toplevel 윈도우
"""

import tkinter as tk
import numpy as np

class MonitorWindow(tk.Toplevel):
    def __init__(self, parent, title):
        """모니터링 윈도우 초기화
        
        Args:
            parent: 부모 윈도우 (ControlWindow의 root)
            title: 윈도우 제목
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("960x350") # 초기 크기 설정
        
        # 창 닫기 버튼 동작 재정의 (숨기기)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        
        # 캔버스 생성 
        self.canvas = tk.Canvas(self, width=960, height=320) 
        self.canvas.pack(side='top', fill='both', expand=True)
        
        # HSV 범위 표시 레이블
        self.hsv_label = tk.Label(self, text="HSV Range: [0-179, 0-255, 0-255]")
        self.hsv_label.pack(side='bottom', fill='x')
        
        # 업데이트 주기 (ms)
        self.delay = 15
        
        # 이미지 참조 저장
        self.photo_original = None
        self.photo_mask = None
        self.photo_bbox = None
        
        self.last_width = 0
        self.last_height = 0

    def update_frame(self, original_frame, mask_image, bbox_frame):
        """프레임 업데이트 (ControlWindow에서 호출)
        
        Args:
            original_frame: 원본 프레임 (numpy array, RGB)
            mask_image: 마스크 이미지 (numpy array, 흑백)
            bbox_frame: 바운딩 박스가 그려진 프레임 (numpy array, RGB)
        """
        if original_frame is None or mask_image is None or bbox_frame is None:
            return
        
        # Toplevel이 파괴되었는지 확인
        if not self.winfo_exists():
            return
            
        height, width = original_frame.shape[:2]

        # 창 크기 변경 감지 및 캔버스/창 크기 조정
        if width > 0 and height > 0 and (width != self.last_width or height != self.last_height):
            total_width = width * 3
            self.geometry(f"{total_width}x{height + 30}") # 레이블 공간 고려
            self.canvas.config(width=total_width, height=height)
            self.last_width = width
            self.last_height = height

        # 이미지 업데이트 (try-except 추가)
        try:
            # 1. 원본 이미지 표시
            img_data_orig = self._array_to_photoimage(original_frame)
            self.photo_original = img_data_orig
            self.canvas.create_image(0, 0, image=self.photo_original, anchor='nw')
            
            # 2. 마스크 이미지 표시
            mask_rgb = np.stack((mask_image,) * 3, axis=-1)
            img_data_mask = self._array_to_photoimage(mask_rgb)
            self.photo_mask = img_data_mask
            self.canvas.create_image(width, 0, image=self.photo_mask, anchor='nw')

            # 3. 바운딩 박스 이미지 표시
            img_data_bbox = self._array_to_photoimage(bbox_frame)
            self.photo_bbox = img_data_bbox
            self.canvas.create_image(width * 2, 0, image=self.photo_bbox, anchor='nw')
        except tk.TclError as e:
            # 위젯이 파괴된 후 업데이트 시도 시 발생 가능
            print(f"MonitorWindow TclError during image update: {e}")
        
    def update_hsv_range(self, hue_range, sat_range, val_range):
        """HSV 범위 표시 업데이트 (ControlWindow에서 호출)
        
        Args:
            hue_range: (min, max) Hue 범위
            sat_range: (min, max) Saturation 범위
            val_range: (min, max) Value 범위
        """
        if not self.winfo_exists():
             return
        try:
            text = f"HSV Range: H[{hue_range[0]}-{hue_range[1]}], "
            text += f"S[{sat_range[0]}-{sat_range[1]}], "
            text += f"V[{val_range[0]}-{val_range[1]}]"
            self.hsv_label.config(text=text)
        except tk.TclError as e:
            print(f"MonitorWindow TclError during HSV update: {e}")
            
    def _array_to_photoimage(self, arr):
        """numpy 배열을 PhotoImage로 변환"""
        height, width = arr.shape[:2]
        data = f'P6 {width} {height} 255 '.encode() + arr.astype(np.uint8).tobytes()
        return tk.PhotoImage(width=width, height=height, data=data, format='PPM')
        
    # start() 와 stop() 메서드는 더 이상 필요 없음 (부모가 관리) 