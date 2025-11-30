# oop-proj4

Two-player split-screen rhythm battle written with Python and pygame.

## How to run

```bash
python3 main.py
```

Controls
- Menu: Up/Down to choose a song, `Esc` to quit app
- In-game: Player 1 (left) `q w e r`, Player 2 (right) `o p [ ]`
- In-game restart: `B`; `Esc` prompts and returns to menu (quit song), not exit app
- Lead-in countdown runs before the chart starts.

## Notes

- mp3 playback supported. Edit `game.py` `_load_song_list` to point to your mp3 and set bpm/offset/chart_offset/start_delay/length_hint/difficulty (offsets shown in menu for sync tuning).
- Chart generation: energy onset detection mapped to 4 lanes with randomness to keep patterns varied; falls back to bpm-based auto chart if detection fails.
- Built with pygame 2.x which is pre-installed in the provided environment.
