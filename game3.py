import pygame
import os
import librosa
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
from pathlib import Path

# 초기화
pygame.init()
pygame.mixer.init()

# 상수 정의
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BLUE = (70, 70, 150)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)
PURPLE = (150, 50, 150)

class GameState(Enum):
    """게임 상태"""
    MUSIC_SELECT = "MUSIC_SELECT"
    READY = "READY"
    PLAYING = "PLAYING"
    FINISHED = "FINISHED"

class JudgmentType(Enum):
    """판정 타입"""
    PERFECT = "PERFECT"
    GREAT = "GREAT"
    GOOD = "GOOD"
    MISS = "MISS"

@dataclass
class Judgment:
    """판정 정보"""
    type: JudgmentType
    time: int
    position: Tuple[int, int]

@dataclass
class NotePattern:
    """노트 패턴 정보"""
    time: float  # 초 단위
    lane: int

@dataclass
class MusicInfo:
    """음악 정보"""
    path: str
    title: str
    bpm: float
    duration: float

class AudioAnalyzer:
    """오디오 분석 클래스 - BPM 및 비트 감지"""
    
    @staticmethod
    def analyze_audio(file_path: str) -> Tuple[float, np.ndarray]:
        """
        오디오 파일 분석
        Returns: (bpm, beat_times)
        """
        print(f"분석 중: {file_path}")
        
        try:
            # 오디오 로드
            y, sr = librosa.load(file_path)
            
            # BPM 감지
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # 비트 타이밍 계산 (초 단위)
            beat_times = librosa.frames_to_time(beats, sr=sr)
            
            print(f"BPM: {tempo:.1f}, 비트 수: {len(beat_times)}")
            
            return float(tempo), beat_times
            
        except Exception as e:
            print(f"오디오 분석 실패: {e}")
            # 기본값 반환
            return 120.0, np.array([])
    
    @staticmethod
    def get_duration(file_path: str) -> float:
        """오디오 파일 길이 반환 (초)"""
        try:
            y, sr = librosa.load(file_path)
            return len(y) / sr
        except:
            return 0.0

class BeatmapGenerator:
    """비트맵 생성기 - 실제 음악 비트에 맞춘 패턴"""
    
    def __init__(self, beat_times: np.ndarray, bpm: float):
        self.beat_times = beat_times
        self.bpm = bpm
        self.patterns = self.generate_beatmap()
    
    def generate_beatmap(self) -> List[NotePattern]:
        """비트 타이밍에 맞춰 노트 패턴 생성"""
        patterns = []
        
        if len(self.beat_times) == 0:
            # 비트 감지 실패시 BPM 기반으로 생성
            return self.generate_fallback_beatmap()
        
        for i, beat_time in enumerate(self.beat_times):
            # 대부분의 비트에 노트 생성
            if np.random.random() < 0.85:
                lane = np.random.randint(0, 4)
                patterns.append(NotePattern(float(beat_time), lane))
            
            # 강박(4비트마다)에 추가 노트
            if i % 4 == 0 and np.random.random() < 0.4:
                lane2 = np.random.randint(0, 4)
                if patterns and lane2 != patterns[-1].lane:
                    patterns.append(NotePattern(float(beat_time), lane2))
        
        return sorted(patterns, key=lambda p: p.time)
    
    def generate_fallback_beatmap(self) -> List[NotePattern]:
        """비트 감지 실패시 BPM 기반 생성"""
        patterns = []
        beat_interval = 60.0 / self.bpm
        current_time = 2.0
        duration = 120.0
        
        while current_time < duration:
            for beat in range(4):
                if np.random.random() < 0.8:
                    lane = np.random.randint(0, 4)
                    patterns.append(NotePattern(current_time + beat * beat_interval, lane))
            current_time += beat_interval * 4
        
        return sorted(patterns, key=lambda p: p.time)

class MusicLibrary:
    """음악 라이브러리 관리"""
    
    def __init__(self, music_folder: str = "music"):
        self.music_folder = music_folder
        self.music_list: List[MusicInfo] = []
        self.load_music_library()
    
    def load_music_library(self):
        """음악 폴더에서 음악 파일 로드"""
        # music 폴더가 없으면 생성
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            print(f"'{self.music_folder}' 폴더를 생성했습니다. MP3/WAV 파일을 넣어주세요.")
            return
        
        # 지원하는 오디오 포맷
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac'}
        
        for file in os.listdir(self.music_folder):
            file_path = os.path.join(self.music_folder, file)
            ext = Path(file).suffix.lower()
            
            if ext in audio_extensions:
                try:
                    # 음악 정보 분석
                    bpm, _ = AudioAnalyzer.analyze_audio(file_path)
                    duration = AudioAnalyzer.get_duration(file_path)
                    
                    title = Path(file).stem  # 확장자 제외한 파일명
                    
                    music_info = MusicInfo(
                        path=file_path,
                        title=title,
                        bpm=bpm,
                        duration=duration
                    )
                    
                    self.music_list.append(music_info)
                    print(f"로드 완료: {title} (BPM: {bpm:.1f})")
                    
                except Exception as e:
                    print(f"로드 실패 - {file}: {e}")
        
        if not self.music_list:
            print("음악 파일이 없습니다. 'music' 폴더에 MP3/WAV 파일을 추가하세요.")

