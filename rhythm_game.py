import pygame
import random
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# 초기화
pygame.init()

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
        
    def add_note(self, lane: int, speed: float):
        """노트 추가"""
        self.notes.append(Note(lane, -50, speed))
    
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

class NoteGenerator:
    """노트 생성기"""
    def __init__(self, base_speed: float):
        self.base_speed = base_speed
        self.last_spawn_time = 0
        self.spawn_interval = 600  # ms
    
    def update(self, current_time: int, player1: Player, player2: Player):
        """노트 생성 업데이트"""
        if current_time - self.last_spawn_time >= self.spawn_interval:
            # 1P 노트 생성
            lane = random.randint(0, 3)
            player1.add_note(lane, self.base_speed)
            
            # 2P 노트 생성
            lane = random.randint(0, 3)
            player2.add_note(lane, self.base_speed)
            
            self.last_spawn_time = current_time

class Game:
    """게임 메인 클래스"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2P Rhythm Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 플레이어 초기화
        self.player1 = Player("1P", 50, 
                             [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f],
                             GRAY)
        self.player2 = Player("2P", 650,
                             [pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_SEMICOLON],
                             BLUE)
        
        # 노트 생성기
        self.note_generator = NoteGenerator(200)
        self.speed = 2.0
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
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
            
            elif event.type == pygame.KEYUP:
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
        current_time = pygame.time.get_ticks()
        
        # 노트 생성
        self.note_generator.update(current_time, self.player1, self.player2)
        
        # 플레이어 업데이트
        self.player1.update(dt)
        self.player2.update(dt)
    
    def draw(self):
        """화면 그리기"""
        self.screen.fill(BLACK)
        
        # 플레이어 그리기
        self.player1.draw(self.screen)
        self.player2.draw(self.screen)
        
        # UI 그리기
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """UI 그리기"""
        font = pygame.font.Font(None, 36)
        
        # 1P 점수
        score1_text = font.render(f"{self.player1.score}", True, WHITE)
        self.screen.blit(score1_text, (self.player1.x + 180, 20))
        
        speed1_text = font.render(f"Speed {self.speed}", True, WHITE)
        self.screen.blit(speed1_text, (self.player1.x + 150, 50))
        
        # 2P 점수
        score2_text = font.render(f"{self.player2.score}", True, WHITE)
        self.screen.blit(score2_text, (self.player2.x + 180, 20))
        
        speed2_text = font.render(f"Speed {self.speed}", True, WHITE)
        self.screen.blit(speed2_text, (self.player2.x + 150, 50))
        
        # 타이틀
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("2P Rhythm Game", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 20))
        
        # 키 안내
        info_font = pygame.font.Font(None, 24)
        info_text = info_font.render("1P: A S D F  |  2P: J K L ;  |  ESC: Quit", True, GRAY)
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