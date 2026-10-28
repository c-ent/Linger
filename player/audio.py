"""Optional soundtrack. Visuals still run when pygame is missing."""


def play_audio(path: str) -> None:
    try:
        import pygame
    except ImportError:
        print("No audio: pip install pygame")
        return
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as exc:
        print(f"Audio error: {exc}")
