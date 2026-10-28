"""Play one song on a hidden root window."""

from __future__ import annotations

import tkinter as tk

from player.audio import play_audio
from player.song import Song
from player.stage import Stage


class Player:
    def __init__(self, song: Song) -> None:
        self.song = song

    def play(self) -> None:
        root = tk.Tk()
        stage = Stage(root, self.song.style)
        stage.apply_window_style(root, title=self.song.title)
        root.withdraw()
        if self.song.audio:
            play_audio(self.song.audio)
        stage.schedule(self.song.cues)
        root.mainloop()


def play(song: Song) -> None:
    Player(song).play()
