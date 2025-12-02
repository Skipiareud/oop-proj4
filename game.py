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
                "Beethoven Virus",
                "Beethoven Virus.mp3",
                bpm=162,
                offset=0.0,
                chart=[
                    (2, 0.50),(3, 0.75),(2, 1.00),(1, 1.25),(2, 1.50),(3, 1.75),(2, 2.00),(1, 2.25),(2, 2.50),(3, 2.75),(2, 3.00),(3, 3.25),(2, 3.50),(1, 3.75),(2, 4.00),(3, 4.25),(2, 4.50),(3, 4.75),(2, 5.00),(1, 5.25),(2, 5.50),(3, 5.75),(2, 6.00),(1, 6.25),(3, 6.50),(2, 6.75),(3, 7.00),(2, 7.25),(1, 7.50),(3, 7.75),
                    (2, 8.00),(3, 8.25),(2, 8.50),(1, 8.75),(2, 9.00),(3, 9.25),(2, 9.50),(1, 9.75),(3, 10.00),(2, 10.25),(3, 10.50),(2, 10.75),(1, 11.00),(2, 11.25),(3, 11.50),(2, 11.75),(1, 12.00),(2, 12.25),(3, 12.50),(2, 12.75),(1, 13.00),(2, 13.25),(3, 13.50),(2, 13.75),(1, 14.00),(3, 14.25),(2, 14.50),(1, 14.75),(3, 15.00),(2, 15.25),(1, 15.50),(2, 15.75),(3, 16.00),(2, 16.25),(1, 16.50),(2, 16.75),(3, 17.00),(2, 17.25),(1, 17.50),(3, 17.75),(2, 18.00),(3, 18.25),(2, 18.50),(1, 18.75),(3, 19.00),(2, 19.25),(1, 19.50),(3, 19.75),(2, 20.00),(3, 20.25),
                    (1, 32.00),(3, 32.25),(1, 32.50),(3, 32.75),(2, 33.00),(1, 33.25),(3, 33.50),(2, 33.75),(1, 34.00),(3, 34.25),(1, 34.50),(3, 34.75),(2, 35.00),(1, 35.25),(3, 35.50),(1, 35.75),(3, 36.00),(2, 36.25),(1, 36.50),(3, 36.75),(0, 37.00),(2, 37.25),(0, 37.50),(2, 37.75),(3, 38.00),(0, 38.25),(3, 38.50),(1, 38.75),(3, 39.00),(1, 39.25),(0, 39.50),(2, 39.75),(3, 40.00),(1, 40.25),(3, 40.50),(2, 40.75),(1, 41.00),(3, 41.25),(0, 41.50),(2, 41.75),
                    (2, 56.00),(3, 56.25),(1, 56.50),(3, 56.75),(2, 57.00),(0, 57.25),(2, 57.50),(3, 57.75),(1, 58.00),(3, 58.25),(2, 58.50),(3, 58.75),(1, 59.00),(3, 59.25),(0, 59.50),(2, 59.75),(3, 60.00),(2, 60.25),(1, 60.50),(3, 60.75),(2, 61.00),(3, 61.25),(1, 61.50),(3, 61.75),(2, 62.00),(1, 62.25),(3, 62.50),(2, 62.75),(1, 63.00),(3, 63.25),(2, 63.50),(3, 63.75),(1, 64.00),(3, 64.25),(2, 64.50),(1, 64.75),(3, 65.00),(2, 65.25),(1, 65.50),(3, 65.75),
                    (2, 68.00),(3, 68.25),(2, 68.50),(1, 68.75),(2, 69.00),(3, 69.25),(2, 69.50),(1, 69.75),(3, 70.00),(2, 70.25),(3, 70.50),(2, 70.75),(1, 71.00),(2, 71.25),(3, 71.50),(2, 71.75),(1, 72.00),(2, 72.25),(3, 72.50),(2, 72.75),(1, 73.00),(2, 73.25),(3, 73.50),(2, 73.75),(1, 74.00),(3, 74.25),(2, 74.50),(1, 74.75),(3, 75.00),(2, 75.25),(1, 75.50),(2, 75.75),(3, 76.00),(2, 76.25),(1, 76.50),(3, 76.75),(2, 77.00),(1, 77.25),(3, 77.50),(2, 77.75),
                    (2, 102.00),(3, 102.25),(2, 102.50),(1, 102.75),(2, 103.00),(3, 103.25),(2, 103.50),(1, 103.75),(2, 104.00),(3, 104.25)
                ], 
                length_hint=102.5,
                start_delay=2.5,
            ),
            Song(
                "Small girl (feat. D.O.)",
                "이영지 - Small girl (feat. 도경수(D.O.).mp3",
                bpm=96,
                offset=0.0,
                chart=[
                    (2, 0.765), (2, 1.029), (3, 1.118), (2, 1.912), (3, 2.088),
                    (0, 2.176), (1, 2.529), (2, 3.588), (1, 4.294), (1, 4.559),

                    (3, 5.0), (3, 5.618), (2, 5.706), (1, 6.059), (0, 6.324),
                    (0, 6.412), (0, 7.029), (3, 7.471), (1, 8.176), (0, 8.265),

                    (0, 8.529), (0, 8.882), (2, 9.235), (3, 9.765), (1, 9.941),
                    (0, 10.294), (0, 10.912), (0, 11.265), (0, 11.353), (2, 11.971),

                    (2, 12.588), (0, 12.765), (0, 12.941), (0, 13.118), (0, 13.382),
                    (0, 13.647), (1, 13.735), (2, 14.529), (1, 14.882), (3, 15.147),

                    (3, 15.235), (3, 15.412), (3, 15.588), (3, 15.941), (2, 16.647),
                    (0, 16.912), (0, 17.265), (0, 17.353), (0, 17.618), (1, 18.059),

                    (1, 18.324), (3, 18.412), (2, 18.676), (2, 19.382), (3, 19.471),
                    (1, 19.824), (1, 20.176), (1, 20.529), (3, 20.794), (2, 22.294),

                    (2, 22.559), (1, 22.912), (1, 23.618), (2, 23.706), (0, 24.059),
                    (0, 24.324), (0, 24.412), (0, 24.676), (0, 24.941), (2, 25.471),

                    (3, 25.824), (3, 26.176), (3, 26.529), (3, 27.941), (3, 28.294),
                    (1, 29.0), (0, 29.353), (2, 29.706), (2, 29.882), (0, 30.588),

                    (0, 30.765), (1, 30.941), (2, 31.118), (1, 31.471), (0, 31.824),
                    (1, 32.0), (1, 32.529), (2, 32.882), (3, 33.235), (3, 33.588),

                    (3, 33.941), (3, 35.0), (3, 35.353), (2, 35.618), (3, 36.059),
                    (1, 36.765), (1, 37.471), (0, 38.529), (3, 38.882), (2, 39.235),

                    (3, 39.588), (2, 39.941), (2, 40.559), (1, 41.441), (2, 41.618),
                    (2, 42.059), (3, 42.324), (0, 42.412), (0, 43.118), (0, 43.471),

                    (0, 43.824), (0, 44.088), (0, 44.265), (0, 44.882), (1, 45.147),
                    (1, 45.235), (3, 45.588), (3, 46.118), (2, 46.294), (1, 46.647),

                    (2, 47.706), (3, 47.882), (2, 47.971), (0, 48.059), (1, 48.412),
                    (0, 49.029), (2, 49.118), (2, 49.471), (3, 49.824), (0, 50.529),

                    (1, 50.882), (1, 51.235), (0, 52.206), (0, 52.294), (3, 52.559),
                    (1, 53.353), (1, 53.618), (2, 53.706), (2, 54.412), (2, 54.765),

                    (2, 55.471), (2, 55.824), (2, 56.882), (2, 57.235), (0, 57.5),
                    (0, 57.588), (1, 57.853), (3, 58.206), (3, 58.559), (2, 58.647),

                    (3, 59.0), (3, 59.088), (1, 59.353), (2, 59.706), (2, 60.059),
                    (2, 60.324), (0, 60.412), (1, 60.765), (2, 61.118), (2, 61.824),

                    (2, 62.529), (0, 62.882), (1, 63.588), (1, 63.941), (3, 64.294),
                    (3, 64.559), (3, 64.647), (2, 65.706), (2, 65.971), (2, 66.059),

                    (1, 66.412), (1, 67.471), (3, 67.735), (3, 67.824), (3, 68.353),
                    (3, 68.794), (1, 69.235), (2, 69.588), (1, 69.676), (3, 69.941),

                    (3, 70.294), (3, 70.382), (3, 70.559), (1, 70.647), (2, 71.0),
                    (3, 71.088), (1, 71.353), (2, 71.882), (2, 72.059), (0, 72.5),

                    (1, 73.029), (2, 73.735), (2, 74.088), (0, 74.176), (1, 75.235),
                    (0, 75.412), (2, 75.588), (2, 75.941), (3, 76.118), (3, 76.206),

                    (3, 76.735), (2, 76.824), (0, 77.0), (0, 77.353), (0, 77.618),
                    (0, 78.059), (0, 78.412), (2, 78.853), (3, 79.294), (3, 79.735),

                    (2, 79.824), (0, 80.088), (0, 80.176), (0, 80.441), (3, 80.882),
                    (3, 81.235), (3, 81.5), (3, 81.588), (1, 81.941), (1, 82.206),

                    (2, 82.294), (1, 82.647), (0, 83.353), (2, 83.706), (1, 84.059),
                    (1, 84.412), (3, 84.588), (3, 85.118), (3, 85.382), (1, 85.471),

                    (0, 85.824), (1, 86.088), (1, 86.529), (1, 86.794), (3, 87.147),
                    (3, 87.235), (3, 87.5), (3, 87.588), (3, 87.765), (2, 88.118),

                    (1, 88.294), (3, 88.647), (2, 89.0), (1, 89.353), (1, 89.971),
                    (0, 90.059), (0, 90.324), (2, 90.412), (2, 91.118), (2, 91.294),

                    (2, 92.706), (2, 92.882), (1, 93.147), (0, 93.235), (0, 93.588),
                    (0, 93.941), (1, 94.559), (0, 94.647), (1, 94.912), (2, 95.0),

                    (3, 95.265), (1, 95.971), (2, 96.412), (2, 96.765), (3, 97.029),
                    (2, 97.118), (1, 97.382), (1, 97.471), (3, 97.735), (1, 98.882),

                    (0, 99.235), (0, 99.5), (1, 99.941), (0, 100.294), (1, 101.0),
                    (1, 101.176), (0, 101.529), (0, 101.618), (0, 101.706), (1, 101.882),

                    (0, 102.059), (1, 102.412), (3, 102.588), (2, 102.765), (3, 102.941),
                    (2, 103.118), (1, 103.735), (1, 103.824), (1, 104.529), (1, 105.941),

                    (1, 106.647), (3, 106.912), (3, 107.353), (2, 107.706), (1, 108.059),
                    (0, 108.324), (1, 108.765), (0, 109.118), (1, 109.382), (3, 109.471),

                    (3, 110.176), (3, 110.529), (2, 110.882), (1, 111.588), (3, 111.853),
                    (3, 112.206), (2, 113.706), (2, 113.971), (0, 114.059), (1, 114.412),

                    (2, 115.029), (1, 115.382), (3, 116.882), (2, 117.235), (0, 117.853),
                    (1, 118.206), (2, 118.294), (1, 118.559), (1, 119.0), (0, 119.706),

                    (0, 119.971), (0, 120.059), (1, 120.235), (3, 120.676), (3, 120.941),
                    (3, 121.824), (2, 122.529), (2, 122.882), (2, 123.588), (2, 124.206),

                    (2, 124.294), (0, 124.912), (0, 125.529), (0, 126.412), (1, 127.118),
                    (2, 128.088), (0, 128.529), (1, 129.412), (0, 129.853), (0, 129.941),

                    (1, 130.206), (3, 130.294), (3, 130.559), (1, 131.353), (1, 131.529),
                    (0, 131.794), (2, 132.147), (3, 133.471), (2, 133.824), (0, 134.088),

                    (1, 134.176), (0, 134.882), (0, 135.5), (0, 135.853), (2, 136.206),
                    (2, 136.912), (2, 137.0), (2, 137.265), (3, 137.971), (3, 138.765),

                    (3, 139.471), (1, 140.882), (3, 141.941), (2, 142.294), (2, 142.647),
                    (3, 142.824), (3, 143.353), (3, 143.706), (2, 144.412), (1, 144.765),

                    (1, 145.824), (3, 146.529), (2, 146.882), (2, 147.588), (3, 147.941),
                    (3, 149.0), (3, 149.529), (2, 149.706), (3, 150.059), (0, 150.412),

                    (0, 150.765), (0, 151.206), (0, 151.471), (0, 152.265), (0, 154.118),
                    (2, 155.176), (2, 156.147), (1, 156.676), (0, 156.765), (1, 158.529),

                    (0, 159.235), (1, 159.676), (0, 160.294), (0, 160.824), (2, 160.912),
                    (2, 161.441), (0, 161.971), (0, 162.235), (0, 162.765), (0, 163.471),

                    (0, 163.824), (1, 164.794), (2, 164.882), (0, 165.235), (1, 165.5),
                    (0, 165.588), (1, 165.941), (3, 166.294), (3, 166.471), (3, 166.647),

                    (3, 167.0), (2, 167.618), (3, 167.706), (3, 168.059), (2, 170.441),
                    (2, 170.529), (0, 170.882), (3, 171.941), (2, 172.118), (2, 172.294),

                    (2, 172.647), (0, 173.0), (0, 173.265), (0, 173.353), (1, 173.706),
                    (1, 174.412), (0, 175.824), (0, 176.176), (1, 177.059), (0, 177.235),

                    (0, 177.588), (2, 177.765), (3, 177.941), (2, 178.647), (2, 178.912),
                    (3, 179.0), (2, 179.706), (3, 180.412), (2, 180.765), (3, 181.118),

                    (2, 181.824), (1, 182.176), (3, 182.529), (3, 182.706), (3, 182.882),
                    (3, 183.235), (3, 183.941), (3, 184.294)
                ],
                length_hint=189.8,
                start_delay=2.5,
            ),
        ]
    


    #  ---- State transitions ----
    def _start_song(self, song: Song) -> None:
        chart = [(lane, max(MIN_FIRST_NOTE, t + song.offset)) for lane, t in (song.chart or [])]
        if not chart:
            print(f"[warn] chart is empty for '{song.name}'. Add (lane, time) tuples to Song.chart.")
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
