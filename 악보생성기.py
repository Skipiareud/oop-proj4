import librosa
import numpy as np
import random
from scipy.signal import butter, sosfilt

AUDIO_PATH = "entrance.wav"

# 난이도 조절용 파라미터
DIFFICULTY_MULTIPLIER = 2.0   # 2~5 정도 추천, 더 올리면 진짜 지옥
SUBDIVISION = 4               # 4=16분, 8=32분 단위 스냅
MIN_INTERVAL = 0.02           # 같은 타이밍 사이 최소 간격(초) – 작을수록 더 빽빽
STRONG_KEEP_Q = 0.15          # 상위 몇 %만 "강한 온셋"으로 볼지 (낮을수록 더 많이 남김)

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
# 3. HPSS (harmonic / percussive)
# ----------------------------------------
y_harm, y_perc = librosa.effects.hpss(y)

# ----------------------------------------
# 4. Band-pass for melody (300~3000 Hz)
# ----------------------------------------
def bandpass_filter(x, sr, low=300, high=3000, order=4):
    sos = butter(order, [low, high], "bandpass", fs=sr, output="sos")
    return sosfilt(sos, x)

y_mel = bandpass_filter(y_harm, sr)

# ----------------------------------------
# 5. Onsets: 멜로디 + 퍼커션 둘 다 추출
# ----------------------------------------
mel_on_frames = librosa.onset.onset_detect(y=y_mel, sr=sr, backtrack=True,
                                           pre_max=8, post_max=8)
mel_on_times = librosa.frames_to_time(mel_on_frames, sr=sr)
mel_env = librosa.onset.onset_strength(y=y_mel, sr=sr)
mel_strengths = mel_env[mel_on_frames]

perc_on_frames = librosa.onset.onset_detect(y=y_perc, sr=sr, backtrack=True,
                                            pre_max=8, post_max=8)
perc_on_times = librosa.frames_to_time(perc_on_frames, sr=sr)
perc_env = librosa.onset.onset_strength(y=y_perc, sr=sr)
perc_strengths = perc_env[perc_on_frames]

# 강한 온셋 threshold (멜로디/퍼커션 각각 따로)
mel_th = np.quantile(mel_strengths, STRONG_KEEP_Q)
perc_th = np.quantile(perc_strengths, STRONG_KEEP_Q)

cand_times = []

# 멜로디 쪽 온셋 – 강한건 무조건, 약한 것도 약간 섞기
for t, s in zip(mel_on_times, mel_strengths):
    weight = 1.0 if s >= mel_th else 0.3
    # weight 기반으로 몇 번 넣을지 결정 (난이도 곱)
    count = max(1, int(weight * DIFFICULTY_MULTIPLIER))
    for _ in range(count):
        cand_times.append(t)

# 퍼커션 쪽 온셋 – 리듬 강화
for t, s in zip(perc_on_times, perc_strengths):
    weight = 0.8 if s >= perc_th else 0.2
    count = max(1, int(weight * DIFFICULTY_MULTIPLIER))
    for _ in range(count):
        cand_times.append(t)

cand_times = np.array(cand_times)

# ----------------------------------------
# 6. beat grid 기반로도 노트 추가 (빈 구간 채우기)
# ----------------------------------------
# 예: 모든 박자 + 8분 위치에 기본 노트 후보 추가
for bt in beat_times:
    cand_times = np.append(cand_times, [bt, bt + seconds_per_beat * 0.5])

# ----------------------------------------
# 7. Snap to grid (SUBDIVISION 단위)
# ----------------------------------------
def snap(t, subdiv=SUBDIVISION):
    idx = t / seconds_per_beat
    snap_idx = round(idx * subdiv) / subdiv
    return snap_idx * seconds_per_beat

snapped = np.array([snap(t) for t in cand_times])
snapped = snapped[(snapped > 0.05)]  # 아주 초반 노이즈 제거
snapped = np.sort(snapped)

# 너무 가까운 것 병합
merged = []
for t in snapped:
    if not merged or abs(t - merged[-1]) > MIN_INTERVAL:
        merged.append(t)
snapped = np.array(merged)

# ----------------------------------------
# 8. Pitch tracking (멜로디 라인 기준 lane 배치)
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
    # 멜로디 음 높이에 따른 기본 레인
    if p is None:
        return random.choice([1, 2])
    if p < 400:   # 낮은 음
        return 0
    elif p < 800: # 중저
        return 1
    elif p < 1200: # 중고
        return 2
    else:         # 아주 높은 음
        return 3

# ----------------------------------------
# 9. 고난도 패턴 설계 (점프, 코드, 트릴 추가)
# ----------------------------------------
chart = []
start_delay = 1.5

for i, t in enumerate(snapped):
    p = estimate_pitch_at(t)
    base_lane = pitch_to_base_lane(p)

    # 기본 노트
    lanes = [base_lane]

    # 확률적으로 코드/점프 추가
    r = random.random()

    if r < 0.25:
        # 양손 코드 (좌우)
        if base_lane <= 1:
            lanes.append(base_lane + 2)
        else:
            lanes.append(base_lane - 2)
    elif r < 0.45:
        # 인접 레인 트릴 느낌 (빠른 근접 노트)
        if base_lane > 0 and base_lane < 3:
            lanes.append(base_lane - 1 if random.random() < 0.5 else base_lane + 1)
    elif r < 0.55:
        # 3개 코드 (클라이맥스 느낌)
        all_lanes = [0, 1, 2, 3]
        random.shuffle(all_lanes)
        lanes = sorted(all_lanes[:3])

    # 레인 중복 제거
    lanes = sorted(set(lanes))

    # 시간/딜레이 적용
    for lane in lanes:
        chart.append((lane, round(t + start_delay, 3)))

    # 추가 트릴/연타: 일정 확률로 바로 뒤에 같은/인접 레인 한 번 더
    if random.random() < 0.20:
        dt = seconds_per_beat / SUBDIVISION  # 32분 하나 정도 뒤
        t2 = t + dt
        lane2 = lanes[-1] if random.random() < 0.5 else random.choice([0, 1, 2, 3])
        chart.append((lane2, round(t2 + start_delay, 3)))

# 시간 기준으로 정렬
chart.sort(key=lambda x: x[1])

# ----------------------------------------
# 10. 출력: 10개씩 정렬해서 출력
# ----------------------------------------
print("\nSong(")
print('    "Entrance (Deemo ver.)",')
print('    "entrance.wav",')
print(f"    bpm={tempo:.2f},")
print(f"    start_delay={start_delay},")
print("    chart=[")

for i, (lane, t) in enumerate(chart):
    comma = "," if i < len(chart) - 1 else ""
    # 한 줄에 10개씩
    if i % 10 == 0:
        print("        ", end="")
    print(f"({lane}, {t}){comma} ", end="")
    if (i + 1) % 10 == 0:
        print()
print()
print("    ],")
print(")")

