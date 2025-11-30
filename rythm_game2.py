import pygame
import random
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

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

class GameState(Enum):
    """게임 상태"""
    READY = "READY"
    PLAYING = "PLAYING"
    FINISHED = "FINISHED"

@dataclass
class NotePattern:
    """노트 패턴 정보"""
    time: float  # 초 단위
    lane: int

class BeatmapGenerator:
    """비트맵 생성기 - 음악 리듬에 맞는 노트 패턴 생성"""
    def __init__(self, bpm: int = 120):
        self.bpm = bpm
        self.beat_interval = 60.0 / bpm  # 1비트의 시간(초)
        self.patterns = self.generate_beatmap()
    
    def generate_beatmap(self) -> List[NotePattern]:
        """비트맵 생성 - 음악 리듬에 맞춘 패턴"""
        patterns = []
        current_time = 2.0  # 2초 후부터 시작
        duration = 120.0  # 120초 (2분) 플레이
        
        while current_time < duration:
            # 4비트 패턴 (4/4박자)
            for beat in range(4):
                if random.random() < 0.8:  # 80% 확률로 노트 생성
                    lane = random.randint(0, 3)
                    patterns.append(NotePattern(current_time + beat * self.beat_interval, lane))
            
            # 가끔 동시 타격 추가
            if random.random() < 0.3:
                lane2 = random.randint(0, 3)
                if patterns:
                    patterns.append(NotePattern(patterns[-1].time, lane2))
            
            current_time += self.beat_interval * 4  # 4비트 후 다음 패턴
        
        return sorted(patterns, key=lambda p: p.time)

class MusicPlayer:
    """음악 재생 관리"""
    def __init__(self):
        self.playing = False
        self.start_time = 0
        self.bpm = 120
        
        # 간단한 비트 사운드 생성
        self.create_beat_sound()
    
    def create_beat_sound(self):
        """비트 사운드 생성"""
        try:
            # 간단한 비프음 생성 (440Hz, 0.1초)
            sample_rate = 22050
            duration = 0.1
            frequency = 440
            
            n_samples = int(round(duration * sample_rate))
            buf = []
            for i in range(n_samples):
                value = int(32767 * 0.3 * pygame.math.Vector2(1, 0).rotate(
                    360.0 * frequency * i / sample_rate).x)
                buf.append([value, value])
            
            self.beat_sound = pygame.sndarray.make_sound(buf)
        except:
            self.beat_sound = None
    
    def start(self):
        """음악 시작"""
        self.playing = True
        self.start_time = pygame.time.get_ticks()
    
    def get_current_time(self) -> float:
        """현재 음악 시간 (초)"""
        if not self.playing:
            return 0.0
        return (pygame.time.get_ticks() - self.start_time) / 1000.0
    
    def play_beat(self):
        """비트 사운드 재생"""
        if self.beat_sound:
            self.beat_sound.play()
    
    def stop(self):
        """음악 정지"""
        self.playing = False
        pygame.mixer.stop()
    """판정 타입"""
    PERFECT = "PERFECT"
    GREAT = "GREAT"
    GOOD = "GOOD"
    MISS = "MISS"

