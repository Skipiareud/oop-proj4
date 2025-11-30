import os

import pygame


class AudioPlayer:
    def __init__(self) -> None:
        try:
            pygame.mixer.init()
        except pygame.error:
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            pygame.mixer.init()
        self.play_at_ms: int = 0
        self.started: bool = False

    def queue(self, path: str, start_delay: float) -> None:
        self.started = False
        self.play_at_ms = pygame.time.get_ticks() + int(start_delay * 1000)
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
        except Exception as exc:
            print(f"[warn] audio load failed for {path}: {exc}")

    def tick(self) -> None:
        if not self.started and pygame.time.get_ticks() >= self.play_at_ms:
            try:
                pygame.mixer.music.play()
            except Exception as exc:
                print(f"[warn] audio play failed: {exc}")
            self.started = True

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.started = False
