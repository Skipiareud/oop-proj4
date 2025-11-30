import random
from typing import List, Tuple

import numpy as np
import pygame

from models import Song


class OnsetDetector:
    """Spectral-flux onset detector using pygame audio array."""

    def detect(self, path: str) -> List[float]:
        snd = pygame.mixer.Sound(path)
        freq, _, _ = pygame.mixer.get_init()
        data = pygame.sndarray.array(snd).astype(np.float32)
        if data.ndim == 2:
            data = data.mean(axis=1)
        maxv = np.max(np.abs(data))
        if maxv > 0:
            data /= maxv
        frame = 2048
        hop = 512
        hann = np.hanning(frame)
        flux_values: List[float] = []
        positions: List[int] = []
        pos = 0
        prev_mag = None
        while pos + frame < len(data):
            window = data[pos : pos + frame] * hann
            spectrum = np.fft.rfft(window)
            mag = np.abs(spectrum)
            if prev_mag is not None:
                diff = mag - prev_mag
                flux = np.sum(np.clip(diff, 0, None))
                flux_values.append(float(flux))
                positions.append(pos)
            prev_mag = mag
            pos += hop
        if not flux_values:
            return []
        flux_arr = np.asarray(flux_values)
        # Adaptive threshold: lower threshold for higher difficulty by caller
        # We keep detector pure; selection handles density.
        thresh = np.median(flux_arr) + 0.6 * np.std(flux_arr)
        peaks: List[int] = []
        last_idx = -10
        for i, val in enumerate(flux_arr):
            if val < thresh or i - last_idx < 2:  # small local refractory in frames
                continue
            left = flux_arr[i - 1] if i > 0 else val
            right = flux_arr[i + 1] if i + 1 < len(flux_arr) else val
            if val >= left and val >= right:
                peaks.append(i)
                last_idx = i
        times = [((positions[idx] + frame // 2) / freq) for idx in peaks]
        return times


def quantize_onsets(times: List[float], bpm: int, divisions: int = 4) -> List[float]:
    if bpm <= 0 or not times:
        return times
    beat = 60.0 / bpm
    grid = beat / divisions
    return [round(t / grid) * grid for t in times]


def _filter_density(times: List[float], difficulty: float) -> List[float]:
    """Adjust density by difficulty: higher difficulty -> more notes, smaller gaps."""
    if not times:
        return times
    times = sorted(times)
    # min gap shrinks with difficulty
    min_gap = max(0.08, 0.18 - 0.05 * (difficulty - 1))
    keep: List[float] = []
    last_t = -1e9
    for t in times:
        if t - last_t < min_gap:
            continue
        keep.append(t)
        last_t = t
    # If still too dense/sparse, randomly drop/add slightly
    rng = random.Random(len(times))
    target_mult = difficulty
    if target_mult < 1.0:
        drop_prob = min(0.6, 0.2 + (1.0 - target_mult))
        keep = [t for t in keep if rng.random() > drop_prob]
    elif target_mult > 1.0:
        # Duplicate occasional notes for chords/extra hits
        extras: List[float] = []
        for t in keep:
            if rng.random() < 0.15 * (target_mult - 1.0):
                extras.append(t + rng.uniform(-0.02, 0.02))
        keep.extend(extras)
        keep.sort()
    return keep


def map_onsets_to_lanes(times: List[float], seed: int, difficulty: float) -> List[Tuple[int, float]]:
    times = _filter_density(times, difficulty)
    rng = random.Random(seed)
    chart: List[Tuple[int, float]] = []
    prev_lane = rng.randrange(4) if times else 0
    for i, t in enumerate(times):
        candidates = list(range(4))
        if rng.random() < 0.7 and prev_lane in candidates and len(candidates) > 1:
            candidates.remove(prev_lane)
        lane = rng.choice(candidates)
        prev_lane = lane
        chart.append((lane, t))
        # Add chord when close timing and higher difficulty
        if i > 0 and times[i] - times[i - 1] < 0.22 and rng.random() < 0.35 * difficulty:
            chord_lane = rng.choice([l for l in range(4) if l != lane])
            chart.append((chord_lane, t))
    return chart


class ProceduralChartGenerator:
    """Fallback beat-based chart."""

    def generate(self, song: Song) -> List[Tuple[int, float]]:
        beat = 60.0 / song.bpm
        rng = random.Random(abs(hash(song.name)) & 0xFFFFFFFF)
        density = max(0.2, min(1.5, song.difficulty))
        t = beat
        chart: List[Tuple[int, float]] = []
        while t < song.length_hint:
            lane = rng.randrange(4)
            chart.append((lane, t))
            if rng.random() < 0.2 * density:
                chord_lane = rng.randrange(4)
                if chord_lane != lane:
                    chart.append((chord_lane, t))
            hop = beat / 2 if rng.random() < 0.35 * density else beat
            t += hop
        return chart


class OnsetChartGenerator:
    def __init__(self, detector: OnsetDetector, fallback: ProceduralChartGenerator):
        self.detector = detector
        self.fallback = fallback

    def generate(self, song: Song) -> Tuple[List[Tuple[int, float]], str]:
        try:
            onsets = self.detector.detect(song.path)
        except Exception as exc:
            print(f"[warn] onset detection failed: {exc}")
            onsets = []
        if onsets and len(onsets) >= 5:
            seed = abs(hash(song.name + song.path)) & 0xFFFFFFFF
            times = quantize_onsets(onsets, song.bpm)
            times = [max(0.0, t + song.chart_offset) for t in times]
            chart = map_onsets_to_lanes(times, seed=seed, difficulty=song.difficulty)
            end_time = max(t for _, t in chart) if chart else song.length_hint
            song.length_hint = max(song.length_hint, end_time)
            return chart, "onset"
        return self.fallback.generate(song), "procedural"
