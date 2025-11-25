"""
Simple two-player rhythm game prototype (object-oriented, pygame).
Both players share the same song/chart; screen is split vertically.
Each player has health; when the opponent hits a 10-combo multiple,
damage is applied. Press ESC to quit.

Dependencies:
- pygame (install with `pip install pygame`)
Assets:
- Drop your audio to assets/song.ogg (or update AUDIO_PATH).
- Put a background image at assets/bg.png (optional).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

import pygame


SCREEN_W, SCREEN_H = 1000, 700
LANE_COUNT = 4
HIT_LINE_Y = int(SCREEN_H * 0.8)
NOTE_SPEED = 0.35  # pixels per ms
HIT_WINDOW_MS = 120
COMBO_DAMAGE = 5

ROOT = Path(__file__).parent
ASSET_DIR = ROOT / "assets"
AUDIO_PATH = ASSET_DIR / "song.ogg"


@dataclass
class Note:
    time_ms: int
    lane: int
    hit: bool = False

    def y_at(self, song_ms: int) -> float:
        dt = song_ms - self.time_ms
        return dt * NOTE_SPEED


@dataclass
class Lane:
    index: int
    key: int
    x: int
    width: int
    color: pygame.Color
    notes: List[Note] = field(default_factory=list)

    def spawn_notes(self, chart: Sequence[Note]) -> None:
        self.notes = [n for n in chart if n.lane == self.index]

    def next_hittable(self, song_ms: int) -> Note | None:
        for note in self.notes:
            if note.hit:
                continue
            if abs(song_ms - note.time_ms) <= HIT_WINDOW_MS:
                return note
            if note.time_ms > song_ms + HIT_WINDOW_MS:
                break
        return None

    def remove_passed(self, song_ms: int) -> bool:
        """Remove notes that went too far; returns True if a miss happened."""
        missed = False
        while self.notes and not self.notes[0].hit:
            note = self.notes[0]
            if song_ms - note.time_ms > HIT_WINDOW_MS:
                missed = True
                self.notes.pop(0)
            else:
                break
        return missed

    def draw(self, surf: pygame.Surface, song_ms: int) -> None:
        pygame.draw.rect(surf, self.color, (self.x, 0, self.width, SCREEN_H), 2)
        for note in self.notes:
            if note.hit:
                continue
            y = note.y_at(song_ms)
            if y > SCREEN_H:
                continue
            pygame.draw.rect(
                surf,
                self.color,
                (self.x + 6, y, self.width - 12, 24),
                border_radius=6,
            )
        pygame.draw.line(
            surf, pygame.Color("yellow"), (self.x, HIT_LINE_Y), (self.x + self.width, HIT_LINE_Y), 2
        )


class Player:
    def __init__(self, name: str, keys: Sequence[int], x_start: int, width: int, color: str):
        self.name = name
        self.combo = 0
        self.score = 0
        self.health = 100
        palette = [pygame.Color(color), pygame.Color("lightskyblue"), pygame.Color("lightgreen"), pygame.Color("plum")]
        self.lanes: List[Lane] = [
            Lane(i, keys[i], x_start + i * width, width, palette[i % len(palette)]) for i in range(LANE_COUNT)
        ]

    def load_chart(self, chart: Sequence[Note]) -> None:
        for lane in self.lanes:
            lane.spawn_notes(chart)

    def handle_input(self, key: int, song_ms: int) -> bool:
        """Returns True if hit landed."""
        for lane in self.lanes:
            if key == lane.key:
                note = lane.next_hittable(song_ms)
                if note:
                    note.hit = True
                    self.combo += 1
                    self.score += 100 * self.combo
                    return True
                self.combo = 0
        return False

    def tick(self, song_ms: int) -> bool:
        """Update lanes and return True if any miss occurred."""
        missed = False
        for lane in self.lanes:
            if lane.remove_passed(song_ms):
                missed = True
                self.combo = 0
        return missed

    def draw(self, surf: pygame.Surface, song_ms: int) -> None:
        for lane in self.lanes:
            lane.draw(surf, song_ms)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("OOP Rhythm Duel")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.bg = self.load_bg()
        self.music_loaded = self.load_music()
        lane_w = SCREEN_W // 8
        self.p1 = Player("P1", [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k], x_start=lane_w, width=lane_w, color="orange")
        self.p2 = Player(
            "P2",
            [pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP, pygame.K_RIGHT],
            x_start=SCREEN_W // 2 + lane_w,
            width=lane_w,
            color="deepskyblue",
        )
        chart = self.generate_chart()
        self.p1.load_chart(chart)
        self.p2.load_chart(chart)
        self.running = True
        self.song_start_ms = 0

    def load_bg(self) -> pygame.Surface:
        if ASSET_DIR.joinpath("bg.png").exists():
            return pygame.transform.scale(pygame.image.load(ASSET_DIR / "bg.png"), (SCREEN_W, SCREEN_H))
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        bg.fill((18, 18, 24))
        return bg

    def load_music(self) -> bool:
        try:
            pygame.mixer.init()
            if AUDIO_PATH.exists():
                pygame.mixer.music.load(str(AUDIO_PATH))
                return True
        except pygame.error as exc:
            print(f"Audio init failed: {exc}")
        return False

    def generate_chart(self) -> List[Note]:
        # Demo chart: repeating lanes every 500ms
        chart: List[Note] = []
        pattern = [0, 1, 2, 3, 2, 1]
        time_ms = 1000
        for _ in range(30):
            for lane in pattern:
                chart.append(Note(time_ms=time_ms, lane=lane))
                time_ms += 180
            time_ms += 200
        return chart

    def apply_damage(self, attacker: Player, defender: Player) -> None:
        if attacker.combo and attacker.combo % 10 == 0:
            defender.health = max(0, defender.health - COMBO_DAMAGE)

    def run(self) -> None:
        if self.music_loaded:
            pygame.mixer.music.play()
            self.song_start_ms = pygame.time.get_ticks()
        else:
            self.song_start_ms = pygame.time.get_ticks()

        while self.running:
            dt = self.clock.tick(120)
            now_ms = pygame.time.get_ticks() - self.song_start_ms
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if self.p1.handle_input(event.key, now_ms):
                        self.apply_damage(self.p1, self.p2)
                    if self.p2.handle_input(event.key, now_ms):
                        self.apply_damage(self.p2, self.p1)

            if self.p1.tick(now_ms):
                pass
            if self.p2.tick(now_ms):
                pass
            if self.p1.health <= 0 or self.p2.health <= 0:
                self.running = False

            self.draw(now_ms)

        pygame.quit()
        sys.exit()

    def draw(self, song_ms: int) -> None:
        self.screen.blit(self.bg, (0, 0))
        pygame.draw.line(self.screen, pygame.Color("gray50"), (SCREEN_W // 2, 0), (SCREEN_W // 2, SCREEN_H), 3)
        self.p1.draw(self.screen, song_ms)
        self.p2.draw(self.screen, song_ms)
        self.draw_hud(self.p1, 20, song_ms)
        self.draw_hud(self.p2, SCREEN_W // 2 + 20, song_ms)
        pygame.display.flip()

    def draw_hud(self, player: Player, x: int, song_ms: int) -> None:
        texts = [
            f"{player.name}",
            f"Score: {player.score}",
            f"Combo: {player.combo}",
            f"Health: {player.health}",
        ]
        for i, txt in enumerate(texts):
            surf = self.font.render(txt, True, pygame.Color("white"))
            self.screen.blit(surf, (x, 20 + i * 28))
        pygame.draw.rect(self.screen, pygame.Color("red3"), (x, 150, 200, 16))
        pygame.draw.rect(
            self.screen,
            pygame.Color("limegreen"),
            (x, 150, int(200 * (player.health / 100)), 16),
        )


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
