import sys
from typing import List, Optional, Tuple

import pygame

from audio_player import AudioPlayer
from models import Song, Track

MIN_FIRST_NOTE = 0.4  # clamp first note a bit after lead-in


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.width, self.height = 960, 540
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Two Player Rhythm Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 22)
        self.big_font = pygame.font.SysFont("Menlo", 36, bold=True)
        self.label_font = pygame.font.SysFont("Menlo", 26, bold=True)
        self.hit_y = self.height - 100
        self.speed = 420
        self.tracks = self._make_tracks()
        self.songs = self._load_song_list()
        self.selected_song_idx = 0
        self.state = "menu"
        self.audio = AudioPlayer()
        self.song_end: float = 0.0
        self.start_ms: int = pygame.time.get_ticks()
        self.current_song: Optional[Song] = None
        self.confirming_exit: bool = False
        self.bg_color = (12, 14, 22)
        self.accent_color = (86, 122, 255)
        self.center_line_color = (80, 80, 90)
        self.judge_colors = {
            "Perfect": (120, 220, 255),
            "Great": (140, 235, 180),
            "Good": (255, 210, 120),
            "Miss": (255, 120, 120),
        }

    def _make_tracks(self) -> Tuple[Track, Track]:
        half = self.width // 2
        left_keys = {pygame.K_q: 0, pygame.K_w: 1, pygame.K_e: 2, pygame.K_r: 3}
        right_keys = {pygame.K_o: 0, pygame.K_p: 1, pygame.K_LEFTBRACKET: 2, pygame.K_RIGHTBRACKET: 3}
        return (
            Track("Player 1", 0, half, left_keys, (111, 203, 255)),
            Track("Player 2", half, half, right_keys, (255, 176, 122)),
        )

    def _load_song_list(self) -> List[Song]:
        return [
            Song(
                "Entrance",
                "deemo_Entrance.mp3",
                bpm=128,
                offset=0.0,  # global offset if needed
                chart=[],  # 여기에 (lane, time) 튜플 리스트로 악보를 넣으세요
                length_hint=113.3,
                start_delay=2.5,
            ),
            Song(
                "Beethoven Virus",
                "Beethoven Virus.mp3",
                bpm=162,
                offset=0.0,
                chart=[],
                length_hint=102.5,
                start_delay=2.5,
            ),
            Song(
                "Small girl (feat. D.O.)",
                "이영지 - Small girl (feat. 도경수(D.O.).mp3",
                bpm=96,
                offset=0.0,
                chart=[],
                length_hint=189.8,
                start_delay=2.5,
            ),
        ]

    # ---- State transitions ----
    def _start_song(self, song: Song) -> None:
        chart = [(lane, max(MIN_FIRST_NOTE, t + song.offset)) for lane, t in (song.chart or [])]
        chart.sort(key=lambda x: x[1])
        for track in self.tracks:
            track.load_chart(chart)
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
            label = f"{prefix}{song.name} (bpm {song.bpm}, diff {song.difficulty:.1f})"
            surf = self.font.render(label, True, color)
            self.screen.blit(surf, (80, y))
            y += 30

    def _draw_play(self, now: float, raw_now: float) -> None:
        self._draw_background()
        for track in self.tracks:
            track.draw(self.screen, now, self.hit_y, self.speed)
        self._draw_center_divider()
        self._draw_ui(now)
        lead = self.current_song.start_delay if self.current_song else 0
        remain = lead - raw_now if raw_now < lead else 0
        if remain > 0 and not self.confirming_exit:
            self._draw_countdown(remain)
        if self.confirming_exit:
            self._draw_exit_confirm()

    def _draw_background(self) -> None:
        self.screen.fill(self.bg_color)
        half = self.width // 2
        tint_left = pygame.Surface((half, self.height), pygame.SRCALPHA)
        tint_left.fill((*self.tracks[0].color, 26))
        tint_right = pygame.Surface((half, self.height), pygame.SRCALPHA)
        tint_right.fill((*self.tracks[1].color, 26))
        self.screen.blit(tint_left, (0, 0))
        self.screen.blit(tint_right, (half, 0))
        band = pygame.Surface((self.width, 140), pygame.SRCALPHA)
        pygame.draw.rect(band, (255, 255, 255, 18), (0, 0, self.width, 140), border_radius=18)
        self.screen.blit(band, (0, 0))
        grid = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 36):
            alpha = 20 if (y // 36) % 2 == 0 else 12
            pygame.draw.line(grid, (255, 255, 255, alpha), (0, y), (self.width, y), 1)
        self.screen.blit(grid, (0, 0))

    def _draw_center_divider(self) -> None:
        pygame.draw.line(self.screen, self.center_line_color, (self.width // 2, 0), (self.width // 2, self.height), 3)
        glow = pygame.Surface((4, self.height), pygame.SRCALPHA)
        pygame.draw.line(glow, (255, 255, 255, 60), (2, 0), (2, self.height), 2)
        self.screen.blit(glow, (self.width // 2 - 2, 0))
        pygame.draw.circle(self.screen, self.center_line_color, (self.width // 2, int(self.hit_y)), 8, 2)

    def _draw_ui(self, now: float) -> None:
        for track in self.tracks:
            self._draw_track_panel(track)
            self._draw_judgement(track, now)
        self._draw_footer(now)

    def _draw_track_panel(self, track: Track) -> None:
        panel_rect = pygame.Rect(track.x + 16, 16, track.width - 32, 72)
        pygame.draw.rect(self.screen, (*track.color, 70), panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (*track.color, 120), panel_rect, width=2, border_radius=14)
        name_surf = self.label_font.render(track.name, True, (245, 245, 245))
        score_surf = self.font.render(f"Score {track.score}", True, (230, 230, 230))
        combo_surf = self.font.render(f"Combo {track.combo}", True, (230, 230, 230))
        lane_keys = [""] * 4
        for key, lane in track.keys.items():
            label = pygame.key.name(key).upper()
            if lane < len(lane_keys):
                lane_keys[lane] = label
        keys_surf = self.font.render(" ".join(lane_keys), True, (210, 210, 210))
        self.screen.blit(name_surf, (panel_rect.x + 14, panel_rect.y + 6))
        self.screen.blit(score_surf, (panel_rect.x + 14, panel_rect.y + 36))
        self.screen.blit(combo_surf, (panel_rect.x + panel_rect.width // 2, panel_rect.y + 36))
        self.screen.blit(keys_surf, (panel_rect.right - keys_surf.get_width() - 14, panel_rect.y + 6))
        pygame.draw.rect(
            self.screen,
            (*track.color, 160),
            (panel_rect.x + 12, panel_rect.bottom - 10, min(panel_rect.width - 24, 160), 4),
            border_radius=2,
        )

    def _draw_judgement(self, track: Track, now: float) -> None:
        if track.last_label_time <= 0:
            return
        age = now - track.last_label_time
        if age > 1.1:
            return
        if now < track.first_note_time:
            return
        color = self.judge_colors.get(track.last_label, (235, 235, 235))
        surf = self.big_font.render(track.last_label, True, color)
        alpha = max(0, 255 - int((age / 1.1) * 255))
        surf.set_alpha(alpha)
        x = track.x + track.width // 2 - surf.get_width() // 2
        y = self.hit_y - 130
        shadow = self.big_font.render(track.last_label, True, (0, 0, 0))
        shadow.set_alpha(min(alpha, 140))
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(surf, (x, y))

    def _draw_footer(self, now: float) -> None:
        info_text = "B: restart | Esc: quit song"
        info_surf = self.font.render(info_text, True, (205, 205, 205))
        info_x = self.width // 2 - info_surf.get_width() // 2
        info_y = 98
        self.screen.blit(info_surf, (info_x, info_y))
        timer_surf = self.font.render(f"{now:05.2f}s", True, (215, 215, 215))
        timer_x = self.width // 2 - timer_surf.get_width() // 2
        timer_y = info_y + 26
        self.screen.blit(timer_surf, (timer_x, timer_y))

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
