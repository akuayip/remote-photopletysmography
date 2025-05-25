# respirasi_processor.py
import numpy as np
import cv2
import mediapipe as mp
from collections import deque

# Impor fungsi yang kamu butuhkan dari signal_utils.py (jika ada untuk respirasi)
# Contoh:
# try:
#     from signal_utils import bandpass_filter_resp, calculate_respiration_rate
#     SIGNAL_UTILS_RESP_AVAILABLE = True
# except ImportError:
#     SIGNAL_UTILS_RESP_AVAILABLE = False
#     def bandpass_filter_resp(data, fs, low, high, order=3): return data
#     def calculate_respiration_rate(signal, fs): return None, []

class RespirasiProcessor:
    def __init__(self, max_len=300, smoothing_window=5, fps=15): # Tambahkan fps jika perlu
        self.pose = mp.solutions.pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.prev_shoulder_y_avg = None # Simpan rata-rata y bahu
        self.shoulder_motion_signal = deque(maxlen=fps * 30) # Simpan data ~30 detik jika fps diketahui
        self.shoulder_points_history = deque(maxlen=fps * 30) # Simpan histori titik bahu
        self.smoothed_signal_buffer = deque(maxlen=smoothing_window)
        self.fps = fps # Simpan fps
        print(f"DEBUG respirasi_processor: RespirasiProcessor diinisialisasi dengan fps={self.fps}")


    def extract_resp_from_frame(self, frame):
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        
        current_left_shoulder = (0,0)
        current_right_shoulder = (0,0)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_shoulder_lm = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder_lm = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]

            if left_shoulder_lm.visibility > 0.5 and right_shoulder_lm.visibility > 0.5: # Cek visibilitas
                current_left_shoulder = (int(left_shoulder_lm.x * w), int(left_shoulder_lm.y * h))
                current_right_shoulder = (int(right_shoulder_lm.x * w), int(right_shoulder_lm.y * h))
                
                current_shoulder_y_avg = (current_left_shoulder[1] + current_right_shoulder[1]) / 2.0

                if self.prev_shoulder_y_avg is not None:
                    # Perubahan posisi vertikal rata-rata bahu
                    # Gerakan ke atas (inspirasi) bisa jadi dy negatif jika y dihitung dari atas
                    # Atau positif jika dihitung terbalik, kita konsisten saja
                    dy = self.prev_shoulder_y_avg - current_shoulder_y_avg 
                    self.smoothed_signal_buffer.append(dy)
                    smoothed_value = np.mean(self.smoothed_signal_buffer)
                    self.shoulder_motion_signal.append(smoothed_value)
                else:
                    self.shoulder_motion_signal.append(0) # Data pertama, belum ada delta
                
                self.prev_shoulder_y_avg = current_shoulder_y_avg
            else: # Landmark tidak cukup terlihat
                self.shoulder_motion_signal.append(0)
                self.prev_shoulder_y_avg = None # Reset jika tidak terlihat
        else: # Tidak ada pose landmark terdeteksi
            self.shoulder_motion_signal.append(0)
            self.prev_shoulder_y_avg = None # Reset jika tidak terdeteksi

        self.shoulder_points_history.append((current_left_shoulder, current_right_shoulder))

    def get_signal(self): # Ini bisa jadi get_latest_signal_chunk juga
        return list(self.shoulder_motion_signal) # Kembalikan sebagai list

    def get_shoulder_points(self): # Mengembalikan titik bahu terakhir
        if self.shoulder_points_history:
            return [self.shoulder_points_history[-1]] # Kembalikan sebagai list berisi satu tuple (untuk konsistensi dengan kode GUI lama)
        return [((0,0),(0,0))] # Default jika kosong

    # --- METHOD BARU UNTUK GUI ---
    def get_latest_signal_chunk(self, num_samples=200):
        """Mengembalikan N sampel terakhir dari sinyal respirasi."""
        return list(self.shoulder_motion_signal)[-num_samples:]

    def get_current_rr(self, window_size_seconds=20): # RR butuh window lebih panjang
        """Menghitung dan mengembalikan RR saat ini."""
        # if not SIGNAL_UTILS_RESP_AVAILABLE: return None # Jika pakai signal_utils khusus respirasi

        required_samples = int(window_size_seconds * self.fps)
        signal_to_process = self.get_latest_signal_chunk(num_samples=required_samples) # Ambil window yang sesuai

        if len(signal_to_process) < required_samples:
            # print(f"DEBUG RESP RR: Data sinyal belum cukup ({len(signal_to_process)}/{required_samples})")
            return None

        current_signal_window = np.array(signal_to_process)

        try:
            # Frekuensi napas biasanya 0.1 Hz (6x/menit) - 0.5 Hz (30x/menit) atau lebih
            # Sesuaikan rentang filter ini!
            # filtered_signal = bandpass_filter_resp(current_signal_window, fs=self.fps, low=0.1, high=0.7, order=2)
            filtered_signal = current_signal_window # Gunakan mentah dulu jika filter belum ada

            # rr_rpm, peaks_resp = calculate_respiration_rate(filtered_signal, fs=self.fps)
            
            # Placeholder kasar, ganti dengan logikamu:
            from scipy.signal import find_peaks
            # Parameter find_peaks sangat penting untuk sinyal respirasi
            peaks_resp, _ = find_peaks(filtered_signal, height=np.std(filtered_signal)*0.4, distance=self.fps*1.5) # Jarak antar napas minimal 1.5 detik

            if len(peaks_resp) < 2: return None
            duration_seconds = len(filtered_signal) / self.fps
            if duration_seconds == 0: return None
            rr_rpm = (len(peaks_resp) / duration_seconds) * 60

            if 5 <= rr_rpm <= 35: # Validasi rentang RR
                # print(f"DEBUG RESP RR: Terhitung RR = {rr_rpm:.1f} rpm")
                return rr_rpm
            else:
                # print(f"DEBUG RESP RR: RR hasil kalkulasi ({rr_rpm}) di luar rentang wajar.")
                return None

        except Exception as e:
            print(f"ERROR di RespirasiProcessor get_current_rr: {e}")
            import traceback
            traceback.print_exc()
            return None