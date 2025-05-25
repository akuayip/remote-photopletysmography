# main.py

import cv2
from rppg_processor import RPPGProcessor
from signal_utils import bandpass_filter, calculate_heart_rate
from visualization import plot_signal_with_peaks

def main():
    rppg = RPPGProcessor(fps=30)
    cap = cv2.VideoCapture(0)

    frame_count = 0
    max_frames = 300  # 10 detik

    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        rppg.extract_rgb_from_frame(frame)
        cv2.imshow("Live Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()

    rgb_signals = rppg.get_rgb_signals()
    rppg_raw = rppg.compute_pos(rgb_signals)
    rppg_filtered = bandpass_filter(rppg_raw)

    hr, peaks = calculate_heart_rate(rppg_filtered)
    plot_signal_with_peaks(rppg_filtered, peaks, hr)

if __name__ == '__main__':
    main()
