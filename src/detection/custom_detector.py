"""
OpenCV를 사용하지 않는 HSV 기반 객체 검출기
"""

import numpy as np
from numba import jit, prange
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class DetectedObject:
    """검출된 객체 정보"""
    x: int
    y: int
    width: int
    height: int
    area: float
    contour: np.ndarray

class CustomDetector:
    def __init__(self, h_lower=0, h_upper=179, s_lower=0, s_upper=255, v_lower=0, v_upper=255):
        """HSV 기반 객체 검출기 초기화
        
        Args:
            h_lower (int): Hue 하한값 (0-179)
            h_upper (int): Hue 상한값 (0-179)
            s_lower (int): Saturation 하한값 (0-255)
            s_upper (int): Saturation 상한값 (0-255)
            v_lower (int): Value 하한값 (0-255)
            v_upper (int): Value 상한값 (0-255)
        """
        self.set_hsv_range(h_lower, h_upper, s_lower, s_upper, v_lower, v_upper)
    
    def set_hsv_range(self, h_lower, h_upper, s_lower, s_upper, v_lower, v_upper):
        """HSV 범위 설정"""
        self.lower_color = np.array([h_lower, s_lower, v_lower], dtype=np.uint8)
        self.upper_color = np.array([h_upper, s_upper, v_upper], dtype=np.uint8)
    
    @staticmethod
    @jit(nopython=True)
    def _bgr_to_hsv_compute(b: int, g: int, r: int) -> np.ndarray:
        """단일 픽셀의 BGR을 HSV로 변환
        
        Args:
            b (int): Blue 값 (0-255)
            g (int): Green 값 (0-255)
            r (int): Red 값 (0-255)
            
        Returns:
            np.ndarray: HSV 값 [H(0-179), S(0-255), V(0-255)]
        """
        b = b / 255.0
        g = g / 255.0
        r = r / 255.0
        
        maxc = max(r, g, b)
        minc = min(r, g, b)
        v = maxc
        diff = maxc - minc
        
        s = 0.0 if maxc == 0 else (diff / maxc)
        
        h = 0.0
        if maxc != minc:
            if maxc == r:
                h = 60.0 * (g - b) / diff
                if g < b:
                    h += 360.0
            elif maxc == g:
                h = 60.0 * (b - r) / diff + 120.0
            else:
                h = 60.0 * (r - g) / diff + 240.0
        
        # OpenCV 범위로 변환
        h = (h / 2.0)  # 0-180 범위로 변환
        s = s * 255.0  # 0-255 범위로 변환
        v = v * 255.0  # 0-255 범위로 변환
        
        return np.array([
            min(max(round(h), 0), 180),
            min(max(round(s), 0), 255),
            min(max(round(v), 0), 255)
        ], dtype=np.uint8)
    
    def bgr_to_hsv(self, bgr_image: np.ndarray) -> np.ndarray:
        """BGR 이미지를 HSV로 변환
        
        Args:
            bgr_image (np.ndarray): BGR 이미지
            
        Returns:
            np.ndarray: HSV 이미지
        """
        # 4채널 이미지를 3채널로 변환
        if bgr_image.shape[2] == 4:
            bgr_image = bgr_image[..., :3]
        
        height, width = bgr_image.shape[:2]
        hsv = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            for x in range(width):
                b, g, r = bgr_image[y, x]
                hsv[y, x] = self._bgr_to_hsv_compute(b, g, r)
        
        return hsv
    
    @staticmethod
    @jit(nopython=True)
    def _check_color_range(h: int, s: int, v: int, lower: np.ndarray, upper: np.ndarray) -> bool:
        """단일 픽셀의 HSV 값이 지정된 범위 내에 있는지 확인
        
        Args:
            h (int): Hue 값 (0-179)
            s (int): Saturation 값 (0-255)
            v (int): Value 값 (0-255)
            lower (np.ndarray): HSV 하한값 [H, S, V]
            upper (np.ndarray): HSV 상한값 [H, S, V]
            
        Returns:
            bool: 범위 내에 있으면 True
        """
        # Hue는 원형이므로 특별 처리
        if lower[0] <= upper[0]:
            h_match = lower[0] <= h <= upper[0]
        else:
            h_match = h >= lower[0] or h <= upper[0]
        
        # Saturation과 Value는 일반 범위 비교
        s_match = lower[1] <= s <= upper[1]
        v_match = lower[2] <= v <= upper[2]
        
        return h_match and s_match and v_match
    
    def create_mask(self, hsv_image: np.ndarray) -> np.ndarray:
        """HSV 이미지에서 마스크 생성
        
        Args:
            hsv_image (np.ndarray): HSV 이미지
            
        Returns:
            np.ndarray: 이진 마스크 이미지
        """
        height, width = hsv_image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for y in prange(height):
            for x in prange(width):
                h, s, v = hsv_image[y, x]
                if self._check_color_range(h, s, v, self.lower_color, self.upper_color):
                    mask[y, x] = 255
        
        return mask
    
    @staticmethod
    @jit(nopython=True)
    def _dilate_compute(mask: np.ndarray, kernel_size: int = 3, iterations: int = 2) -> np.ndarray:
        """마스크 팽창 연산
        
        Args:
            mask (np.ndarray): 이진 마스크 이미지
            kernel_size (int): 커널 크기
            iterations (int): 반복 횟수
            
        Returns:
            np.ndarray: 팽창된 마스크 이미지
        """
        height, width = mask.shape
        pad = kernel_size // 2
        result = mask.copy()
        
        for _ in range(iterations):
            temp = np.zeros_like(result)
            for y in range(height):
                for x in range(width):
                    # 커널 영역 검사
                    for ky in range(max(0, y-pad), min(height, y+pad+1)):
                        for kx in range(max(0, x-pad), min(width, x+pad+1)):
                            if result[ky, kx] > 0:
                                temp[y, x] = 255
                                break
                        if temp[y, x] > 0:
                            break
            result = temp
        
        return result
    
    def find_contours(self, mask: np.ndarray, min_area: int = 20) -> List[Tuple[np.ndarray, float]]:
        """마스크에서 윤곽선 찾기
        
        Args:
            mask (np.ndarray): 이진 마스크 이미지
            min_area (int): 최소 면적
            
        Returns:
            List[Tuple[np.ndarray, float]]: (윤곽선 좌표 배열, 면적) 리스트
        """
        height, width = mask.shape
        visited = np.zeros_like(mask, dtype=bool)
        contours = []
        
        def trace_contour(start_y: int, start_x: int) -> Optional[np.ndarray]:
            """윤곽선 추적"""
            contour = []
            stack = [(start_y, start_x)]
            directions = [
                (0, 1),   # 오른쪽
                (1, 1),   # 오른쪽 아래
                (1, 0),   # 아래
                (1, -1),  # 왼쪽 아래
                (0, -1),  # 왼쪽
                (-1, -1), # 왼쪽 위
                (-1, 0),  # 위
                (-1, 1)   # 오른쪽 위
            ]
            
            while stack:
                y, x = stack.pop()
                if visited[y, x]:
                    continue
                
                visited[y, x] = True
                is_edge = False
                
                # 가장자리 픽셀 확인
                for dy, dx in directions:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if mask[ny, nx] == 0:
                            is_edge = True
                            break
                    else:
                        is_edge = True
                        break
                
                if is_edge:
                    contour.append((x, y))
                    
                    # 가장자리 우선 탐색
                    for dy, dx in directions:
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < height and 0 <= nx < width and 
                            mask[ny, nx] > 0 and not visited[ny, nx]):
                            stack.append((ny, nx))
            
            return np.array(contour) if contour else None
        
        # 외곽 윤곽선 찾기
        for y in range(height):
            for x in range(width):
                if mask[y, x] > 0 and not visited[y, x]:
                    contour = trace_contour(y, x)
                    if contour is not None:
                        area = self.calculate_contour_area(contour)
                        if area >= min_area:
                            contours.append((contour, area))
        
        return contours
    
    @staticmethod
    def calculate_contour_area(contour: np.ndarray) -> float:
        """윤곽선의 면적 계산 (Green's theorem)
        
        Args:
            contour (np.ndarray): 윤곽선 좌표 배열
            
        Returns:
            float: 면적
        """
        x = contour[:, 0]
        y = contour[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    @staticmethod
    def get_bounding_rect(contour: np.ndarray) -> Tuple[int, int, int, int]:
        """윤곽선의 경계 사각형 계산
        
        Args:
            contour (np.ndarray): 윤곽선 좌표 배열
            
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        x_coords = contour[:, 0]
        y_coords = contour[:, 1]
        
        x = int(np.min(x_coords))
        y = int(np.min(y_coords))
        w = int(np.max(x_coords) - x + 1)
        h = int(np.max(y_coords) - y + 1)
        
        return (x, y, w, h)
    
    def detect(self, frame: np.ndarray) -> dict:
        """프레임에서 객체 검출
        
        Args:
            frame (np.ndarray): BGR 이미지 (numpy array)
            
        Returns:
            dict: 검출 결과 
                  {'hsv': hsv_image, 
                   'mask': dilated_mask, 
                   'objects': detected_objects,
                   'bbox_frame': bbox_drawn_frame}
        """
        # 1. BGR to HSV 변환
        hsv_image = self.bgr_to_hsv(frame)
        
        # 2. HSV 범위 기반 마스크 생성
        mask = self.create_mask(hsv_image)
        
        # 3. 노이즈 제거 (팽창)
        dilated_mask = self._dilate_compute(mask)
        
        # 4. 윤곽선 찾기
        contours_with_area = self.find_contours(dilated_mask)
        
        # 5. 객체 정보 생성
        detected_objects = []
        for contour, area in contours_with_area:
            if area > 20: # 최소 면적 필터링
                x, y, w, h = self.get_bounding_rect(contour)
                detected_objects.append(DetectedObject(
                    x=x, y=y, width=w, height=h, area=area, contour=contour
                ))
        
        # 6. 바운딩 박스가 그려진 프레임 생성 (추가)
        bbox_drawn_frame = self.draw_objects(frame.copy(), detected_objects) # 원본을 복사하여 그림
        
        return {
            'hsv': hsv_image,
            'mask': dilated_mask,
            'objects': detected_objects,
            'bbox_frame': bbox_drawn_frame # 결과에 추가
        }
    
    def draw_objects(self, frame: np.ndarray, objects: List[DetectedObject], 
                    color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray: # thickness 추가
        """프레임에 검출된 객체 바운딩 박스 그리기 (NumPy 사용)

        Args:
            frame (np.ndarray): 원본 BGR 프레임
            objects (List[DetectedObject]): 검출된 객체 리스트
            color (Tuple[int, int, int]): BGR 색상 튜플 (기본값: 녹색)
            thickness (int): 선 두께

        Returns:
            np.ndarray: 바운딩 박스가 그려진 프레임
        """
        output_frame = frame # 원본 프레임 직접 수정 (또는 copy() 사용)
        
        for obj in objects:
            x, y, w, h = obj.x, obj.y, obj.width, obj.height
            
            # NumPy 슬라이싱을 사용하여 사각형 그리기
            # 상단 가로선
            output_frame[y:y+thickness, x:x+w] = color
            # 하단 가로선
            output_frame[y+h-thickness:y+h, x:x+w] = color
            # 좌측 세로선
            output_frame[y:y+h, x:x+thickness] = color
            # 우측 세로선
            output_frame[y:y+h, x+w-thickness:x+w] = color
        
        return output_frame 