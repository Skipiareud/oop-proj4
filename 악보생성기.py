import librosa
import numpy as np
import random

AUDIO_PATH = "entrance.wav"

# ----------------------------------------
# 1. Load Wave
# ----------------------------------------
y, sr = librosa.load(AUDIO_PATH, sr=None, mono=True)

# ----------------------------------------
# 2. BPM & Beat Tracking
# ----------------------------------------
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
if isinstance(tempo, np.ndarray):
    tempo = float(tempo.mean())
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

seconds_per_beat = 60.0 / tempo

print(f"[INFO] BPM Detected: {tempo:.2f}")

# ----------------------------------------
# 3. HPSS Harmonic/Percussive separation
# ----------------------------------------
y_harmonic, y_percussive = librosa.effects.hpss(y)

# ----------------------------------------
# 4. Melody Band-pass Filtering (300Hz ~ 3000Hz)
# ----------------------------------------
from scipy.signal import butter, sosfilt

def bandpass_filter(x, sr, low=300, high=3000, order=4):
    sos = butter(order, [low, high], "bandpass", fs=sr, output="sos")
    return sosfilt(sos, x)

y_melody = bandpass_filter(y_harmonic, sr)

# ----------------------------------------
# 5. Onset detection (melody only)
# ----------------------------------------
onset_frames = librosa.onset.onset_detect(y=y_melody, sr=sr, backtrack=True, pre_max=10, post_max=10)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)

# Strength
onset_env = librosa.onset.onset_strength(y=y_melody, sr=sr)
strengths = onset_env[onset_frames]

# Keep strong notes (top 60%)
threshold = np.quantile(strengths, 0.40)
strong_onsets = []
for t, s in zip(onset_times, strengths):
    if s >= threshold:
        strong_onsets.append(t)

# ----------------------------------------
# 6. Snap to grid (16th or 32nd)
# ----------------------------------------
def snap(t, subdiv=4):  # subdiv=4 => 16th
    idx = t / seconds_per_beat
    snap_idx = round(idx * subdiv) / subdiv
    return snap_idx * seconds_per_beat

snapped_onsets = np.array(sorted({snap(t, subdiv=4) for t in strong_onsets}))

# ----------------------------------------
# 7. Remove too-close events (< 40ms)
# ----------------------------------------
filtered = []
for t in snapped_onsets:
    if not filtered or abs(t - filtered[-1]) > 0.04:
        filtered.append(t)

# ----------------------------------------
# 8. Pitch tracking to determine lane
# ----------------------------------------
pitches, mags = librosa.piptrack(y=y_melody, sr=sr)
pitch_times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr)

def estimate_pitch(t):
    idx = np.argmin(abs(pitch_times - t))
    col = pitches[:, idx]
    if col.max() < 1e-3:
        return None
    mag_col = mags[:, idx]
    mask = mag_col > 0.6 * mag_col.max()
    if np.any(mask):
        return float(col[mask].mean())
    return float(col[np.argmax(mag_col)])

def lane_from_pitch(p):
    if p is None:
        return random.choice([1, 2])
    if p < 400: return 0
    if p < 800: return 1
    if p < 1200: return 2
    return 3

# ----------------------------------------
# 9. Generate chart
# ----------------------------------------
chart = []
start_delay = 1.5

for t in filtered:
    lane = lane_from_pitch(estimate_pitch(t))
    chart.append((lane, round(t + start_delay, 3)))

# ----------------------------------------
# 10. Print chart neatly in groups of 10
# ----------------------------------------
print("\nSong(")
print('    "Entrance (Deemo ver.)",')
print('    "entrance.wav",')
print(f"    bpm={tempo:.2f},")
print(f"    start_delay={start_delay},")
print("    chart=[")

for i, (lane, time) in enumerate(chart):
    end = "," if i < len(chart)-1 else ""
    print(f"        ({lane}, {time}){end}", end="")
    if (i+1) % 10 == 0:
        print()
    else:
        print(" ", end="")
print("\n    ],")
print(")")