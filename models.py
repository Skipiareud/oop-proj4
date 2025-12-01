from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame


@dataclass
class Song:
    name: str
    path: str
    bpm: int
    offset: float = 0.0  # audio alignment
    chart_offset: float = 0.0  # fine tune for chart timing
    difficulty: float = 1.0  # density multiplier
    length_hint: float = 60.0
    start_delay: float = 2.5  # lead-in seconds
    chart: Optional[List[Tuple[int, float]]] = None  # optional manual chart (lane, time)


@dataclass
class Note:
    lane: int
    time: float
    hit: bool = False
    missed: bool = False

    def y(self, now: float, hit_y: float, speed: float) -> float:
        return hit_y - (self.time - now) * speed


class Track:
    def __init__(self, name: str, x: int, width: int, keys: Dict[int, int], color: Tuple[int, int, int]):
        self.name = name
        self.x = x
        self.width = width
        self.keys = keys
        self.color = color
        self.notes: List[Note] = []
        self.last_label: str = "Ready"
        self.last_label_time: float = 0.0
        self.last_press: Dict[int, float] = {}
        self.first_note_time: float = 0.0
        self.score: int = 0
        self.combo: int = 0

    def load_chart(self, chart: List[Tuple[int, float]]) -> None:
        self.notes = [Note(lane, time) for lane, time in chart]
        self.score = 0
        self.combo = 0
        self.last_label = "Ready"
        self.last_label_time = 0.0
        self.last_press = {}
        self.first_note_time = min((n.time for n in self.notes), default=0.0)

    def handle_key(self, key: int, now: float) -> None:
        if key not in self.keys:
            return
        lane = self.keys[key]
        self.last_press[lane] = now
        note = self._closest_pending_note(lane)
        if note is None:
            self.last_label = "Miss"
            self.last_label_time = now
            self.combo = 0
            return
        delta = abs(note.time - now)
        windows = [(0.08, "Perfect", 1000), (0.16, "Great", 700), (0.25, "Good", 400)]
        for limit, label, points in windows:
            if delta <= limit:
                note.hit = True
                self.score += points + self.combo * 5
                self.combo += 1
                self.last_label = label
                self.last_label_time = now
                return
        if now > note.time:
            note.missed = True
            self.last_label = "Miss"
            self.last_label_time = now
            self.combo = 0

    def update_misses(self, now: float, drop_after: float = 0.3) -> None:
        for note in self.notes:
            if not note.hit and not note.missed and now - note.time > drop_after:
                note.missed = True
                self.last_label = "Miss"
                self.last_label_time = now
                self.combo = 0

    def draw(self, screen: pygame.Surface, now: float, hit_y: float, speed: float) -> None:
        lane_w = self.width // 4
        lane_color = (*[c // 2 for c in self.color], 180)
        glow_age = now - self.last_label_time
        glow_strength = max(0.0, 1.0 - glow_age / 0.4)
        for lane in range(4):
            x = self.x + lane * lane_w
            pygame.draw.rect(screen, lane_color, (x + 4, 0, lane_w - 8, screen.get_height()), border_radius=8)
            press_age = now - self.last_press.get(lane, -999)
            if press_age < 0.18:
                alpha = int(160 * (1 - press_age / 0.18))
                overlay = pygame.Surface((lane_w - 8, 26), pygame.SRCALPHA)
                overlay.fill((*self.color, alpha))
                screen.blit(overlay, (x + 4, hit_y - 10))
        base_bar_height = 6 + int(12 * glow_strength)
        pygame.draw.rect(screen, self.color, (self.x, hit_y, self.width, base_bar_height), border_radius=4)
        for note in self.notes:
            if note.hit or note.missed:
                continue
            y = note.y(now, hit_y, speed)
            if -80 < y < screen.get_height() + 40:
                lane_x = self.x + note.lane * lane_w + 6
                pygame.draw.rect(screen, self.color, (lane_x, y, lane_w - 12, 24), border_radius=6)

    def _closest_pending_note(self, lane: int) -> Optional[Note]:
        pending = [n for n in self.notes if n.lane == lane and not n.hit and not n.missed]
        if not pending:
            return None
        return min(pending, key=lambda n: n.time)

    def finished(self) -> bool:
        return all(n.hit or n.missed for n in self.notes)
