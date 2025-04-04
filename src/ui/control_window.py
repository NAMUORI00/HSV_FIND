"""
HSV 값 조정을 위한 컨트롤 윈도우
"""

import tkinter as tk
from tkinter import ttk, filedialog
import json
import os
import sys # main.py의 exit_flag 접근을 위해
from src.ui.monitor_window import MonitorWindow
import queue

SETTINGS_FILE = 'hsv_settings.json'

class ControlWindow:
    def __init__(self, screen_capture, detector):
        """컨트롤 윈도우 초기화
        
        Args:
            screen_capture: 화면 캡처 객체
            detector: 객체 검출기
        """
        self.screen_capture = screen_capture
        self.detector = detector
        
        # 모니터 목록 가져오기
        self.monitors = screen_capture.get_monitors()
        
        # UI 초기화
        self.root = tk.Tk()
        self.init_ui()
        
        # MonitorWindow 생성 (Toplevel)
        self.monitor_window = MonitorWindow(self.root, "Detection Monitor")
        self.monitor_window.withdraw() # 초기에는 숨김
        
        # 모니터링 윈도우 표시/숨김 버튼 추가
        self.show_monitor_button = ttk.Button(self.root, text="Show Monitor", command=self.toggle_monitor_window)
        self.show_monitor_button.pack(pady=5)
        
        # 스레드 통신을 위한 큐 생성
        self.queue = queue.Queue()
        
        # 주기적으로 큐 확인 및 UI 업데이트
        self.queue_check_interval = 50 # ms
        self.check_queue()
        
        # 초기 설정 로드
        self.load_settings()
        
    def init_ui(self):
        """UI 초기화"""
        self.root.title('HSV Control')
        self.root.geometry('450x350') # 창 크기 조정
        
        # === 창 닫기 이벤트 처리 ===
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # ==========================
        
        # --- 모니터 선택 --- 
        monitor_frame = ttk.Frame(self.root)
        monitor_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(monitor_frame, text='Monitor:').pack(side='left')
        self.monitor_var = tk.StringVar()
        monitor_combo = ttk.Combobox(monitor_frame, textvariable=self.monitor_var, width=40)
        monitor_combo['values'] = [f'Monitor {i}: {m["width"]}x{m["height"]}' 
                                 for i, m in enumerate(self.monitors, 1)]
        if self.monitors:
             monitor_combo.current(0)
        monitor_combo.pack(side='left', fill='x', expand=True, padx=5)
        monitor_combo.bind('<<ComboboxSelected>>', self.on_monitor_changed)
        
        # --- HSV 슬라이더 --- 
        hsv_frame = ttk.LabelFrame(self.root, text='HSV Controls')
        hsv_frame.pack(fill='x', padx=10, pady=5)
        
        # 슬라이더 변수 생성
        self.hue_min = tk.IntVar()
        self.hue_max = tk.IntVar()
        self.sat_min = tk.IntVar()
        self.sat_max = tk.IntVar()
        self.val_min = tk.IntVar()
        self.val_max = tk.IntVar()

        # 슬라이더 생성 함수
        def create_slider(parent, text, var_min, var_max, from_, to):
            frame = ttk.Frame(parent)
            frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(frame, text=text, width=10).pack(side='left')
            ttk.Label(frame, text='Min:', width=4).pack(side='left')
            min_scale = ttk.Scale(frame, from_=from_, to=to, variable=var_min, 
                     orient='horizontal', command=self.on_slider_changed)
            min_scale.pack(side='left', fill='x', expand=True)
            ttk.Label(frame, text='Max:', width=4).pack(side='left')
            max_scale = ttk.Scale(frame, from_=from_, to=to, variable=var_max,
                     orient='horizontal', command=self.on_slider_changed)
            max_scale.pack(side='left', fill='x', expand=True)
            return min_scale, max_scale

        create_slider(hsv_frame, 'Hue:', self.hue_min, self.hue_max, 0, 179)
        create_slider(hsv_frame, 'Saturation:', self.sat_min, self.sat_max, 0, 255)
        create_slider(hsv_frame, 'Value:', self.val_min, self.val_max, 0, 255)
        
        # --- HSV 값 표시 --- 
        self.hsv_label = ttk.Label(self.root, text='HSV Range: H[0-179], S[0-255], V[0-255]', anchor='center')
        self.hsv_label.pack(fill='x', padx=10, pady=5)
        
        # --- 설정 저장/불러오기 버튼 --- 
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Load Settings", command=self.load_settings).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side='left', expand=True, padx=5)
        
    def on_monitor_changed(self, event):
        """모니터 선택 변경 이벤트"""
        try:
            index = event.widget.current()
            self.screen_capture.select_monitor(index)
        except tk.TclError: # 위젯이 파괴된 경우 등 예외 처리
            pass 
            
    def on_slider_changed(self, *args):
        """슬라이더 값 변경 이벤트"""
        # 최소값이 최대값보다 커지는 것 방지
        if self.hue_min.get() > self.hue_max.get():
            self.hue_min.set(self.hue_max.get())
        if self.sat_min.get() > self.sat_max.get():
            self.sat_min.set(self.sat_max.get())
        if self.val_min.get() > self.val_max.get():
            self.val_min.set(self.val_max.get())
            
        # HSV 범위 업데이트
        self.detector.set_hsv_range(
            self.hue_min.get(), self.hue_max.get(),
            self.sat_min.get(), self.sat_max.get(),
            self.val_min.get(), self.val_max.get()
        )
        
        # HSV 값 표시 업데이트
        self.update_hsv_label()
        
    def update_hsv_label(self):
         """HSV 레이블 업데이트"""
         self.hsv_label.config(
            text=f'HSV Range: H[{self.hue_min.get()}-{self.hue_max.get()}], '
                 f'S[{self.sat_min.get()}-{self.sat_max.get()}], '
                 f'V[{self.val_min.get()}-{self.val_max.get()}]'
        )

    def save_settings(self):
        """현재 HSV 설정을 파일에 저장"""
        settings = {
            'hue_min': self.hue_min.get(),
            'hue_max': self.hue_max.get(),
            'sat_min': self.sat_min.get(),
            'sat_max': self.sat_max.get(),
            'val_min': self.val_min.get(),
            'val_max': self.val_max.get(),
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"Settings saved to {SETTINGS_FILE}") # 사용자 피드백
        except IOError as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """파일에서 HSV 설정을 불러옴"""
        if not os.path.exists(SETTINGS_FILE):
            # 기본값 설정 및 라벨 업데이트
            self.hue_min.set(0)
            self.hue_max.set(179)
            self.sat_min.set(0)
            self.sat_max.set(255)
            self.val_min.set(0)
            self.val_max.set(255)
            self.on_slider_changed() # 탐지기 및 라벨 업데이트
            print(f"{SETTINGS_FILE} not found. Using default settings.")
            return
            
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            
            self.hue_min.set(settings.get('hue_min', 0))
            self.hue_max.set(settings.get('hue_max', 179))
            self.sat_min.set(settings.get('sat_min', 0))
            self.sat_max.set(settings.get('sat_max', 255))
            self.val_min.set(settings.get('val_min', 0))
            self.val_max.set(settings.get('val_max', 255))
            
            # 슬라이더 변경 이벤트 호출하여 값 적용 및 라벨 업데이트
            self.on_slider_changed()
            print(f"Settings loaded from {SETTINGS_FILE}") # 사용자 피드백
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading settings: {e}. Using default settings.")
            # 오류 발생 시 기본값 사용
            self.hue_min.set(0)
            self.hue_max.set(179)
            self.sat_min.set(0)
            self.sat_max.set(255)
            self.val_min.set(0)
            self.val_max.set(255)
            self.on_slider_changed()
    
    def toggle_monitor_window(self):
        """모니터링 윈도우 표시/숨김 토글"""
        if self.monitor_window.winfo_viewable():
            self.monitor_window.withdraw()
            self.show_monitor_button.config(text="Show Monitor")
        else:
            self.monitor_window.deiconify()
            self.show_monitor_button.config(text="Hide Monitor")

    def check_queue(self):
        """주기적으로 큐를 확인하여 MonitorWindow 업데이트"""
        try:
            while not self.queue.empty():
                data = self.queue.get_nowait()
                if data is None: # 종료 신호
                    return 
                
                original, mask, bbox, hsv_ranges = data
                
                # MonitorWindow가 존재하고 보이면 업데이트
                if self.monitor_window and self.monitor_window.winfo_exists() and self.monitor_window.winfo_viewable():
                    self.monitor_window.update_frame(original, mask, bbox)
                    self.monitor_window.update_hsv_range(*hsv_ranges)
                    
        except queue.Empty:
            pass # 큐가 비어있으면 아무것도 안 함
        except Exception as e:
             print(f"Error processing queue: {e}")
        finally:
            # 다음 큐 확인 예약
            if hasattr(self, 'root') and self.root.winfo_exists(): # 루트 윈도우 존재 확인
                 self.root.after(self.queue_check_interval, self.check_queue)

    def on_closing(self):
        """창 닫기 버튼 클릭 시 호출될 함수"""
        print("Control window closing...")
        
        # main.py의 exit_flag 설정
        try:
             main_module = sys.modules['__main__']
             main_module.exit_flag = True 
             # 스레드가 종료되도록 큐에 종료 신호 추가 (선택적)
             self.queue.put(None) 
        except KeyError:
             print("Warning: Could not set exit_flag in main module.")
        
        # MonitorWindow 닫기 (destroy 호출)
        if self.monitor_window and self.monitor_window.winfo_exists():
            print("Destroying monitor window...")
            self.monitor_window.destroy()
            self.monitor_window = None # 참조 제거
            
        # 메인 루프 종료
        print("Quitting main loop...")
        self.root.quit()
        # destroy는 start 메서드의 finally 블록에서 처리

    def start(self):
        """윈도우 시작"""
        # 프로그램 시작 시 슬라이더 값에 맞춰 detector 초기화
        self.on_slider_changed()
        try:
            self.root.mainloop()
        finally:
             # mainloop 종료 후 최종 정리
             print("Main loop finished in ControlWindow. Cleaning up...")
             # Monitor 윈도우가 아직 존재하면 확실히 닫기
             if self.monitor_window and self.monitor_window.winfo_exists():
                 self.monitor_window.destroy()
             # 루트 윈도우 파괴 (이미 on_closing에서 quit 했으므로 destroy만)
             if hasattr(self, 'root') and self.root.winfo_exists():
                 self.root.destroy()
            
    # def stop(self): # stop 메서드 대신 on_closing 사용
    #     """윈도우 종료"""
    #     # 종료 시 현재 설정 저장 (선택 사항)
    #     # self.save_settings()
    #     self.root.quit()
    #     self.root.destroy() # Tkinter 윈도우 완전 제거 