# rppg_processor.py

import numpy as np
import cv2
import mediapipe as mp

# Impor fungsi yang kamu butuhkan dari signal_utils.py
# Pastikan nama file dan nama fungsinya sesuai dengan yang kamu punya.
# Contoh:
try:
    from signal_utils import bandpass_filter, calculate_heart_rate
    SIGNAL_UTILS_AVAILABLE = True
    print("DEBUG rppg_processor: signal_utils berhasil diimpor.")
except ImportError:
    SIGNAL_UTILS_AVAILABLE = False
    print("PERINGATAN rppg_processor: signal_utils tidak ditemukan. Perhitungan HR mungkin tidak akurat/tidak bekerja.")
    # Definisikan fungsi dummy jika tidak ada, agar tidak error saat dipanggil
    def bandpass_filter(data, fs, low, high, order=3):
        print("PERINGATAN: bandpass_filter dummy dipanggil.")
        return data # Kembalikan data asli jika fungsi tidak ada
    def calculate_heart_rate(signal, fs):
        print("PERINGATAN: calculate_heart_rate dummy dipanggil.")
        # Contoh placeholder sangat kasar, JANGAN DIGUNAKAN UNTUK HASIL AKURAT
        if len(signal) < fs * 2: return None, [] # Butuh minimal 2 detik data
        from scipy.signal import find_peaks # Hanya untuk placeholder kasar
        peaks, _ = find_peaks(signal, prominence=np.std(signal)*0.3)
        duration_seconds = len(signal) / fs
        if duration_seconds == 0 or len(peaks) < 2: return None, []
        hr = (len(peaks) / duration_seconds) * 60
        return hr, peaks


