"""Per-song look. The player reads this; it does not hard-code sizes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    """Visual knobs for one song.

    Defaults match the centered, word-timed look. Override fields when a song
    needs a different size, speed, or placement.
    """

    font_name: str = "Helvetica"
    font_size: int = 28
    line_pad: int = 18
    fg: str = "#111111"
    type_speed: float = 0.05
    word_hold: float = 2.5
    line_w: int = 400
    # False scatters ordinary lines near the top and lets them grow in place.
    lines_centered: bool = True

    sbs_hold: float = 1.8
    sbs_pad: int = 40
    sbs_min_w: int = 110
    sbs_gap: int = 24
    sbs_frame_pad: int = 8
    sbs_type_speed: float = 0.04

    window_icon_color: str = "#7C949E"
    slide_duration_ms: int = 2000
    slide_fps: int = 120

    shout_count: int = 50
    shout_interval_ms: int = 30
    shout_batch: int = 5
    shout_w: int = 280
    shout_h: int = 72
    shout_font_size: int | None = None

    tinker_count: int = 10
    tinker_spawn_ms: int = 40
    tinker_batch: int = 5
    tinker_fps: int = 60
    tinker_w: int = 200
    tinker_h: int = 64
    tinker_font_size: int | None = None
    tinker_speed_min: float = 0.25
    tinker_speed_max: float = 0.55
    tinker_speed_floor: float = 0.15
    # Zero disables the clear zone in the middle of the screen.
    tinker_keepout_w: int = 720
    tinker_keepout_h: int = 380

    linger_width: int = 520
    linger_font_size: int | None = None
    linger_type_speed: float = 0.07

    slam_width: int = 640
    slam_font_size: int | None = None
    slam_type_speed: float = 0.085
    # False lets the slam window grow while the line types.
    slam_presize: bool = True

    def shout_font(self) -> int:
        if self.shout_font_size is None:
            return self.font_size
        return self.shout_font_size

    def tinker_font(self) -> int:
        if self.tinker_font_size is None:
            return self.font_size
        return self.tinker_font_size

    def linger_font(self) -> int:
        if self.linger_font_size is None:
            return self.font_size
        return self.linger_font_size

    def slam_font(self) -> int:
        if self.slam_font_size is None:
            return self.font_size
        return self.slam_font_size