class MusicPlayer:
    """음악 재생 관리"""
    
    def __init__(self):
        self.playing = False
        self.start_time = 0
        self.current_music: Optional[MusicInfo] = None
    
    def load_music(self, music_info: MusicInfo):
        """음악 로드"""
        try:
            pygame.mixer.music.load(music_info.path)
            self.current_music = music_info
            print(f"음악 로드: {music_info.title}")
        except Exception as e:
            print(f"음악 로드 실패: {e}")
    
    def start(self):
        """음악 시작"""
        if self.current_music:
            pygame.mixer.music.play()
            self.playing = True
            self.start_time = pygame.time.get_ticks()
    
    def get_current_time(self) -> float:
        """현재 음악 시간 (초)"""
        if not self.playing:
            return 0.0
        return (pygame.time.get_ticks() - self.start_time) / 1000.0
    
    def stop(self):
        """음악 정지"""
        pygame.mixer.music.stop()
        self.playing = False
    
    def set_volume(self, volume: float):
        """볼륨 설정 (0.0 ~ 1.0)"""
        pygame.mixer.music.set_volume(volume)

class Note:
    """노트 클래스"""
    
    def __init__(self, lane: int, y: float, speed: float):
        self.lane = lane
        self.y = y
        self.speed = speed
        self.width = 50
        self.height = 15
        self.active = True
    
    def update(self, dt: float):
        """노트 위치 업데이트"""
        self.y += self.speed * dt
    
    def draw(self, screen: pygame.Surface, x: int):
        """노트 그리기"""
        if self.active:
            pygame.draw.rect(screen, WHITE, 
                           (x + self.lane * 60, self.y, self.width, self.height))
    
    def is_off_screen(self) -> bool:
        """화면 밖으로 나갔는지 확인"""
        return self.y > SCREEN_HEIGHT + 50

