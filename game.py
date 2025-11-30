import sys
from typing import List, Optional, Tuple

import pygame

from audio_player import AudioPlayer
from chart import OnsetChartGenerator, OnsetDetector, ProceduralChartGenerator
from models import Song, Track


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.width, self.height = 960, 540
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Two Player Rhythm Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 22)
        self.big_font = pygame.font.SysFont("Menlo", 36)
        self.hit_y = self.height - 100
        self.speed = 420
        self.tracks = self._make_tracks()
        self.songs = self._load_song_list()
        self.selected_song_idx = 0
        self.state = "menu"
        self.generator = OnsetChartGenerator(OnsetDetector(), ProceduralChartGenerator())
        self.audio = AudioPlayer()
        self.song_end: float = 0.0
        self.start_ms: int = pygame.time.get_ticks()
        self.last_chart_source: str = "procedural"
        self.current_song: Optional[Song] = None
        self.confirming_exit: bool = False

    def _make_tracks(self) -> Tuple[Track, Track]:
        half = self.width // 2
        left_keys = {pygame.K_q: 0, pygame.K_w: 1, pygame.K_e: 2, pygame.K_r: 3}
        right_keys = {pygame.K_o: 0, pygame.K_p: 1, pygame.K_LEFTBRACKET: 2, pygame.K_RIGHTBRACKET: 3}
        return (
            Track("Player 1 (Q W E R)", 0, half, left_keys, (111, 203, 255)),
            Track("Player 2 (O P [ ])", half, half, right_keys, (255, 176, 122)),
        )

    def _load_song_list(self) -> List[Song]:
        return [
            Song(
                "Entrance",
                "deemo_Entrance.mp3",
                bpm=128,
                offset=0.0,
                chart_offset=0.0,
                difficulty=1.0,
                length_hint=113.3,
                start_delay=2.5,
            ),
            Song(
                "Beethoven Virus",
                "Beethoven Virus.mp3",
                bpm=162,
                offset=0.0,
                chart_offset=0.0,
                difficulty=1.15,
                length_hint=102.5,
                start_delay=2.5,
            ),
            Song(
                "Small girl (feat. D.O.)",
                "이영지 - Small girl (feat. 도경수(D.O.).mp3",
                bpm=96,
                offset=0.0,
                chart_offset=0.0,
                difficulty=0.95,
                length_hint=189.8,
                start_delay=2.5,
            ),
        ]

    # ---- State transitions ----
    def _start_song(self, song: Song) -> None:
        chart, source = self.generator.generate(song)
        chart = [(lane, t + song.offset) for lane, t in chart]
        for track in self.tracks:
            track.load_chart(chart)
        self.last_chart_source = source
        self.song_end = (max(time for _, time in chart) if chart else song.length_hint) + 4.0
        self.start_ms = pygame.time.get_ticks()
        self.audio.queue(song.path, song.start_delay)
        self.state = "play"
        self.confirming_exit = False
        self.current_song = song

    def _back_to_menu(self) -> None:
        self.state = "menu"
        self.audio.stop()
        self.confirming_exit = False

    # ---- Main loop ----
    def run(self) -> None:
        running = True
        while running:
            tick_now = pygame.time.get_ticks()
            raw_now = (tick_now - self.start_ms) / 1000.0
            start_delay = self.current_song.start_delay if self.state == "play" and self.current_song else 0.0
            now = max(0.0, raw_now - start_delay)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key(event.key, now)

            if self.state == "play":
                self.audio.tick()
                if not self.confirming_exit:
                    for track in self.tracks:
                        track.update_misses(now)
                self._draw_play(now, raw_now)
                if not self.confirming_exit and now > self.song_end and all(t.finished() for t in self.tracks):
                    self._draw_game_over()
                    pygame.display.flip()
                    self._wait_for_restart()
                    self._back_to_menu()
            else:
                self._draw_menu()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    # ---- Input ----
    def _handle_key(self, key: int, now: float) -> bool:
        if self.confirming_exit:
            if key in (pygame.K_y, pygame.K_RETURN):
                self._back_to_menu()
            elif key in (pygame.K_n, pygame.K_ESCAPE, pygame.K_SPACE):
                self.confirming_exit = False
            return True

        if self.state == "menu":
            if key == pygame.K_ESCAPE:
                return False
            if key == pygame.K_UP:
                self.selected_song_idx = (self.selected_song_idx - 1) % len(self.songs)
            elif key == pygame.K_DOWN:
                self.selected_song_idx = (self.selected_song_idx + 1) % len(self.songs)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                song = self.songs[self.selected_song_idx]
                self._start_song(song)
            return True

        # playing state
        if key == pygame.K_ESCAPE:
            self.confirming_exit = True
            return True
        if key == pygame.K_b:
            self._start_song(self.current_song)
            return True
        for track in self.tracks:
            track.handle_key(key, now)
        return True

    # ---- Drawing ----
    def _draw_menu(self) -> None:
        self.screen.fill((18, 18, 24))
        title = self.big_font.render("Two Player Rhythm Battle", True, (240, 240, 240))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 40))
        info_lines = [
            "Controls: P1=QWER, P2=OP[], Up/Down to choose, Esc=quit app",
        ]
        y = 120
        for line in info_lines:
            surf = self.font.render(line, True, (210, 210, 210))
            self.screen.blit(surf, (60, y))
            y += 28
        y += 8
        for idx, song in enumerate(self.songs):
            color = (255, 230, 150) if idx == self.selected_song_idx else (190, 190, 190)
            prefix = "➤ " if idx == self.selected_song_idx else "  "
            label = f"{prefix}{song.name} (bpm {song.bpm}, diff {song.difficulty:.1f}, offset {song.offset:+.2f}, chartOff {song.chart_offset:+.2f})"
            surf = self.font.render(label, True, color)
            self.screen.blit(surf, (80, y))
            y += 30

    def _draw_play(self, now: float, raw_now: float) -> None:
        self.screen.fill((25, 26, 32))
        for track in self.tracks:
            track.draw(self.screen, now, self.hit_y, self.speed)
        self._draw_ui(now)
        lead = self.current_song.start_delay if self.current_song else 0
        remain = lead - raw_now if raw_now < lead else 0
        if remain > 0 and not self.confirming_exit:
            self._draw_countdown(remain)
        if self.confirming_exit:
            self._draw_exit_confirm()

    def _draw_ui(self, now: float) -> None:
        text_y = 10
        for track in self.tracks:
            label = f"{track.name} | Score: {track.score} | Combo: {track.combo} | {track.last_label}"
            surf = self.font.render(label, True, (235, 235, 235))
            self.screen.blit(surf, (20, text_y))
            text_y += 28
        info = self.font.render("B: restart   Esc: quit song", True, (200, 200, 200))
        self.screen.blit(info, (20, self.height - 32))
        timer = self.font.render(f"{now:05.2f}s", True, (180, 180, 180))
        self.screen.blit(timer, (self.width - 120, 10))

    def _draw_countdown(self, remain: float) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        text = self.big_font.render(f"Starts in {remain:0.1f}s", True, (240, 240, 240))
        rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, rect)

    def _draw_exit_confirm(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        lines = [
            "Quit this song and return to menu?",
            "Y/Enter: Yes   N/Esc: No",
        ]
        y = self.height // 2 - 20
        for line in lines:
            surf = self.big_font.render(line, True, (240, 240, 240))
            rect = surf.get_rect(center=(self.width // 2, y))
            self.screen.blit(surf, rect)
            y += 48

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        p1, p2 = self.tracks
        winner = "Draw" if p1.score == p2.score else ("Player 1" if p1.score > p2.score else "Player 2")
        lines = [
            "Song complete!",
            f"P1: {p1.score}    P2: {p2.score}",
            f"Winner: {winner}",
            "B: restart | Esc: quit song | wait: menu",
        ]
        y = self.height // 2 - 70
        for line in lines:
            surf = self.big_font.render(line, True, (240, 240, 240))
            rect = surf.get_rect(center=(self.width // 2, y))
            self.screen.blit(surf, rect)
            y += 44

    def _wait_for_restart(self) -> None:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._back_to_menu()
                        return
                    if event.key == pygame.K_b:
                        self._start_song(self.current_song)
                        return
            self.clock.tick(60)
