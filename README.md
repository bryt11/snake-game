# 🐍 Classic Snake Arcade

A polished, modern Snake Arcade game built in Python using standard library Tkinter with **zero external dependencies**.

![Game Preview](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-green)
![Dependencies](https://img.shields.io/badge/Dependencies-None%20(Standard%20Library)-brightgreen)

---

## ✨ Features

- **🎮 Smooth Gameplay & Responsive Controls**: Dual control scheme (Arrow Keys & WASD) with input buffering so fast multi-key turns are never dropped.
- **🍎 Food & Golden Bonus Stars**: Collect apples (+10 points) and time-limited Golden Stars (+bonus points with remaining time multiplier) that spawn every 5 apples.
- **⚡ Dynamic Progression**: Speed gradually accelerates as you score higher.
- **👀 Expressive Snake Animations**: Snake head features animated eyes that watch the direction of travel, with alternating segment colors.
- **🏆 Persistent High Score**: Best scores are automatically saved to `highscore.json`.
- **🔊 Native Sound Effects**: Built-in sound effects (using macOS system audio) with an instant Mute toggle (`M`).
- **⏸️ Pause & Instant Restart**: Pause anytime (`Space` or `P`) and restart immediately (`R`).

---

## 🚀 How to Run

No installation required! Just run with Python 3:

```bash
python3 snake_game.py
```

---

## 🕹️ Controls

| Key | Action |
|---|---|
| `↑` / `W` | Move Up |
| `↓` / `S` | Move Down |
| `←` / `A` | Move Left |
| `→` / `D` | Move Right |
| `Space` or `P` | Pause / Resume |
| `R` | Restart Game |
| `M` | Toggle Sound Effects (ON / OFF) |
| `Esc` or `Q` | Quit Game |

---

## 📁 File Structure

- [`snake_game.py`](file:///Users/Bright/Desktop/Vibe%20Coding/Gemini%20Course/snake_game.py) - Complete Snake game implementation.
- [`highscore.json`](file:///Users/Bright/Desktop/Vibe%20Coding/Gemini%20Course/highscore.json) - Saved high score data (automatically generated).