class JudgmentType(Enum):
    """판정 타입"""
    PERFECT = "PERFECT"
    GREAT = "GREAT"
    GOOD = "GOOD"
    MISS = "MISS"
    """판정 정보"""
    type: JudgmentType
    time: int
    position: Tuple[int, int]

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
        self.ready = False  # 준비 상태
        
    def add_note(self, lane: int, speed: float, spawn_y: float = -50):
        """노트 추가"""
        self.notes.append(Note(lane, spawn_y, speed))
    
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
        # 노트 업데이트
        for note in self.notes:
            note.update(dt)
        
        # 화면 밖 노트 제거 및 MISS 처리
        for note in self.notes[:]:
            if note.is_off_screen() and note.active:
                note.active = False
                self.add_judgment(JudgmentType.MISS, 
                                self.x + note.lane * self.lane_width + 25,
                                self.judgment_line_y)
                self.combo = 0
        
        self.notes = [n for n in self.notes if not n.is_off_screen()]
        
        # 판정 메시지 업데이트
        current_time = pygame.time.get_ticks()
        self.judgments = [j for j in self.judgments if current_time - j.time < 500]
    
    def handle_key_press(self, lane: int):
        """키 입력 처리"""
        self.pressed_lanes[lane] = True
        
        # 해당 레인의 가장 가까운 노트 찾기
        closest_note = None
        min_distance = float('inf')
        
        for note in self.notes:
            if note.lane == lane and note.active:
                distance = abs(note.y + note.height/2 - self.judgment_line_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_note = note
        
        # 판정
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
        # 배경
        pygame.draw.rect(screen, self.color, 
                        (self.x - 10, 0, self.lane_width * self.lanes + 20, SCREEN_HEIGHT))
        
        # 게임 영역
        game_rect = pygame.Rect(self.x, 0, self.lane_width * self.lanes, SCREEN_HEIGHT)
        pygame.draw.rect(screen, BLACK, game_rect)
        
        # 레인 구분선
        for i in range(1, self.lanes):
            x = self.x + i * self.lane_width
            pygame.draw.line(screen, DARK_GRAY, (x, 0), (x, SCREEN_HEIGHT), 2)
        
        # 판정선
        pygame.draw.line(screen, RED, 
                        (self.x, self.judgment_line_y),
                        (self.x + self.lane_width * self.lanes, self.judgment_line_y), 3)
        
        # 노트 그리기
        for note in self.notes:
            note.draw(screen, self.x)
        
        # 키 프레스 효과
        for i, pressed in enumerate(self.pressed_lanes):
            if pressed:
                pygame.draw.rect(screen, WHITE, 
                               (self.x + i * self.lane_width, 
                                self.judgment_line_y - 20, 
                                self.lane_width, 40), 2)
        
        # 판정 메시지
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
        
        # 콤보 표시
        if self.combo > 0:
            combo_font = pygame.font.Font(None, 48)
            combo_text = combo_font.render(str(self.combo), True, WHITE)
            screen.blit(combo_text, 
                       (self.x + self.lane_width * 2 - combo_text.get_width()//2, 
                        self.judgment_line_y + 60))

class SyncedNoteSpawner:
    """동기화된 노트 생성기 - 비트맵 기반"""
    def __init__(self, beatmap: BeatmapGenerator, base_speed: float, judgment_line_y: float):
        self.beatmap = beatmap
        self.base_speed = base_speed
        self.judgment_line_y = judgment_line_y
        self.pattern_index = 0
        self.spawned_patterns = set()
        
        # 노트가 판정선에 도달하는 시간 계산
        spawn_distance = SCREEN_HEIGHT + 50 + self.judgment_line_y
        self.spawn_ahead_time = spawn_distance / self.base_speed  # 초 단위
    
    def update(self, current_music_time: float, player1: Player, player2: Player):
        """비트맵에 따라 노트 생성"""
        # 현재 시간 + 미리 생성 시간
        spawn_time = current_music_time + self.spawn_ahead_time
        
        # 생성해야 할 패턴 찾기
        for i, pattern in enumerate(self.beatmap.patterns):
            if i in self.spawned_patterns:
                continue
                
            if pattern.time <= spawn_time:
                # 양쪽 플레이어에게 동일한 노트 추가
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
        pygame.display.set_caption("2P Rhythm Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.READY
        
        # 플레이어 초기화
        self.player1 = Player("1P", 50, 
                             [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f],
                             GRAY)
        self.player2 = Player("2P", 650,
                             [pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_SEMICOLON],
                             BLUE)
        
        # 음악 및 비트맵
        self.music = MusicPlayer()
        self.beatmap = BeatmapGenerator(bpm=120)
        self.speed = 200.0  # 픽셀/초
        
        # 노트 생성기
        self.note_spawner = SyncedNoteSpawner(
            self.beatmap, 
            self.speed,
            self.player1.judgment_line_y
        )
    
    def start_game(self):
        """게임 시작"""
        self.state = GameState.PLAYING
        self.player1.reset()
        self.player2.reset()
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
                # 준비 화면에서 키 입력
                if self.state == GameState.READY:
                    # 1P 준비
                    if event.key in self.player1.keys:
                        self.player1.ready = True
                        self.check_ready()
                    
                    # 2P 준비
                    if event.key in self.player2.keys:
                        self.player2.ready = True
                        self.check_ready()
                
                # 게임 중 키 입력
                elif self.state == GameState.PLAYING:
                    # 1P 키 처리
                    for i, key in enumerate(self.player1.keys):
                        if event.key == key:
                            self.player1.handle_key_press(i)
                    
                    # 2P 키 처리
                    for i, key in enumerate(self.player2.keys):
                        if event.key == key:
                            self.player2.handle_key_press(i)
                
                # ESC로 종료
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # R키로 재시작
                if event.key == pygame.K_r:
                    self.state = GameState.READY
                    self.player1.reset()
                    self.player2.reset()
            
            elif event.type == pygame.KEYUP:
                if self.state == GameState.PLAYING:
                    # 1P 키 릴리즈
                    for i, key in enumerate(self.player1.keys):
                        if event.key == key:
                            self.player1.handle_key_release(i)
                    
                    # 2P 키 릴리즈
                    for i, key in enumerate(self.player2.keys):
                        if event.key == key:
                            self.player2.handle_key_release(i)
    
    def update(self, dt: float):
        """게임 상태 업데이트"""
        if self.state == GameState.PLAYING:
            current_music_time = self.music.get_current_time()
            
            # 노트 생성
            self.note_spawner.update(current_music_time, self.player1, self.player2)
            
            # 플레이어 업데이트
            self.player1.update(dt)
            self.player2.update(dt)
    
    def draw(self):
        """화면 그리기"""
        self.screen.fill(BLACK)
        
        if self.state == GameState.READY:
            self.draw_ready_screen()
        elif self.state == GameState.PLAYING:
            # 플레이어 그리기
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            
            # UI 그리기
            self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ready_screen(self):
        """준비 화면 그리기"""
        # 타이틀
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("2P RHYTHM GAME", True, WHITE)
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
        else:
            info_text = info_font.render("Press any key to ready up!", True, WHITE)
            self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 450))
        
        # 하단 정보
        bottom_font = pygame.font.Font(None, 24)
        bottom_text = bottom_font.render("ESC: Quit  |  R: Restart", True, GRAY)
        self.screen.blit(bottom_text, (SCREEN_WIDTH//2 - bottom_text.get_width()//2, 
                                      SCREEN_HEIGHT - 30))
    
    def draw_ui(self):
        """UI 그리기"""
        font = pygame.font.Font(None, 36)
        
        # 1P 점수
        score1_text = font.render(f"{self.player1.score}", True, WHITE)
        self.screen.blit(score1_text, (self.player1.x + 180, 20))
        
        # 2P 점수
        score2_text = font.render(f"{self.player2.score}", True, WHITE)
        self.screen.blit(score2_text, (self.player2.x + 180, 20))
        
        # 타이틀
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("2P Rhythm Game", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        # 음악 시간
        time_text = font.render(f"Time: {self.music.get_current_time():.1f}s", True, GRAY)
        self.screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, 60))
        
        # 키 안내
        info_font = pygame.font.Font(None, 24)
        info_text = info_font.render("1P: A S D F  |  2P: J K L ;  |  R: Restart  |  ESC: Quit", True, GRAY)
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
    game = Game()
    game.run()