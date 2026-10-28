"""Song data. A new track is a list of cues plus a Style, not a new player."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from player.style import Style

KINDS = frozenset({"line", "words", "linger", "slam", "shout", "tinker", "side"})


@dataclass(frozen=True)
class Cue:
    """One timed event.

    ``hold`` is seconds after typing finishes. ``None`` leaves the window up
    until the next cue clears the screen.
    """

    at: float
    kind: str
    text: str = ""
    hold: float | None = None
    width: int | None = None
    type_speed: float | None = None
    words: tuple[tuple[float, str], ...] | None = None
    phrases: tuple[str, ...] | None = None
    delay: float = 0.3
    size: tuple[int, int] | None = None
    y_offset: int = 0
    gap: int | None = None
    keep_previous: bool = False
    count: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown cue kind {self.kind!r}")
        if self.at < 0:
            raise ValueError(f"cue time must be >= 0, got {self.at}")


@dataclass(frozen=True)
class Song:
    id: str
    title: str
    cues: tuple[Cue, ...]
    style: Style = field(default_factory=Style)
    audio: str | None = None

    def __post_init__(self) -> None:
        cues = tuple(self.cues)
        object.__setattr__(self, "cues", cues)
        if not self.id:
            raise ValueError("song id is required")
        if not cues:
            raise ValueError(f"{self.id} has no cues")
        last = -1.0
        for cue in cues:
            if cue.at < last:
                raise ValueError(
                    f"{self.id}: cue at {cue.at}s comes before {last}s"
                )
            last = cue.at


def line(
    at: float,
    text: str,
    hold: float | None = None,
    width: int | None = None,
    type_speed: float | None = None,
) -> Cue:
    """Ordinary typed line."""
    return Cue(at, "line", text=text, hold=hold, width=width, type_speed=type_speed)


def words(
    at: float,
    fragments: Sequence[tuple[float, str]],
    hold: float | None = None,
    width: int | None = None,
) -> Cue:
    """Line whose characters follow absolute song times."""
    timed = _timed(fragments)
    return Cue(
        at,
        "words",
        text=_join(timed),
        hold=hold,
        width=width,
        words=timed,
    )


def linger(
    at: float,
    payload: str | Sequence[tuple[float, str]],
    hold: float | None = None,
) -> Cue:
    """Centered line that stays. Payload may be word-timed fragments."""
    return _text_or_timed(at, "linger", payload, hold)


def slam(
    at: float,
    payload: str | Sequence[tuple[float, str]],
    hold: float | None = 3.5,
) -> Cue:
    """Oversized payoff line. Closing it also clears a tinker swarm."""
    return _text_or_timed(at, "slam", payload, hold)


def shout(at: float, text: str, hold: float | None = None) -> Cue:
    """Flood the screen with copies of one line."""
    return Cue(at, "shout", text=text, hold=hold)


def tinker(
    at: float,
    phrases: str | Sequence[str],
    hold: float | None = None,
    count: int | None = None,
) -> Cue:
    """Bouncing chips. They stay up through later lines until a slam closes."""
    if isinstance(phrases, str):
        packed = (phrases,)
    else:
        packed = tuple(phrases)
    return Cue(at, "tinker", hold=hold, phrases=packed, count=count)


def side(
    at: float,
    phrases: Sequence[str],
    delay: float = 0.3,
    hold: float | None = None,
    size: tuple[int, int] | None = None,
    y_offset: int = 0,
    gap: int | None = None,
    keep_previous: bool = False,
    type_speed: float | None = None,
) -> Cue:
    """Panels that open one after another across the screen."""
    return Cue(
        at,
        "side",
        phrases=tuple(phrases),
        delay=delay,
        hold=hold,
        size=size,
        y_offset=y_offset,
        gap=gap,
        keep_previous=keep_previous,
        type_speed=type_speed,
    )


def side_hold(
    gap: float,
    phrases: Sequence[str],
    delay: float,
    type_speed: float,
) -> float:
    """Fit the side-by-side hold so the row ends as the next cue begins."""
    typing_s = sum(len(phrase) * type_speed for phrase in phrases)
    delays_s = delay * max(0, len(phrases) - 1)
    return max(0.0, gap - typing_s - delays_s)


def _timed(fragments: Sequence[tuple[float, str]]) -> tuple[tuple[float, str], ...]:
    return tuple((float(t), str(frag)) for t, frag in fragments)


def _join(fragments: Sequence[tuple[float, str]]) -> str:
    return "".join(frag for _, frag in fragments)


def _text_or_timed(
    at: float,
    kind: str,
    payload: str | Sequence[tuple[float, str]],
    hold: float | None,
) -> Cue:
    if isinstance(payload, str):
        return Cue(at, kind, text=payload, hold=hold)
    timed = _timed(payload)
    return Cue(at, kind, text=_join(timed), hold=hold, words=timed)
