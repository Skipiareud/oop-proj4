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

        # (예전 ESC 확인용 플래그 – 지금은 안 씀, 남겨만둠)
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

        # ---- 일시정지 관련 상태 ----
        self.is_paused: bool = False               # 완전 정지 상태
        self.in_resume_countdown: bool = False     # 3초 카운트다운 중인지
        self.resume_countdown: float = 0.0         # 남은 카운트다운 시간
        self.pause_tick_ms: int = 0                # pause 시작 tick
        self.paused_raw_now: float = 0.0           # pause 시점의 raw_now
        self.resume_start_ms: int = 0              # 카운트다운 시작 tick

        # ---- 콤보 공격 관련 ----
        self.combo_damage: int = 500               # 콤보 공격 시 깎을 점수
        self.prev_combos = [0, 0]                  # 직전 프레임 콤보값

        # 콤보 공격 이펙트용
        self.last_combo_attack_time: float = -1.0
        self.last_combo_attack_player: Optional[int] = None

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
                "Entrance (Deemo ver.)",
                "entrance.wav",
                bpm=90.67,
                start_delay=1.5,
                chart=[
                    (1, 5.636),         (1, 7.456),         (2, 7.952),         (0, 8.283),         (1, 10.434),         (1, 11.757),         (1, 13.081),         (1, 13.743),         (2, 14.404),         (1, 17.713),
                    (1, 18.541),         (1, 18.871),         (1, 21.022),         (1, 21.684),         (1, 22.346),         (1, 23.007),         (1, 27.805),         (2, 28.302),         (1, 28.963),         (1, 33.927),
                    (1, 36.243),         (1, 36.408),         (1, 41.372),         (3, 42.53),         (1, 42.695),         (1, 42.861),         (1, 47.824),         (3, 48.982),         (1, 50.471),         (2, 51.133),
                    (3, 51.629),         (3, 52.291),         (3, 52.456),         (1, 52.953),         (3, 58.743),         (1, 63.541),         (1, 63.872),         (1, 69.662),         (2, 71.317),         (3, 74.625),
                    (3, 74.956),         (1, 85.214),         (0, 87.034),         (1, 88.523),         (2, 88.853),         (2, 89.515),         (1, 89.846),         (2, 90.177),         (1, 91.335),         (3, 91.501),
                    (1, 91.997),         (1, 92.328),         (2, 92.659),         (1, 93.32),         (2, 93.486),         (3, 94.313),         (2, 96.298),         (1, 96.795),         (1, 96.96),         (2, 99.607),
                    (1, 100.6),         (2, 100.931),         (2, 101.593),         (1, 101.923),         (2, 102.089),         (2, 102.42),         (3, 102.751),         (2, 103.081),         (2, 103.743),         (2, 104.24),
                    (2, 104.901),         (1, 105.232),         (2, 106.059),         (2, 106.887),         (2, 107.383),         (3, 107.548),         (0, 111.684)
                ]
            ),
            Song(
                "Beethoven Virus",
                "Beethoven Virus.mp3",
                bpm=162,
                offset=0.0,
                chart=[
                    (0, 3.093), (0, 3.185), (0, 3.463), (2, 3.741), (1, 4.296),
                    (0, 5.037), (1, 5.407), (3, 5.963), (2, 6.148), (1, 6.333),

                    (0, 6.519), (2, 6.704), (2, 6.981), (2, 7.074), (0, 7.167),
                    (1, 7.259), (2, 7.352), (2, 7.444), (1, 7.722), (2, 8.093),

                    (2, 8.185), (1, 8.37), (1, 8.556), (1, 8.741), (0, 9.389),
                    (0, 9.852), (0, 10.037), (0, 10.222), (0, 10.593), (1, 10.778),

                    (1, 10.963), (1, 11.519), (2, 11.704), (0, 11.889), (0, 12.167),
                    (0, 12.352), (0, 12.537), (1, 12.63), (0, 12.907), (0, 13.093),

                    (0, 13.185), (2, 13.37), (3, 13.833), (3, 14.481), (2, 14.667),
                    (1, 14.852), (3, 15.037), (3, 15.222), (3, 15.407), (2, 16.056),

                    (1, 16.889), (2, 17.074), (1, 17.444), (1, 18.185), (1, 18.37),
                    (1, 18.556), (0, 19.296), (2, 19.481), (1, 20.315), (2, 20.407),

                    (3, 20.778), (2, 21.333), (2, 21.704), (1, 22.167), (2, 22.444),
                    (0, 22.63), (0, 22.907), (0, 23.185), (0, 23.556), (1, 23.833),

                    (2, 24.389), (3, 24.667), (0, 24.852), (0, 25.037), (0, 25.222),
                    (0, 25.593), (1, 25.963), (0, 26.148), (0, 26.333), (0, 26.519),

                    (1, 26.704), (2, 26.889), (2, 27.167), (0, 27.259), (0, 27.537),
                    (1, 27.63), (0, 28.093), (1, 28.463), (3, 28.741), (2, 28.926),

                    (2, 29.296), (1, 29.667), (2, 30.037), (0, 30.222), (0, 30.407),
                    (1, 30.593), (2, 30.778), (3, 31.056), (3, 31.241), (1, 31.704),

                    (1, 31.889), (0, 32.074), (1, 32.259), (1, 32.63), (0, 33.093),
                    (0, 33.741), (0, 34.296), (1, 34.481), (0, 34.667), (2, 34.852),

                    (2, 35.037), (3, 35.222), (3, 35.407), (2, 35.685), (0, 36.333),
                    (0, 36.519), (0, 36.704), (0, 36.889), (0, 37.444), (0, 37.63),

                    (0, 38.0), (1, 38.648), (1, 38.926), (2, 39.111), (2, 39.481),
                    (1, 39.667), (0, 40.037), (0, 40.222), (0, 40.407), (0, 40.593),

                    (2, 40.778), (3, 40.963), (2, 41.148), (0, 41.519), (1, 41.704),
                    (3, 42.259), (2, 42.444), (3, 42.63), (1, 43.0), (1, 43.37),

                    (0, 43.556), (2, 43.741), (1, 43.926), (2, 44.296), (2, 44.574),
                    (0, 45.407), (0, 45.593), (1, 45.963), (1, 46.148), (2, 46.426),

                    (2, 46.704), (0, 46.889), (0, 47.167), (1, 47.444), (1, 47.815),
                    (0, 48.0), (0, 48.185), (2, 48.37), (1, 48.556), (1, 48.741),

                    (1, 48.926), (0, 49.111), (0, 49.296), (0, 49.481), (0, 49.759),
                    (2, 49.852), (2, 50.037), (1, 50.407), (0, 50.87), (1, 50.963),

                    (3, 51.333), (3, 51.519), (3, 51.704), (3, 52.259), (3, 52.444),
                    (3, 52.63), (1, 52.815), (2, 53.37), (2, 53.833), (3, 53.926),

                    (1, 54.296), (2, 54.481), (3, 54.852), (1, 55.037), (0, 55.222),
                    (1, 55.407), (3, 55.778), (2, 55.963), (1, 56.148), (2, 56.333),

                    (3, 57.167), (3, 57.259), (3, 57.63), (3, 57.815), (3, 58.185),
                    (2, 58.37), (3, 58.741), (3, 58.926), (1, 59.204), (0, 59.296),

                    (3, 60.037), (3, 60.407), (1, 60.778), (1, 61.241), (1, 61.426),
                    (2, 61.611), (1, 61.704), (1, 61.889), (2, 62.074), (1, 62.352),

                    (2, 63.185), (3, 63.556), (2, 63.741), (3, 64.574), (3, 64.667),
                    (3, 64.852), (1, 65.13), (2, 65.222), (2, 65.593), (3, 65.778),

                    (1, 65.963), (0, 66.148), (1, 66.333), (0, 66.519), (0, 66.889),
                    (1, 67.074), (3, 67.444), (2, 68.926), (2, 69.667), (3, 69.852),

                    (3, 70.037), (1, 70.407), (2, 70.593), (3, 71.148), (2, 71.333),
                    (1, 71.519), (1, 71.981), (0, 72.63), (0, 73.0), (0, 73.741),

                    (0, 74.111), (1, 74.481), (0, 74.667), (2, 74.852), (3, 75.222),
                    (1, 75.685), (2, 76.148), (1, 76.519), (1, 76.704), (1, 77.074),

                    (1, 77.259), (2, 77.63), (3, 78.0), (3, 78.37), (2, 78.741),
                    (1, 79.111), (3, 79.296), (2, 79.481), (2, 79.759), (3, 80.037),

                    (3, 80.315), (1, 80.778), (1, 80.963), (0, 81.333), (1, 81.889),
                    (2, 82.259), (3, 82.63), (3, 83.0), (3, 83.278), (3, 83.37),

                    (3, 83.833), (3, 84.296), (1, 84.852), (0, 85.963), (1, 86.333),
                    (0, 86.704), (0, 86.889), (2, 87.074), (1, 87.352), (1, 87.63),

                    (0, 87.815), (0, 88.185), (0, 88.37), (1, 88.556), (2, 88.926),
                    (1, 89.296), (1, 89.481), (1, 90.037), (3, 90.222), (3, 90.407),

                    (3, 90.593), (1, 90.963), (0, 91.333), (2, 91.704), (2, 92.63),
                    (0, 93.185), (1, 93.37), (1, 93.741), (1, 93.926), (0, 94.111),

                    (0, 94.296), (1, 94.481), (1, 95.037), (0, 95.778), (0, 96.148),
                    (0, 96.889), (1, 97.259), (3, 97.815), (2, 98.278), (2, 98.463),

                    (2, 98.741), (3, 99.019), (2, 99.111), (0, 99.296)
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
        self.current_song = song

        # pause / combo 상태 리셋
        self.is_paused = False
        self.in_resume_countdown = False
        self.resume_countdown = 0.0
        self.prev_combos = [0, 0]
        self.last_combo_attack_time = -1.0
        self.last_combo_attack_player = None

    def _back_to_menu(self) -> None:
        self.state = "menu"
        self.audio.stop()
        self.is_paused = False
        self.in_resume_countdown = False
        self.resume_countdown = 0.0
        self.last_combo_attack_time = -1.0
        self.last_combo_attack_player = None

    # ---- Main loop ----
    def run(self) -> None:
        running = True
        while running:
            tick_now = pygame.time.get_ticks()

            # 시간 계산 (pause / countdown 중이면 시간 멈춤)
            if self.state == "play" and self.current_song:
                if self.is_paused or self.in_resume_countdown:
                    raw_now = self.paused_raw_now
                else:
                    raw_now = (tick_now - self.start_ms) / 1000.0
                start_delay = self.current_song.start_delay
                now = max(0.0, raw_now - start_delay)
            else:
                raw_now = 0.0
                now = 0.0

            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key(event.key, now)

            # 상태 업데이트 & 그리기
            if self.state == "play" and self.current_song:
                # 재개 카운트다운 처리
                if self.in_resume_countdown:
                    elapsed = (tick_now - self.resume_start_ms) / 1000.0
                    self.resume_countdown = max(0.0, 3.0 - elapsed)
                    if self.resume_countdown <= 0.0:
                        # 카운트다운 끝 → 실제 시간 보정 후 재개
                        self.in_resume_countdown = False
                        self.is_paused = False
                        delta_ms = tick_now - self.pause_tick_ms
                        self.start_ms += delta_ms
                        try:
                            pygame.mixer.music.unpause()
                        except pygame.error:
                            pass

                # 실제 플레이 진행은 pause / countdown 아닐 때만
                if not self.is_paused and not self.in_resume_countdown:
                    self.audio.tick()
                    for track in self.tracks:
                        track.update_misses(now)
                    self._update_combo_attacks(now)

                self._draw_play(now, raw_now)

                # 게임 종료 판정도 진행 중일 때만
                if (
                    not self.is_paused
                    and not self.in_resume_countdown
                    and now > self.song_end
                    and all(t.finished() for t in self.tracks)
                ):
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
        # 메뉴
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

        # 플레이 중일 때 (state == "play")
        if self.state == "play":
            # 일시정지/카운트다운 상태에서의 입력
            if self.is_paused or self.in_resume_countdown:
                if key in (pygame.K_RETURN, pygame.K_SPACE):
                    # 일시정지 중 Enter/Space → 3초 카운트다운 시작
                    if self.is_paused and not self.in_resume_countdown:
                        self.in_resume_countdown = True
                        self.resume_start_ms = pygame.time.get_ticks()
                        self.resume_countdown = 3.0
                    return True
                if key == pygame.K_ESCAPE:
                    # 일시정지 상태에서 ESC → 메뉴로
                    self._back_to_menu()
                    return True
                if key == pygame.K_b:
                    # 일시정지 상태에서 B → 곡 재시작
                    self._start_song(self.current_song)
                    return True
                return True

            # 여기부터는 정상 플레이 중
            if key == pygame.K_ESCAPE:
                # ESC → 일시정지 진입
                self._enter_pause()
                return True
            if key == pygame.K_b:
                # 곡 재시작
                self._start_song(self.current_song)
                return True

            for track in self.tracks:
                track.handle_key(key, now)
            return True

        return True

    def _enter_pause(self) -> None:
        """ESC 눌렀을 때 호출: 게임/음악 일시정지."""
        if self.is_paused:
            return
        self.is_paused = True
        self.in_resume_countdown = False
        self.resume_countdown = 0.0
        self.pause_tick_ms = pygame.time.get_ticks()
        self.paused_raw_now = (self.pause_tick_ms - self.start_ms) / 1000.0
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass

    # ---- Combo 공격 로직 ----
    def _update_combo_attacks(self, now: float) -> None:
        """콤보가 5,10,15,...에 도달할 때마다 상대 점수를 깎고 이펙트."""
        for i, track in enumerate(self.tracks):
            combo = track.combo
            prev = self.prev_combos[i]
            if combo != prev:
                if combo > prev and combo > 0 and combo % 5 == 0:
                    other = self.tracks[1 - i]
                    # 점수 감소
                    other.score = max(0, other.score - self.combo_damage)
                    # 맞은 쪽에 -500 판정처럼 표시
                    other.last_label = f"-{self.combo_damage}"
                    other.last_label_time = now
                    # 이펙트 정보 기록 (공격한 플레이어 인덱스)
                    self.last_combo_attack_time = now
                    self.last_combo_attack_player = i
                self.prev_combos[i] = combo

    # ---- Drawing ----
    def _draw_menu(self) -> None:
        self.screen.fill((18, 18, 24))
        title = self.big_font.render("Two Player Rhythm Battle", True, (240, 240, 240))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 40))
        info_lines = [
            "Controls: P1=QWER, P2=OP[], Up/Down to choose",
            "In game: B=restart, Esc=pause",
            "Paused: Enter/Space=resume (3s), B=restart, Esc=menu",
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

        # 곡 시작 전 리드인 카운트다운 (일시정지 중에는 표시 안 함)
        lead = self.current_song.start_delay if self.current_song else 0
        remain = lead - raw_now if raw_now < lead else 0
        if remain > 0 and not self.is_paused and not self.in_resume_countdown:
            self._draw_countdown(remain)

        # 콤보 공격 이펙트
        self._draw_combo_effect(now)

        # Pause / Resume 카운트다운 오버레이
        if self.is_paused and not self.in_resume_countdown:
            self._draw_pause_menu()
        if self.in_resume_countdown:
            self._draw_countdown(self.resume_countdown)

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
        info_text = "B: restart | Esc: pause"
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

    def _draw_pause_menu(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        lines = [
            "Paused",
            "Enter/Space: resume (3s countdown)",
            "B: restart song",
            "Esc: back to menu",
        ]
        y = self.height // 2 - 40
        for line in lines:
            surf = self.big_font.render(line, True, (240, 240, 240))
            rect = surf.get_rect(center=(self.width // 2, y))
            self.screen.blit(surf, rect)
            y += 44

    def _draw_combo_effect(self, now: float) -> None:
        """콤보 공격 시 맞은 쪽 화면 붉게 번쩍 + COMBO HIT! 텍스트."""
        if self.last_combo_attack_time < 0 or self.last_combo_attack_player is None:
            return
        age = now - self.last_combo_attack_time
        duration = 0.35
        if age < 0 or age > duration:
            return

        t = age / duration
        alpha = int(180 * (1.0 - t))
        if alpha <= 0:
            return

        attacker = self.last_combo_attack_player
        victim_idx = 1 - attacker
        victim_track = self.tracks[victim_idx]

        # 맞은 쪽 레인 전체 붉은 오버레이
        overlay = pygame.Surface((victim_track.width, self.height), pygame.SRCALPHA)
        overlay.fill((255, 80, 80, alpha))
        self.screen.blit(overlay, (victim_track.x, 0))

        # 중앙에 "COMBO HIT!" 텍스트
        text = self.big_font.render("COMBO HIT!", True, (255, 255, 255))
        text.set_alpha(alpha)
        cx = victim_track.x + victim_track.width // 2 - text.get_width() // 2
        cy = self.height // 2 - text.get_height() // 2
        self.screen.blit(text, (cx, cy))

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