class Player:
    """플레이어 클래스"""
    
    def __init__(self, name: str, x: int, keys: List[int], color: Tuple[int, int, int]):
        self.name = name
        self.x = x
        self.keys = keys
        self.color = color
        self.lanes = 4
        self.lane_width = 60
        self.judgment_line_y = SCREEN_HEIGHT - 100
        self.score = 0
        self.combo = 0
        self.notes: List[Note] = []
        self.pressed_lanes = [False] * self.lanes
        self.judgments: List[Judgment] = []
        self.ready = False
    
    def add_note(self, lane: int, speed: float):
        """노트 추가"""
        self.notes.append(Note(lane, -50, speed))
    
    def reset(self):
        """게임 리셋"""
        self.score = 0
        self.combo = 0
        self.notes.clear()
        self.judgments.clear()
        self.pressed_lanes = [False] * self.lanes
        self.ready = False
    
    def update(self, dt: float):
        """플레이어 상태 업데이트"""
        for note in self.notes:
            note.update(dt)
        
        for note in self.notes[:]:
            if note.is_off_screen() and note.active:
                note.active = False
                self.add_judgment(JudgmentType.MISS, 
                                self.x + note.lane * self.lane_width + 25,
                                self.judgment_line_y)
                self.combo = 0
        
        self.notes = [n for n in self.notes if not n.is_off_screen()]
        
        current_time = pygame.time.get_ticks()
        self.judgments = [j for j in self.judgments if current_time - j.time < 500]
    
    def handle_key_press(self, lane: int):
        """키 입력 처리"""
        self.pressed_lanes[lane] = True
        
        closest_note = None
        min_distance = float('inf')
        
        for note in self.notes:
            if note.lane == lane and note.active:
                distance = abs(note.y + note.height/2 - self.judgment_line_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_note = note
        
        if closest_note and min_distance < 100:
            self.judge_note(closest_note, min_distance)
    
    def handle_key_release(self, lane: int):
        """키 릴리즈 처리"""
        self.pressed_lanes[lane] = False
    
    def judge_note(self, note: Note, distance: float):
        """노트 판정"""
        note.active = False
        x = self.x + note.lane * self.lane_width + 25
        
        if distance < 20:
            judgment = JudgmentType.PERFECT
            self.score += 100
            self.combo += 1
        elif distance < 40:
            judgment = JudgmentType.GREAT
            self.score += 70
            self.combo += 1
        elif distance < 60:
            judgment = JudgmentType.GOOD
            self.score += 40
            self.combo += 1
        else:
            judgment = JudgmentType.MISS
            self.combo = 0
        
        self.add_judgment(judgment, x, self.judgment_line_y)
    
    def add_judgment(self, judgment_type: JudgmentType, x: int, y: int):
        """판정 메시지 추가"""
        self.judgments.append(Judgment(
            judgment_type,
            pygame.time.get_ticks(),
            (x, y)
        ))
    
    def draw(self, screen: pygame.Surface):
        """플레이어 화면 그리기"""
        pygame.draw.rect(screen, self.color, 
                        (self.x - 10, 0, self.lane_width * self.lanes + 20, SCREEN_HEIGHT))
        
        game_rect = pygame.Rect(self.x, 0, self.lane_width * self.lanes, SCREEN_HEIGHT)
        pygame.draw.rect(screen, BLACK, game_rect)
        
        for i in range(1, self.lanes):
            x = self.x + i * self.lane_width
            pygame.draw.line(screen, DARK_GRAY, (x, 0), (x, SCREEN_HEIGHT), 2)
        
        pygame.draw.line(screen, RED, 
                        (self.x, self.judgment_line_y),
                        (self.x + self.lane_width * self.lanes, self.judgment_line_y), 3)
        
        for note in self.notes:
            note.draw(screen, self.x)
        
        for i, pressed in enumerate(self.pressed_lanes):
            if pressed:
                pygame.draw.rect(screen, WHITE, 
                               (self.x + i * self.lane_width, 
                                self.judgment_line_y - 20, 
                                self.lane_width, 40), 2)
        
        font = pygame.font.Font(None, 36)
        for judgment in self.judgments:
            color = WHITE
            if judgment.type == JudgmentType.PERFECT:
                color = (255, 255, 0)
            elif judgment.type == JudgmentType.GREAT:
                color = (0, 255, 0)
            elif judgment.type == JudgmentType.GOOD:
                color = (0, 150, 255)
            elif judgment.type == JudgmentType.MISS:
                color = (255, 0, 0)
            
            text = font.render(judgment.type.value, True, color)
            screen.blit(text, (judgment.position[0] - text.get_width()//2, 
                             judgment.position[1] - 60))
        
        if self.combo > 0:
            combo_font = pygame.font.Font(None, 48)
            combo_text = combo_font.render(str(self.combo), True, WHITE)
            screen.blit(combo_text, 
                       (self.x + self.lane_width * 2 - combo_text.get_width()//2, 
                        self.judgment_line_y + 60))

class SyncedNoteSpawner:
    """동기화된 노트 생성기"""
    
    def __init__(self, beatmap: BeatmapGenerator, base_speed: float, judgment_line_y: float):
        self.beatmap = beatmap
        self.base_speed = base_speed
        self.judgment_line_y = judgment_line_y
        self.spawned_patterns = set()
        
        spawn_distance = SCREEN_HEIGHT + 50 + self.judgment_line_y
        self.spawn_ahead_time = spawn_distance / self.base_speed
    
    def update(self, current_music_time: float, player1: Player, player2: Player):
        """비트맵에 따라 노트 생성"""
        spawn_time = current_music_time + self.spawn_ahead_time
        
        for i, pattern in enumerate(self.beatmap.patterns):
            if i in self.spawned_patterns:
                continue
                
            if pattern.time <= spawn_time:
                player1.add_note(pattern.lane, self.base_speed)
                player2.add_note(pattern.lane, self.base_speed)
                self.spawned_patterns.add(i)
    
    def reset(self):
        """스포너 리셋"""
        self.spawned_patterns.clear()

class Game:
    """게임 메인 클래스"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2P Rhythm Game - Music Select")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MUSIC_SELECT
        
        # 플레이어 초기화
        self.player1 = Player("1P", 50, 
                             [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f],
                             GRAY)
        self.player2 = Player("2P", 650,
                             [pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_SEMICOLON],
                             BLUE)
        
        # 음악 라이브러리
        self.music_library = MusicLibrary()
        self.selected_music_index = 0
        
        # 게임 요소들 (음악 선택 후 초기화)
        self.music = MusicPlayer()
        self.beatmap: Optional[BeatmapGenerator] = None
        self.note_spawner: Optional[SyncedNoteSpawner] = None
        self.speed = 200.0
    
    def select_music(self, music_info: MusicInfo):
        """음악 선택 및 게임 준비"""
        print(f"\n선택된 음악: {music_info.title}")
        print(f"BPM: {music_info.bpm:.1f}, 길이: {music_info.duration:.1f}초")
        
        # 음악 로드
        self.music.load_music(music_info)
        
        # 비트 분석 및 비트맵 생성
        print("비트 분석 중...")
        bpm, beat_times = AudioAnalyzer.analyze_audio(music_info.path)
        self.beatmap = BeatmapGenerator(beat_times, bpm)
        
        # 노트 생성기 초기화
        self.note_spawner = SyncedNoteSpawner(
            self.beatmap,
            self.speed,
            self.player1.judgment_line_y
        )
        
        # 준비 화면으로 전환
        self.state = GameState.READY
        pygame.display.set_caption(f"2P Rhythm Game - {music_info.title}")
    
    def start_game(self):
        """게임 시작"""
        self.state = GameState.PLAYING
        self.player1.reset()
        self.player2.reset()
        if self.note_spawner:
            self.note_spawner.reset()
        self.music.start()
    
    def check_ready(self):
        """두 플레이어 모두 준비되었는지 확인"""
        if self.player1.ready and self.player2.ready:
            self.start_game()
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # 음악 선택 화면
                if self.state == GameState.MUSIC_SELECT:
                    if event.key == pygame.K_UP:
                        self.selected_music_index = (self.selected_music_index - 1) % max(1, len(self.music_library.music_list))
                    elif event.key == pygame.K_DOWN:
                        self.selected_music_index = (self.selected_music_index + 1) % max(1, len(self.music_library.music_list))
                    elif event.key == pygame.K_RETURN and self.music_library.music_list:
                        self.select_music(self.music_library.music_list[self.selected_music_index])
                
                # 준비 화면
                elif self.state == GameState.READY:
                    if event.key in self.player1.keys:
                        self.player1.ready = True
                        self.check_ready()
                    
                    if event.key in self.player2.keys:
                        self.player2.ready = True
                        self.check_ready()
                    
                    if event.key == pygame.K_BACKSPACE:
                        self.state = GameState.MUSIC_SELECT
                        self.music.stop()
                
                # 게임 중
                elif self.state == GameState.PLAYING:
                    for i, key in enumerate(self.player1.keys):
                        if event.key == key:
                            self.player1.handle_key_press(i)
                    
                    for i, key in enumerate(self.player2.keys):
                        if event.key == key:
                            self.player2.handle_key_press(i)
                
                # ESC로 종료
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # R키로 재시작
                if event.key == pygame.K_r and self.state == GameState.PLAYING:
                    self.state = GameState.READY
                    self.player1.reset()
                    self.player2.reset()
                    self.music.stop()
            
            elif event.type == pygame.KEYUP:
                if self.state == GameState.PLAYING:
                    for i, key in enumerate(self.player1.keys):
                        if event.key == key:
                            self.player1.handle_key_release(i)
                    
                    for i, key in enumerate(self.player2.keys):
                        if event.key == key:
                            self.player2.handle_key_release(i)
    
    def update(self, dt: float):
        """게임 상태 업데이트"""
        if self.state == GameState.PLAYING:
            current_music_time = self.music.get_current_time()
            
            if self.note_spawner:
                self.note_spawner.update(current_music_time, self.player1, self.player2)
            
            self.player1.update(dt)
            self.player2.update(dt)
    
    def draw(self):
        """화면 그리기"""
        self.screen.fill(BLACK)
        
        if self.state == GameState.MUSIC_SELECT:
            self.draw_music_select()
        elif self.state == GameState.READY:
            self.draw_ready_screen()
        elif self.state == GameState.PLAYING:
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            self.draw_ui()
        
        pygame.display.flip()
    
    def draw_music_select(self):
        """음악 선택 화면"""
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("MUSIC SELECT", True, PURPLE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        
        if not self.music_library.music_list:
            info_font = pygame.font.Font(None, 36)
            info_text = info_font.render("'music' 폴더에 MP3/WAV 파일을 추가하세요", True, RED)
            self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 250))
            
            guide_font = pygame.font.Font(None, 28)
            guide_text = guide_font.render("프로그램을 재시작하면 음악이 로드됩니다", True, GRAY)
            self.screen.blit(guide_text, (SCREEN_WIDTH//2 - guide_text.get_width()//2, 300))
        else:
            # 음악 리스트 표시
            list_y = 180
            for i, music in enumerate(self.music_library.music_list):
                color = YELLOW if i == self.selected_music_index else WHITE
                font_size = 48 if i == self.selected_music_index else 36
                font = pygame.font.Font(None, font_size)
                
                # 음악 제목
                text = font.render(f"{music.title}", True, color)
                self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, list_y))
                
                # 음악 정보
                if i == self.selected_music_index:
                    info_font = pygame.font.Font(None, 28)
                    info_text = info_font.render(
                        f"BPM: {music.bpm:.1f}  |  {music.duration:.0f}초",
                        True, GRAY
                    )
                    self.screen.blit(info_text, 
                                   (SCREEN_WIDTH//2 - info_text.get_width()//2, list_y + 40))
                    list_y += 100
                else:
                    list_y += 60
        
        # 컨트롤 안내
        control_font = pygame.font.Font(None, 24)
        control_text = control_font.render(
            "↑↓: 선택  |  ENTER: 확인  |  ESC: 종료",
            True, GRAY
        )
        self.screen.blit(control_text, 
                        (SCREEN_WIDTH//2 - control_text.get_width()//2, SCREEN_HEIGHT - 50))
    
    def draw_ready_screen(self):
        """준비 화면"""
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("READY", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        
        # 1P 영역
        p1_x = 200
        p1_y = 300
        p1_color = GREEN if self.player1.ready else GRAY
        pygame.draw.rect(self.screen, p1_color, (p1_x - 100, p1_y - 50, 200, 100), 3)
        
        font = pygame.font.Font(None, 48)
        p1_text = font.render("1P", True, p1_color)
        self.screen.blit(p1_text, (p1_x - p1_text.get_width()//2, p1_y - 20))
        
        info_font = pygame.font.Font(None, 32)
        p1_status = "READY!" if self.player1.ready else "Press A/S/D/F"
        p1_status_text = info_font.render(p1_status, True, p1_color)
        self.screen.blit(p1_status_text, (p1_x - p1_status_text.get_width()//2, p1_y + 20))
        
        # 2P 영역
        p2_x = 1000
        p2_y = 300
        p2_color = GREEN if self.player2.ready else BLUE
        pygame.draw.rect(self.screen, p2_color, (p2_x - 100, p2_y - 50, 200, 100), 3)
        
        p2_text = font.render("2P", True, p2_color)
        self.screen.blit(p2_text, (p2_x - p2_text.get_width()//2, p2_y - 20))
        
        p2_status = "READY!" if self.player2.ready else "Press J/K/L/;"
        p2_status_text = info_font.render(p2_status, True, p2_color)
        self.screen.blit(p2_status_text, (p2_x - p2_status_text.get_width()//2, p2_y + 20))
        
        # 안내 메시지
        if self.player1.ready and self.player2.ready:
            start_font = pygame.font.Font(None, 56)
            start_text = start_font.render("STARTING...", True, YELLOW)
            self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 450))
        
        # 하단 정보
        bottom_font = pygame.font.Font(None, 24)
        bottom_text = bottom_font.render("BACKSPACE: 음악 선택  |  ESC: 종료", True, GRAY)
        self.screen.blit(bottom_text, (SCREEN_WIDTH//2 - bottom_text.get_width()//2, 
                                      SCREEN_HEIGHT - 30))
    
    def draw_ui(self):
        """게임 UI"""
        font = pygame.font.Font(None, 36)
        
        score1_text = font.render(f"{self.player1.score}", True, WHITE)
        self.screen.blit(score1_text, (self.player1.x + 180, 20))
        
        score2_text = font.render(f"{self.player2.score}", True, WHITE)
        self.screen.blit(score2_text, (self.player2.x + 180, 20))
        
        title_font = pygame.font.Font(None, 48)
        if self.music.current_music:
            title_text = title_font.render(self.music.current_music.title, True, WHITE)
            self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        time_text = font.render(f"Time: {self.music.get_current_time():.1f}s", True, GRAY)
        self.screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, 60))
        
        info_font = pygame.font.Font(None, 24)
        info_text = info_font.render("R: Restart  |  ESC: Quit", True, GRAY)
        self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 
                                    SCREEN_HEIGHT - 30))
    
    def run(self):
        """게임 실행"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()

# 게임 실행
if __name__ == "__main__":
    print("=" * 60)
    print("2P RHYTHM GAME")
    print("=" * 60)
    print("\n사용 방법:")
    print("  1. ↑↓ 키로 음악을 선택하고 ENTER로 확인")
    print("  2. 키를 눌러 양쪽 플레이어가 준비되면 게임 시작!")
    print("=" * 60)
    print()
    
    game = Game()
    game.run()