class RPPGProcessor:
    def __init__(self, fps=30):
        self.fps = fps
        self.r, self.g, self.b = [], [], []
        self.timestamps = [] # Untuk menyimpan timestamp setiap frame, berguna untuk HR akurat

        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        self.last_forehead_rect = None
        
        # Menyimpan sinyal rPPG yang sudah diproses (misalnya hasil dari compute_pos)
        self.processed_rppg_signal = []
        print(f"DEBUG rppg_processor: RPPGProcessor diinisialisasi dengan fps={self.fps}")

    def extract_rgb_from_frame(self, frame):
        # Tambahkan timestamp
        current_time = cv2.getTickCount() / cv2.getTickFrequency() # Waktu dalam detik
        self.timestamps.append(current_time)
        if len(self.timestamps) > self.fps * 30: # Simpan maksimal 30 detik data timestamp
            self.timestamps.pop(0)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        h, w, _ = frame.shape
        r_mean, g_mean, b_mean = 0, 0, 0

        if results.detections:
            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape # Gunakan dimensi frame asli untuk bbox
            
            xmin = int(bboxC.xmin * iw)
            ymin = int(bboxC.ymin * ih)
            width = int(bboxC.width * iw)
            height = int(bboxC.height * ih)

            # ROI Dahi
            forehead_x1 = xmin + int(0.15 * width)
            forehead_x2 = xmin + int(0.85 * width)
            # Penyesuaian ROI y untuk dahi, mungkin perlu lebih hati-hati
            forehead_y1 = ymin + int(0.1 * height) # Sedikit di bawah batas atas bounding box wajah
            forehead_y2 = ymin + int(0.3 * height) # Ambil sekitar 20% tinggi wajah untuk dahi

            forehead_x1 = max(0, forehead_x1)
            forehead_x2 = min(iw, forehead_x2) # Gunakan iw
            forehead_y1 = max(0, forehead_y1)
            forehead_y2 = min(ih, forehead_y2) # Gunakan ih

            self.last_forehead_rect = (forehead_x1, forehead_y1, forehead_x2, forehead_y2)
            
            if forehead_x1 < forehead_x2 and forehead_y1 < forehead_y2: # Pastikan ROI valid
                roi = frame[forehead_y1:forehead_y2, forehead_x1:forehead_x2]
                if roi.size > 0:
                    b_mean, g_mean, r_mean = np.mean(roi, axis=(0, 1)) # OpenCV BGR order
            else:
                self.last_forehead_rect = None
        else:
            self.last_forehead_rect = None
            
        # Simpan sinyal RGB (OpenCV membaca B,G,R jadi kita simpan sesuai)
        self.b.append(b_mean)
        self.g.append(g_mean)
        self.r.append(r_mean)

        # Batasi panjang buffer sinyal (misalnya 30 detik * fps)
        max_len = self.fps * 30 
        if len(self.g) > max_len:
            self.r.pop(0)
            self.g.pop(0)
            self.b.pop(0)
        
        # (Opsional) Hitung sinyal POS di sini jika ingin selalu update per frame
        # self.update_processed_rppg_signal()


    def get_forehead_rect(self):
        return self.last_forehead_rect

    # Hapus salah satu get_forehead_rect jika ada duplikat

    def get_rgb_signals(self):
        # Mengembalikan dalam urutan R, G, B untuk konsistensi jika ada yang pakai
        return np.array([self.r, self.g, self.b]).reshape(1, 3, -1)

    def compute_pos(self, rgb_signal_window): # Terima window sinyal RGB
        """
        Menghitung sinyal rPPG menggunakan metode POS.
        rgb_signal_window: array numpy dengan shape (3, N_samples) -> R, G, B
        """
        if rgb_signal_window.shape[1] < int(1.6 * self.fps) + 1 : # Butuh sampel yang cukup untuk window POS
            # print("DEBUG POS: Sampel tidak cukup untuk compute_pos")
            return np.array([]) # Kembalikan array kosong jika tidak cukup sampel
            
        # Transpose agar shape jadi (N_samples, 3)
        # C_normalized = rgb_signal_window.T 
        # Normalisasi per channel
        # C_normalized = C_normalized / (np.mean(C_normalized, axis=0) + 1e-9)
        # C_normalized = C_normalized.T # Kembalikan ke (3, N_samples)
        
        # Implementasi POS dari kodemu (sedikit disesuaikan agar lebih mandiri)
        # Asumsi rgb_signal_window adalah (1, 3, N_samples) seperti dari get_rgb_signals
        # atau (3, N_samples)
        
        signal_for_pos = rgb_signal_window
        if signal_for_pos.ndim == 2: # Jika (3, N) ubah ke (1, 3, N)
            signal_for_pos = np.expand_dims(signal_for_pos, axis=0)

        eps = 1e-9
        e, c, f = signal_for_pos.shape # e=1, c=3, f=N_samples
        w = int(1.6 * self.fps) # Ukuran window untuk POS
        
        if f < w + 1 : # Perlu dicek lagi
            # print(f"DEBUG POS: f ({f}) < w+1 ({w+1}), sampel tidak cukup")
            return np.array([])

        P = np.array([[0, 1, -1], [-2, 1, 1]]) # Matriks proyeksi
        # Q = np.stack([P for _ in range(e)], axis=0) # e selalu 1 di sini
        Q = P # Karena e=1

        H = np.zeros(f) # Sinyal hasil POS akan 1D

        for n in np.arange(w, f):
            m = n - w + 1
            Cn_segment = signal_for_pos[0, :, m:(n + 1)] # Ambil segmen (3, w)
            
            # Normalisasi temporal per window
            mean_Cn_segment = np.mean(Cn_segment, axis=1, keepdims=True)
            if np.any(np.abs(mean_Cn_segment) < eps): # Hindari division by zero
                continue
            normalized_Cn_segment = Cn_segment / (mean_Cn_segment + eps)
            
            S = np.dot(Q, normalized_Cn_segment) # Hasilnya (2, w)
            
            # S1 dan S2 adalah baris dari S
            S1 = S[0, :]
            S2 = S[1, :]
            
            # Hindari std deviasi nol
            std_S1 = np.std(S1)
            std_S2 = np.std(S2)
            if std_S2 < eps:
                alpha = 0 # Atau handle lain, misal alpha = std_S1 / eps
            else:
                alpha = std_S1 / std_S2
            
            H_segment = S1 + alpha * S2
            
            # Detrend H_segment (opsional, tapi umum dilakukan)
            # H_segment_detrended = H_segment - np.mean(H_segment)
            # H[m:(n + 1)] += H_segment_detrended # Atau gabungkan dengan cara lain
            H[n] = H_segment[-1] # Ambil nilai terakhir dari window ini sebagai output POS saat itu
                                  # Atau rata-rata, atau nilai tengah. Ini perlu riset/eksperimen.
                                  # Untuk sinyal yang diakumulasi, += H_segment mungkin lebih tepat,
                                  # tapi H.reshape(-1) di akhir mungkin jadi salah.
                                  # Jika H adalah hasil akhir, maka H[n] = ... lebih masuk akal.
        
        # Jika H diakumulasi, maka perlu normalisasi atau pemotongan awal.
        # Untuk sekarang, kita anggap H[n] adalah output POS per frame (setelah window awal).
        # Kembalikan bagian yang sudah dihitung (mulai dari w)
        return H[w:]


    def update_processed_rppg_signal(self, num_samples_for_pos=None):
        """Method untuk menghitung dan menyimpan sinyal POS."""
        if num_samples_for_pos is None:
            num_samples_for_pos = self.fps * 10 # Proses 10 detik data terakhir untuk POS
        
        if len(self.g) < num_samples_for_pos:
            self.processed_rppg_signal = [] # Atau biarkan yang lama jika data baru sedikit
            return

        # Ambil data RGB terakhir
        # Urutan R, G, B untuk POS jika matriks P dirancang untuk itu.
        # Jika OpenCV BGR disimpan di self.b, self.g, self.r, maka:
        # r_segment = np.array(self.r[-num_samples_for_pos:])
        # g_segment = np.array(self.g[-num_samples_for_pos:])
        # b_segment = np.array(self.b[-num_samples_for_pos:])
        # rgb_data = np.array([r_segment, g_segment, b_segment])
        
        # Jika kita simpan B,G,R (sesuai mean OpenCV) dan P=[[0,1,-1],[-2,1,1]]
        # P[0] = G - B (atau G - R jika urutan RGB)
        # P[1] = -2B + G + R (atau -2R + G + B jika urutan RGB)
        # Kita perlu konsisten. Jika mean_roi[:,:,2] adalah R, mean_roi[:,:,1] adalah G, mean_roi[:,:,0] adalah B
        # maka kita sudah menyimpan R, G, B.
        
        r_val = np.array(self.r[-num_samples_for_pos:])
        g_val = np.array(self.g[-num_samples_for_pos:])
        b_val = np.array(self.b[-num_samples_for_pos:])
        
        # Pastikan semua channel punya panjang sama
        min_len = min(len(r_val), len(g_val), len(b_val))
        if min_len < 1:
            self.processed_rppg_signal = []
            return
            
        rgb_for_pos = np.array([
            r_val[-min_len:],
            g_val[-min_len:],
            b_val[-min_len:]
        ]) # Shape (3, min_len)

        self.processed_rppg_signal = self.compute_pos(rgb_for_pos)
        # print(f"DEBUG: Sinyal POS diupdate, panjang: {len(self.processed_rppg_signal)}")


    # --- METHOD BARU UNTUK GUI ---
    def get_latest_signal_chunk(self, num_samples=200):
        """Mengembalikan N sampel terakhir dari sinyal rPPG yang sudah diproses (POS)."""
        # Panggil update_processed_rppg_signal dulu untuk memastikan sinyal POS terbaru
        self.update_processed_rppg_signal(num_samples_for_pos=num_samples + int(1.6 * self.fps) + 5) # Butuh lebih banyak sampel mentah untuk POS

        if hasattr(self, 'processed_rppg_signal') and len(self.processed_rppg_signal) > 0:
            return self.processed_rppg_signal[-num_samples:]
        # Fallback ke sinyal hijau jika sinyal POS belum ada atau kosong
        elif hasattr(self, 'g') and self.g:
            print("PERINGATAN rppg_processor: Menggunakan sinyal G mentah untuk plot.")
            return self.g[-num_samples:]
        return []

    def get_current_hr(self, window_size_seconds=10):
        """Menghitung dan mengembalikan HR saat ini."""
        # Pastikan sinyal POS terbaru sudah dihitung
        # Window untuk POS mungkin perlu lebih panjang dari window untuk HR agar stabil
        self.update_processed_rppg_signal(num_samples_for_pos=self.fps * (window_size_seconds + 5))

        signal_to_process = self.processed_rppg_signal
        
        required_samples_for_hr = int(window_size_seconds * self.fps)

        if not SIGNAL_UTILS_AVAILABLE:
            print("PERINGATAN rppg_processor: signal_utils tidak tersedia, get_current_hr mengembalikan None.")
            return None 
            
        if len(signal_to_process) < required_samples_for_hr:
            # print(f"DEBUG RPPG HR: Data sinyal POS belum cukup ({len(signal_to_process)}/{required_samples_for_hr})")
            return None

        current_signal_window = np.array(signal_to_process[-required_samples_for_hr:])

        try:
            # Frekuensi untuk HR adalah FPS dari sinyal POS, yang sama dengan FPS video
            # Frekuensi rPPG biasanya antara 0.75 Hz (45 BPM) dan 3.0 Hz (180 BPM) atau 4.0 Hz (240 BPM)
            # Untuk amannya, kita bisa filter sedikit lebih lebar, misal 0.7 Hz - 4.0 Hz
            # Sesuaikan rentang frekuensi ini!
            filtered_signal = bandpass_filter(current_signal_window, fs=self.fps, low=0.7, high=3.5, order=3)
            
            # calculate_heart_rate seharusnya mengembalikan bpm dan peaks
            hr_bpm, peaks = calculate_heart_rate(filtered_signal, fs=self.fps)
            
            if hr_bpm is not None and 40 <= hr_bpm <= 200: # Validasi rentang HR
                # print(f"DEBUG RPPG HR: Terhitung HR = {hr_bpm:.1f} BPM")
                return hr_bpm
            else:
                # print(f"DEBUG RPPG HR: HR hasil kalkulasi ({hr_bpm}) di luar rentang wajar.")
                return None
        except Exception as e:
            print(f"ERROR di RPPGProcessor get_current_hr: {e}")
            import traceback
            traceback.print_exc()
            return None