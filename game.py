import sys
from typing import List, Optional, Tuple

import pygame

from audio_player import AudioPlayer
from models import Song, Track

MIN_FIRST_NOTE = 0.4  # clamp first note a bit after lead-in


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.width, self.height = 1440, 810
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Two Player Rhythm Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 22)
        self.big_font = pygame.font.SysFont("Menlo", 36, bold=True)
        self.label_font = pygame.font.SysFont("Menlo", 26, bold=True)
        self.menu_font = pygame.font.SysFont("Menlo", 26)
        self.menu_big_font = pygame.font.SysFont("Menlo", 44, bold=True)

        self.hit_y = self.height - 150
        self.speed = 420

        self.tracks = self._make_tracks()
        self.songs = self._load_song_list()
        self.selected_song_idx = 0

        self.state = "menu"
        self.audio = AudioPlayer()
        self.song_end: float = 0.0
        self.start_ms: int = pygame.time.get_ticks()
        self.current_song: Optional[Song] = None
        self.just_started: bool = False
        self.play_mode: str = "sudden"
        self.game_modes = [("sudden", "Sudden KO"), ("endurance", "Endurance")]
        self.selected_mode_idx: int = 0

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

        # 공격/피격 이펙트용
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
                "Beethoven Virus",
                "Beethoven Virus.mp3",
                bpm=162,
                offset=-0.5,
                chart = [
                (1, 8.000), (2, 8.185), (3, 8.370), (1, 8.555),
                (0, 8.740), (1, 8.925), (2, 9.110), (3, 9.295),

                (1, 9.480), (3, 9.750), (2, 9.935), (0, 10.120),
                (1, 10.305), (2, 10.490), (3, 10.675), (1, 10.860),

                # 16분 3연타 패턴
                (2, 11.045), (2, 11.138), (2, 11.230),

                (0, 11.415), (1, 11.600), (3, 11.785), (2, 11.970),
                (1, 12.155), (0, 12.340), (2, 12.525), (3, 12.710),

                # 좌우 대칭 점프 패턴
                (0, 12.895), (3, 12.895),
                (1, 13.080), (2, 13.080),
                (0, 13.265), (3, 13.265),

                (1, 13.450), (2, 13.635), (3, 13.820), (1, 14.005),
                (0, 14.190), (1, 14.375), (2, 14.560), (3, 14.745),

                # 16분 계단
                (0, 14.930), (1, 15.015), (2, 15.100), (3, 15.185),

                (2, 15.370), (1, 15.555), (0, 15.740), (3, 15.925),
                (1, 16.110), (2, 16.295), (3, 16.480), (1, 16.665),

                # 중간 하이라이트 계단+점프
                (0, 16.850), (3, 16.850),
                (1, 17.035), (2, 17.220),
                (0, 17.405), (3, 17.590),

                (1, 17.775), (2, 17.960), (3, 18.145), (1, 18.330),
                (0, 18.515), (1, 18.700), (2, 18.885), (3, 19.070),

                # 32분 같은 빠른 5연타 느낌 반영
                (1, 19.255), (1, 19.332), (1, 19.410), (1, 19.488), (1, 19.565),

                (3, 19.750), (2, 19.935), (1, 20.120), (0, 20.305),
                (1, 20.490), (3, 20.675), (2, 20.860), (1, 21.045),

                # 패턴 밀도 증가
                (0, 21.230), (1, 21.322), (2, 21.415), (3, 21.508),
                (1, 21.600), (2, 21.692), (3, 21.785), (0, 21.878),

                (1, 21.970), (2, 22.155), (3, 22.340), (1, 22.525),
                (0, 22.710), (2, 22.895), (3, 23.080), (1, 23.265),

                # 변주 계단
                (0, 23.450), (1, 23.635), (2, 23.820), (3, 24.005),
                (1, 24.190), (0, 24.375), (2, 24.560), (3, 24.745),

                # A파트 끝부 16분 4타로 마무리
                (1, 24.930), (1, 25.015), (1, 25.100), (1, 25.185),

                # 마무리 직전 계단
                (2, 25.370), (3, 25.555), (1, 25.740), (0, 25.925),
                (1, 26.110), (2, 26.295), (3, 26.480), (1, 26.665),

                # 26.8~32.0 구간 연속 패턴 (밀도 높게)
                (0, 26.850), (1, 27.035), (2, 27.220), (3, 27.405),
                (1, 27.590), (2, 27.775), (3, 27.960), (0, 28.145),

                (1, 28.330), (2, 28.515), (3, 28.700), (1, 28.885),
                (0, 29.070), (2, 29.255), (3, 29.440), (1, 29.625),

                (0, 29.810), (1, 29.995), (2, 30.180), (3, 30.365),
                (1, 30.550), (2, 30.735), (3, 30.920), (1, 31.105),

                (0, 31.290), (2, 31.475), (3, 31.660), (1, 31.845),
                (0, 32.000), (2, 32.185), (3, 32.370), (1, 32.555),
                (0, 32.740), (1, 32.925), (2, 33.110), (3, 33.295),

                (1, 33.480), (2, 33.665), (3, 33.850), (1, 34.035),
                (0, 34.220), (1, 34.405), (2, 34.590), (3, 34.775),

                # 계단 반복
                (0, 34.960), (1, 35.145), (2, 35.330), (3, 35.515),

                (1, 35.700), (2, 35.885), (3, 36.070), (1, 36.255),
                (0, 36.440), (1, 36.625), (2, 36.810), (3, 36.995),

                # 좌우 왕복
                (3, 37.180), (0, 37.180),
                (2, 37.365), (1, 37.550),
                (3, 37.735), (0, 37.920),

                (1, 38.105), (2, 38.290), (3, 38.475), (1, 38.660),
                (0, 38.845), (1, 39.030), (2, 39.215), (3, 39.400),

                # 부드러운 4레인 순환
                (0, 39.585), (1, 39.770), (2, 39.955), (3, 40.140),
                (1, 40.325), (2, 40.510), (3, 40.695), (1, 40.880),

                # 중심 레인 위주의 B파트 멜로디 느낌
                (2, 41.065), (2, 41.250), (1, 41.435), (3, 41.620),

                (0, 41.805), (1, 41.990), (2, 42.175), (3, 42.360),
                (1, 42.545), (2, 42.730), (3, 42.915), (1, 43.100),

                # 약간 더 촘촘한 계단 (난타 최소화)
                (0, 43.285), (1, 43.380), (2, 43.475), (3, 43.570),

                (1, 43.755), (2, 43.940), (3, 44.125), (1, 44.310),
                (0, 44.495), (2, 44.680), (3, 44.865), (1, 45.050),

                # B파트 중반: 점프 + 교차
                (0, 45.235), (3, 45.235),
                (1, 45.420), (2, 45.605),
                (0, 45.790), (3, 45.790),

                (1, 45.975), (2, 46.160), (3, 46.345), (1, 46.530),
                (0, 46.715), (1, 46.900), (2, 47.085), (3, 47.270),

                # 대각선 교차
                (0, 47.455), (3, 47.640), (1, 47.825), (2, 48.010),

                # 레인 흔들기 패턴
                (1, 48.195), (3, 48.380), (2, 48.565), (0, 48.750),
                (1, 48.935), (2, 49.120), (3, 49.305), (1, 49.490),

                # B파트 후반 서서히 밀도 증가
                (0, 49.675), (1, 49.860), (2, 50.045), (3, 50.230),
                (1, 50.415), (2, 50.600), (3, 50.785), (1, 50.970),

                (0, 51.155), (1, 51.340), (3, 51.525), (2, 51.710),
                (1, 51.895), (3, 52.080), (2, 52.265), (1, 52.450),

                # A파트와 연결되는 느낌으로 세기 증가
                (0, 52.635), (1, 52.820), (2, 53.005), (3, 53.190),
                (1, 53.375), (2, 53.560), (3, 53.745), (1, 53.930),

                # B파트 마지막 4초: 고정된 흐름 유지
                (0, 54.115), (2, 54.300), (3, 54.485), (1, 54.670),
                (0, 54.855), (1, 55.040), (2, 55.225), (3, 55.410),
                (1, 55.595), (2, 55.780), (3, 55.965), (1, 56.000), 
                (2, 56.185), (3, 56.370), (1, 56.555),
                (0, 56.740), (1, 56.925), (2, 57.110), (3, 57.295),

                # 대칭 + 계단
                (0, 57.480), (3, 57.480),
                (1, 57.665), (2, 57.665),
                (0, 57.850), (3, 57.850),

                (1, 58.035), (2, 58.220), (3, 58.405), (1, 58.590),
                (0, 58.775), (2, 58.960), (3, 59.145), (1, 59.330),

                # 흐름 유지 구간
                (0, 59.515), (1, 59.700), (2, 59.885), (3, 60.070),
                (2, 60.255), (1, 60.440), (0, 60.625), (3, 60.810),

                # 리듬 강조 (난타 없는 12분 느낌)
                (1, 60.995), (2, 61.088), (3, 61.180),
                (1, 61.365), (2, 61.550), (0, 61.735),

                (1, 61.920), (3, 62.105), (2, 62.290), (1, 62.475),
                (0, 62.660), (1, 62.845), (2, 63.030), (3, 63.215),

                # 교차 + 계단
                (0, 63.400), (2, 63.585), (3, 63.770), (1, 63.955),
                (0, 64.140), (1, 64.325), (2, 64.510), (3, 64.695),

                # C파트 중반: 패턴 강도 ↑ (하지만 난타 없음)
                (1, 64.880), (2, 65.065), (3, 65.250), (1, 65.435),
                (0, 65.620), (1, 65.805), (3, 65.990), (2, 66.175),

                (0, 66.360), (2, 66.545), (3, 66.730), (1, 66.915),
                (0, 67.100), (1, 67.285), (2, 67.470), (3, 67.655),

                # 16분 난타 대신 “연속 12분 계단”으로 타격감 표현
                (0, 67.840), (1, 67.932),
                (0, 68.740), (1, 68.925), (2, 69.110), (3, 69.295),

                (1, 69.480), (3, 69.665), (2, 69.850), (0, 70.035),
                (1, 70.220), (2, 70.405), (3, 70.590), (1, 70.775),

                # A' 계단 강화
                (0, 70.960), (1, 71.145), (2, 71.330), (3, 71.515),
                (1, 71.700), (2, 71.885), (3, 72.070), (1, 72.255),

                # 대칭 + 중심 레인 움직임
                (0, 72.440), (3, 72.440),
                (1, 72.625), (2, 72.810),
                (0, 72.995), (3, 72.995),

                (1, 73.180), (2, 73.365), (3, 73.550), (1, 73.735),
                (0, 73.920), (1, 74.105), (2, 74.290), (3, 74.475),

                # 중간 긴장감 상승
                (0, 74.660), (1, 74.845), (2, 75.030), (3, 75.215),
                (1, 75.400), (2, 75.585), (3, 75.770), (1, 75.955),

                (0, 76.140), (1, 76.325), (3, 76.510), (2, 76.695),
                (0, 76.880), (2, 77.065), (3, 77.250), (1, 77.435),

                # A' 후반 - 패턴 순환
                (0, 77.620), (1, 77.805), (2, 77.990), (3, 78.175),
                (2, 78.360), (1, 78.545), (0, 78.730), (3, 78.915),

                (1, 79.100), (2, 79.285), (3, 79.470), (1, 79.655),
                (0, 79.840), (2, 80.025), (3, 80.210), (1, 80.395),

                # 패턴 강화(난타 없이 미세 촘촘)
                (0, 80.580), (1, 80.672), (2, 80.765), (3, 80.858),
                (1, 81.043), (2, 81.228), (3, 81.413), (1, 81.598),

                (0, 81.783), (1, 81.968), (2, 82.153), (3, 82.338),
                (1, 82.523), (2, 82.708), (3, 82.893), (1, 83.078),

                # 후반부 긴장감 ↑
                (0, 83.263), (1, 83.448), (3, 83.633), (2, 83.818),
                (0, 84.003), (2, 84.188), (3, 84.373), (1, 84.558),

                (0, 84.743), (1, 84.928), (2, 85.113), (3, 85.298),
                (1, 85.483), (2, 85.668), (3, 85.853), (1, 86.038),

                # climax 전
                (0, 86.223), (1, 86.408), (2, 86.593), (3, 86.778),
                (1, 86.963), (3, 87.148), (2, 87.333), (1, 87.518),

                (0, 87.703), (1, 87.888), (2, 88.073), (3, 88.258),
                (1, 88.443), (2, 88.628), (3, 88.813), (1, 88.998),

                # 마지막 10초 — 엔딩 패턴!
                (0, 89.183), (3, 89.368),
                (1, 89.553), (2, 89.738),
                (0, 89.923), (3, 89.923),

                (1, 90.108), (2, 90.293), (3, 90.478), (1, 90.663),
                (0, 90.848), (1, 91.033), (2, 91.218), (3, 91.403),

                (1, 91.588), (3, 91.773), (2, 91.958), (1, 92.143),
                (0, 92.328), (1, 92.513), (2, 92.698), (3, 92.883),

                (1, 93.068), (2, 93.253), (3, 93.438), (1, 93.623),

                # 피날레 4레인 순환
                (0, 93.808), (1, 93.993), (2, 94.178), (3, 94.363),
                (1, 94.548), (2, 94.733), (3, 94.918), (1, 95.103),

                (0, 95.288), (2, 95.473), (3, 95.658), (1, 95.843),
                (0, 96.028), (1, 96.213), (2, 96.398), (3, 96.583),

                # 엔딩부 마무리 계단
                (1, 96.768), (2, 96.953), (3, 97.138), (1, 97.323),
                (0, 97.508), (1, 97.693), (2, 97.878), (3, 98.063),

                (1, 98.248), (0, 98.433), (2, 98.618), (3, 98.803),
                (1, 98.988), (2, 99.173), (3, 99.358), (1, 99.543),

                # 엔딩 피날레 8노트
                (0, 99.728), (1, 99.913), (2, 100.098), (3, 100.283),
            

                ],
                length_hint=102.5,
                start_delay=2.5,
            ),
            Song(
                "Small girl (feat. D.O.)",
                "Small girl.mp3",
                bpm=85,
                offset=0.2,
                chart=[
                    (2, 0.765), (2, 1.912), (3, 2.088),
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
        self.just_started = True
        self.play_mode = self.game_modes[self.selected_mode_idx][0]

        # pause / combo 상태 리셋
        self.is_paused = False
        self.in_resume_countdown = False
        self.resume_countdown = 0.0
        self.pause_tick_ms = 0
        self.paused_raw_now = 0.0
        self.resume_start_ms = 0
        self.last_combo_attack_time = -1.0
        self.last_combo_attack_player = None

    def _back_to_menu(self) -> None:
        self.state = "menu"
        self.audio.stop()
        self.current_song = None
        self.is_paused = False
        self.in_resume_countdown = False
        self.resume_countdown = 0.0
        self.pause_tick_ms = 0
        self.paused_raw_now = 0.0
        self.resume_start_ms = 0
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
            skip_updates = False

            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key(event.key, now)

            # 재시작 직후 첫 프레임: 시간/업데이트 초기화
            if self.just_started:
                tick_now = pygame.time.get_ticks()
                raw_now = 0.0
                now = 0.0
                skip_updates = True
                self.just_started = False

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
                if not self.is_paused and not self.in_resume_countdown and not skip_updates:
                    self.audio.tick()
                    for idx, track in enumerate(self.tracks):
                        missed = track.update_misses(now)
                        if missed and not track.is_down:
                            self._apply_health(idx, "Miss", repeat=missed, now=now)
                self._check_deaths(now)
                if self.state != "play" or self.current_song is None:
                    continue

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
            elif key == pygame.K_LEFT:
                self.selected_mode_idx = (self.selected_mode_idx - 1) % len(self.game_modes)
            elif key == pygame.K_RIGHT:
                self.selected_mode_idx = (self.selected_mode_idx + 1) % len(self.game_modes)
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

            for idx, track in enumerate(self.tracks):
                if track.is_down:
                    continue
                label = track.handle_key(key, now)
                if label:
                    self._apply_health(idx, label, now=now)
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

    # ---- HP / 판정 효과 ----
    def _apply_health(self, actor_idx: int, label: str, repeat: int = 1, now: float = 0.0) -> None:
        actor = self.tracks[actor_idx]
        if actor.is_down:
            return
        victim = self.tracks[1 - actor_idx]

        for _ in range(repeat):
            if label == "Perfect":
                actor.heal(1.5)
            elif label == "Great":
                actor.heal(1.0)
            elif label == "Good":
                actor.heal(0.6)
            elif label == "Bad":
                actor.damage(2.0)
            elif label == "Miss":
                actor.damage(5.0)

        # 콤보에 따른 상대 체력 감소/내 체력 회복
        if label in ("Perfect", "Great", "Good") and actor.combo > 0 and actor.combo % 5 == 0:
            victim.damage(4.0)
            actor.heal(3.0)
            self.last_combo_attack_time = now
            self.last_combo_attack_player = actor_idx

    def _check_deaths(self, now: float) -> None:
        if self.state != "play":
            return
        for i, track in enumerate(self.tracks):
            if not track.just_downed and track.health > 0:
                continue
            # 다운 처리
            track.is_down = True
            track.just_downed = False
            track.combo = 0
            track.last_label = "KO"
            track.last_label_time = now
            if self.play_mode == "sudden":
                winner_idx = 1 - i if self.tracks[1 - i].health > 0 else None
                self._handle_ko(winner_idx)
                return

    def _handle_ko(self, winner_idx: Optional[int]) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._draw_ko_overlay(winner_idx)
        pygame.display.flip()
        self._wait_for_restart()
        if self.state != "play":
            self._back_to_menu()

    # ---- Drawing ----
    def _draw_menu(self) -> None:
        self.screen.fill((18, 18, 24))
        title = self.menu_big_font.render("Two Player Rhythm Battle", True, (240, 240, 240))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 48))
        info_lines = [
            "Controls: P1=QWER, P2=OP[], Up/Down to choose",
            "In game: B=restart, Esc=pause",
            "Paused: Enter/Space=resume (3s), B=restart, Esc=menu",
            "Left/Right: change mode (Sudden KO / Endurance)",
        ]
        y = 150
        for line in info_lines:
            surf = self.menu_font.render(line, True, (210, 210, 210))
            self.screen.blit(surf, (70, y))
            y += 32
        y += 8
        for idx, song in enumerate(self.songs):
            color = (255, 230, 150) if idx == self.selected_song_idx else (190, 190, 190)
            prefix = "➤ " if idx == self.selected_song_idx else "  "
            label = f"{prefix}{song.name} (bpm {song.bpm}, diff {song.difficulty:.1f})"
            surf = self.menu_font.render(label, True, color)
            self.screen.blit(surf, (90, y))
            y += 36
        mode_code, mode_label = self.game_modes[self.selected_mode_idx]
        mode_text = f"Mode: {mode_label} ({'stop on KO' if mode_code=='sudden' else 'play to end'})"
        mode_surf = self.menu_font.render(mode_text, True, (220, 220, 220))
        self.screen.blit(mode_surf, (70, y + 12))

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
        band_height = 170
        band = pygame.Surface((self.width, band_height), pygame.SRCALPHA)
        pygame.draw.rect(band, (255, 255, 255, 18), (0, 0, self.width, band_height), border_radius=18)
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
        panel_rect = pygame.Rect(track.x + 16, 16, track.width - 32, 140)
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

        top_y = panel_rect.y + 12
        self.screen.blit(name_surf, (panel_rect.x + 14, top_y))
        self.screen.blit(keys_surf, (panel_rect.right - keys_surf.get_width() - 14, top_y))

        mid_y = panel_rect.y + 62
        self.screen.blit(score_surf, (panel_rect.x + 14, mid_y))
        self.screen.blit(combo_surf, (panel_rect.right - combo_surf.get_width() - 14, mid_y))

        self._draw_health_bar(track, panel_rect)
        if track.is_down:
            down_surf = self.font.render("DOWN", True, (255, 120, 120))
            self.screen.blit(down_surf, (panel_rect.right - down_surf.get_width() - 14, panel_rect.y + 96))

    def _draw_health_bar(self, track: Track, panel_rect: pygame.Rect) -> None:
        hp_pct = max(0.0, min(1.0, track.health / track.max_health))
        bar_rect = pygame.Rect(panel_rect.x + 14, panel_rect.y + panel_rect.height - 30, panel_rect.width - 28, 12)
        pygame.draw.rect(self.screen, (30, 30, 40), bar_rect, border_radius=4)
        fill_w = int(bar_rect.width * hp_pct)
        if fill_w > 0:
            hp_color = (
                int(230 - 150 * hp_pct),
                int(80 + 120 * hp_pct),
                int(90 + 40 * hp_pct),
            )
            pygame.draw.rect(self.screen, hp_color, (bar_rect.x, bar_rect.y, fill_w, bar_rect.height), border_radius=4)
        pygame.draw.rect(self.screen, (*track.color, 140), bar_rect, width=2, border_radius=4)
        hp_text = self.font.render(f"HP {int(track.health)}/{int(track.max_health)}", True, (235, 235, 235))
        self.screen.blit(hp_text, (bar_rect.x, bar_rect.y - 20))

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
        info_y = self.height - 48
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

        # 중앙에 HP 이펙트 텍스트
        text = self.big_font.render("HP DRAIN!", True, (255, 255, 255))
        text.set_alpha(alpha)
        cx = victim_track.x + victim_track.width // 2 - text.get_width() // 2
        cy = self.height // 2 - text.get_height() // 2
        self.screen.blit(text, (cx, cy))

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        p1, p2 = self.tracks
        both_alive = p1.health > 0 and p2.health > 0
        if self.play_mode == "endurance" and both_alive:
            title = "Clear!"
            winner = None
        else:
            # 우선 체력, 동률이면 점수
            if p1.health == p2.health:
                winner = "Draw" if p1.score == p2.score else ("Player 1" if p1.score > p2.score else "Player 2")
            else:
                winner = "Player 1" if p1.health > p2.health else "Player 2"
            title = f"Winner: {winner}" if winner != "Draw" else "Draw"
        lines = [
            "Song complete!",
            f"P1 Score: {p1.score} | HP: {int(p1.health)}",
            f"P2 Score: {p2.score} | HP: {int(p2.health)}",
            title if self.play_mode == "endurance" or not both_alive else "Clear!",
            "B: restart | Esc: quit song | wait: menu",
        ]
        y = self.height // 2 - 70
        for line in lines:
            surf = self.big_font.render(line, True, (240, 240, 240))
            rect = surf.get_rect(center=(self.width // 2, y))
            self.screen.blit(surf, rect)
            y += 44

    def _draw_ko_overlay(self, winner_idx: Optional[int]) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        winner_text = "Draw" if winner_idx is None else f"Player {winner_idx + 1} Wins!"
        lines = [
            "KO!",
            winner_text,
            "B: restart | Esc: quit song",
        ]
        y = self.height // 2 - 40
        for line in lines:
            surf = self.big_font.render(line, True, (240, 240, 240))
            rect = surf.get_rect(center=(self.width // 2, y))
            self.screen.blit(surf, rect)
            y += 48

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
