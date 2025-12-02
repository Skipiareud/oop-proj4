import librosa
import numpy as np
import random
from scipy.signal import butter, sosfilt

# ----------------------------------------
# ★ 사용자가 직접 입력하는 값들 ★
# ----------------------------------------

AUDIO_PATH = "tensi.mp3"

BPM = 128              # ← 너가 직접 지정하는 BPM
START_DELAY = 1.5        # ← 너가 직접 주는 Delay
DIFFICULTY_MULTIPLIER = 2.0
SUBDIVISION = 4          # 4=16분, 8=32분
MIN_INTERVAL = 0.02
STRONG_KEEP_Q = 0.15     # 상위 몇 % 온셋을 "강하게" 처리할지

# ----------------------------------------
# 1. Load Wave
# ----------------------------------------
y, sr = librosa.load(AUDIO_PATH, sr=None, mono=True)

# ----------------------------------------
# 2. BPM 관련 계산 (직접 입력한 BPM 사용)
# ----------------------------------------
seconds_per_beat = 60.0 / BPM
print(f"[INFO] Using custom BPM: {BPM}")

# ----------------------------------------
# 3. HPSS
# ----------------------------------------
y_harm, y_perc = librosa.effects.hpss(y)

# ----------------------------------------
# 4. Band-pass for melody
# ----------------------------------------
def bandpass_filter(x, sr, low=300, high=3000, order=4):
    sos = butter(order, [low, high], "bandpass", fs=sr, output="sos")
    return sosfilt(sos, x)

y_mel = bandpass_filter(y_harm, sr)

# ----------------------------------------
# 5. Onsets (멜로디 & 퍼커션)
# ----------------------------------------
mel_on_frames = librosa.onset.onset_detect(y=y_mel, sr=sr, backtrack=True)
mel_on_times = librosa.frames_to_time(mel_on_frames, sr=sr)
mel_env = librosa.onset.onset_strength(y=y_mel, sr=sr)
mel_strengths = mel_env[mel_on_frames]

perc_on_frames = librosa.onset.onset_detect(y=y_perc, sr=sr, backtrack=True)
perc_on_times = librosa.frames_to_time(perc_on_frames, sr=sr)
perc_env = librosa.onset.onset_strength(y=y_perc, sr=sr)
perc_strengths = perc_env[perc_on_frames]

mel_th = np.quantile(mel_strengths, STRONG_KEEP_Q)
perc_th = np.quantile(perc_strengths, STRONG_KEEP_Q)

cand_times = []

# 멜로디
for t, s in zip(mel_on_times, mel_strengths):
    w = 1.0 if s >= mel_th else 0.3
    count = max(1, int(w * DIFFICULTY_MULTIPLIER))
    cand_times += [t] * count

# 퍼커션
for t, s in zip(perc_on_times, perc_strengths):
    w = 0.8 if s >= perc_th else 0.2
    count = max(1, int(w * DIFFICULTY_MULTIPLIER))
    cand_times += [t] * count

cand_times = np.array(cand_times)

# ----------------------------------------
# 6. Beat grid 추가 (사용자 BPM 기반)
# ----------------------------------------
duration = librosa.get_duration(y=y, sr=sr)
t = 0.0
while t < duration:
    cand_times = np.append(cand_times, t)
    # 8분음표 추가
    cand_times = np.append(cand_times, t + seconds_per_beat * 0.5)
    t += seconds_per_beat

# ----------------------------------------
# 7. Snap to Grid
# ----------------------------------------
def snap(t, subdiv=SUBDIVISION):
    idx = t / seconds_per_beat
    snap_idx = round(idx * subdiv) / subdiv
    return snap_idx * seconds_per_beat

snapped = np.sort(np.array([snap(t) for t in cand_times]))
snapped = snapped[snapped > 0.05]

# 가까운 노트 병합
merged = []
for t in snapped:
    if not merged or abs(t - merged[-1]) > MIN_INTERVAL:
        merged.append(t)
snapped = np.array(merged)

# ----------------------------------------
# 8. Pitch-to-lane
# ----------------------------------------
pitches, mags = librosa.piptrack(y=y_mel, sr=sr)
pitch_times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sr)

def estimate_pitch_at(t):
    idx = np.argmin(np.abs(pitch_times - t))
    col = pitches[:, idx]
    if col.max() < 1e-3:
        return None
    mag_col = mags[:, idx]
    mask = mag_col > 0.5 * mag_col.max()
    if np.any(mask):
        return float(col[mask].mean())
    return float(col[np.argmax(mag_col)])

def pitch_to_base_lane(p):
    if p is None:
        return random.choice([1, 2])
    if p < 400:
        return 0
    elif p < 800:
        return 1
    elif p < 1200:
        return 2
    else:
        return 3

# ----------------------------------------
# 9. 패턴 생성
# ----------------------------------------
chart = []

for i, t in enumerate(snapped):
    base_lane = pitch_to_base_lane(estimate_pitch_at(t))
    lanes = [base_lane]

    r = random.random()

    if r < 0.25:
        # 코드
        if base_lane <= 1:
            lanes.append(base_lane + 2)
        else:
            lanes.append(base_lane - 2)

    elif r < 0.45:
        # 인접 레인
        if base_lane > 0 and base_lane < 3:
            lanes.append(base_lane + (1 if random.random() < 0.5 else -1))

    elif r < 0.55:
        # 3코드
        all_l = [0, 1, 2, 3]
        random.shuffle(all_l)
        lanes = all_l[:3]

    lanes = sorted(set(lanes))

    # 딜레이 적용
    for lane in lanes:
        chart.append((lane, round(t + START_DELAY, 3)))

    # 추가 연타
    if random.random() < 0.20:
        dt = seconds_per_beat / SUBDIVISION
        lane2 = lanes[-1] if random.random() < 0.5 else random.choice([0,1,2,3])
        chart.append((lane2, round(t + dt + START_DELAY, 3)))

chart.sort(key=lambda x: x[1])

# ----------------------------------------
# 10. 출력
# ----------------------------------------
print("\nSong(")
print('    "Entrance (Custom)",')
print('    "entrance.wav",')
print(f"    bpm={BPM},")
print(f"    start_delay={START_DELAY},")
print("    chart=[")

for i, (lane, t) in enumerate(chart):
    comma = "," if i < len(chart) - 1 else ""
    if i % 10 == 0:
        print("        ", end="")
    print(f"({lane}, {t}){comma} ", end="")
    if (i + 1) % 10 == 0:
        print()
print("\n    ],")
print(")")