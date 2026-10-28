"""Desktop stage. Every song shares this; none of them own a copy of it."""

from __future__ import annotations

import ctypes
import math
import random
import struct
import sys
import tempfile
import threading
import time
import tkinter as tk
from typing import Sequence

from player.song import Cue, side_hold
from player.style import Style


class Stage:
    """One Tk root and the windows currently on screen."""

    def __init__(self, root: tk.Misc, style: Style) -> None:
        self.root = root
        self.style = style
        self.sentences: list[SentenceWindow | SlamWindow] = []
        self.side_windows: list[SideBySideWindow] = []
        self.shouts: list[ShoutTile] = []
        self.tinkers: list[TinkerTile] = []
        self._shout_spawn_id = 0
        self._tinker_spawn_id = 0
        self._tinker_anim_id: str | None = None
        self._ico_path: str | None = None
        self._icon: tk.PhotoImage | None = None

    def schedule(self, cues: Sequence[Cue]) -> None:
        """Play cues on a background thread. Tk work is marshalled to the root."""
        origin = time.time()

        def worker() -> None:
            for index, cue in enumerate(cues):
                wait = cue.at - (time.time() - origin)
                if wait > 0:
                    time.sleep(wait)

                if cue.kind != "tinker":
                    closed = threading.Event()

                    def _close_and_signal() -> None:
                        self.close_all()
                        closed.set()

                    self.root.after(0, _close_and_signal)
                    closed.wait(timeout=1.0)
                    time.sleep(0.08)

                gap = None
                if index + 1 < len(cues):
                    gap = cues[index + 1].at - cue.at
                self._dispatch(cue, origin, gap)

        threading.Thread(target=worker, daemon=True).start()

    def _dispatch(self, cue: Cue, origin: float, gap: float | None) -> None:
        style = self.style
        if cue.kind == "shout":
            text = cue.text
            self.root.after(0, lambda text=text: self.show_shout_collage(text))
            return

        if cue.kind == "linger":
            def show(
                text: str = cue.text,
                hold: float | None = cue.hold,
                words: tuple[tuple[float, str], ...] | None = cue.words,
            ) -> None:
                self.open_sentence(
                    text,
                    hold,
                    width=style.linger_width,
                    type_speed=style.linger_type_speed,
                    centered=True,
                    font_size=style.linger_font(),
                    words=words,
                    song_origin=origin,
                )

            self.root.after(0, show)
            return

        if cue.kind == "slam":
            def show(
                text: str = cue.text,
                hold: float | None = cue.hold if cue.hold is not None else 3.5,
                words: tuple[tuple[float, str], ...] | None = cue.words,
            ) -> None:
                self.open_slam(text, hold, words=words, song_origin=origin)

            self.root.after(0, show)
            return

        if cue.kind == "words":
            def show(
                words: tuple[tuple[float, str], ...] | None = cue.words,
                text: str = cue.text,
                hold: float | None = cue.hold,
                width: int = cue.width if cue.width is not None else style.line_w,
            ) -> None:
                self.open_sentence(
                    text,
                    hold,
                    width=width,
                    centered=style.lines_centered,
                    words=words,
                    song_origin=origin,
                )

            self.root.after(0, show)
            return

        if cue.kind == "tinker":
            phrases = cue.phrases or ("…",)
            hold = cue.hold
            count = cue.count
            self.root.after(
                0,
                lambda phrases=phrases, hold=hold, count=count: self.show_tinker_swarm(
                    phrases, hold, count
                ),
            )
            return

        if cue.kind == "side":
            phrases = cue.phrases or ()
            speed = cue.type_speed if cue.type_speed is not None else style.sbs_type_speed
            hold = cue.hold
            if gap is not None:
                hold = side_hold(gap, phrases, cue.delay, speed)
            elif hold is None:
                hold = style.sbs_hold
            self.show_side_by_side(
                phrases,
                cue.delay,
                hold,
                size=cue.size,
                y_offset=cue.y_offset,
                gap=cue.gap,
                keep_previous=cue.keep_previous,
                type_speed=speed,
            )
            return

        width = cue.width if cue.width is not None else style.line_w
        speed = cue.type_speed if cue.type_speed is not None else style.type_speed
        text = cue.text
        hold = cue.hold

        def show_line(
            text: str = text,
            hold: float | None = hold,
            width: int = width,
            speed: float = speed,
        ) -> None:
            self.open_sentence(
                text,
                hold,
                width=width,
                type_speed=speed,
                centered=style.lines_centered,
            )

        self.root.after(0, show_line)

    # ── window chrome ────────────────────────────────────────────────────────

    def apply_window_style(self, win: tk.Misc, title: str = "") -> None:
        win.title(title)
        win.update_idletasks()
        color = self.style.window_icon_color

        if sys.platform == "win32":
            try:
                if self._ico_path is None:
                    self._ico_path = _solid_ico_path(color)
                win.iconbitmap(default=self._ico_path)
            except tk.TclError:
                pass
        else:
            try:
                if self._icon is None:
                    self._icon = _solid_icon(color)
                win.iconphoto(False, self._icon)
            except tk.TclError:
                pass

        if sys.platform != "win32":
            return

        try:
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
            preference = ctypes.c_int(1)  # DWMWCP_DONOTROUND
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                33,  # DWMWA_WINDOW_CORNER_PREFERENCE
                ctypes.byref(preference),
                ctypes.sizeof(preference),
            )
        except Exception:
            pass

    def open_sentence(
        self,
        text: str,
        hold: float | None,
        width: int | None = None,
        type_speed: float | None = None,
        centered: bool = True,
        font_size: int | None = None,
        words: tuple[tuple[float, str], ...] | None = None,
        song_origin: float | None = None,
        y_shift: int = 0,
    ) -> SentenceWindow:
        return SentenceWindow(
            self,
            text,
            hold,
            width=width,
            type_speed=type_speed,
            centered=centered,
            font_size=font_size,
            words=words,
            song_origin=song_origin,
            y_shift=y_shift,
        )

    def open_slam(
        self,
        text: str,
        hold: float | None,
        words: tuple[tuple[float, str], ...] | None = None,
        song_origin: float | None = None,
    ) -> SlamWindow:
        return SlamWindow(self, text, hold, words=words, song_origin=song_origin)

    # ── placement and typing ─────────────────────────────────────────────────

    def centered_pos(self, width: int, height: int | None = None, y_frac: float = 0.5) -> tuple[int, int]:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        if height is not None:
            y = (screen_h - height) // 2
        else:
            y = int(screen_h * y_frac)
        return x, y

    def random_top_pos(self, width: int) -> tuple[int, int]:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2 + random.randint(-180, 180)
        y = random.randint(80, max(81, screen_h // 3))
        return x, y

    def resize_typed_window(self, label: tk.Label, win: tk.Toplevel) -> None:
        """Grow a typing window. Centered lines stay pinned to the screen middle."""
        label.update_idletasks()
        new_h = label.winfo_reqheight() + self.style.line_pad * 2
        win_w = max(win.winfo_width(), 1)
        if getattr(win, "_recenter", False):
            screen_w = win.winfo_screenwidth()
            screen_h = win.winfo_screenheight()
            x = (screen_w - win_w) // 2
            y = (screen_h - new_h) // 2 + getattr(win, "_y_shift", 0)
            win._lock_x = x  # type: ignore[attr-defined]
            win._lock_y = y  # type: ignore[attr-defined]
            win.geometry(f"{win_w}x{new_h}+{x}+{y}")
        else:
            win.geometry(f"{win_w}x{new_h}")

    def type_chars(
        self,
        label: tk.Label,
        win: tk.Toplevel,
        text: str,
        speed_ms: int,
        on_done=None,
    ) -> None:
        def step(i: int = 0) -> None:
            try:
                label.config(text=text[:i])
                self.resize_typed_window(label, win)
            except tk.TclError:
                return
            if i < len(text):
                label.after(speed_ms, lambda: step(i + 1))
            elif on_done:
                on_done()

        step()

    def type_timed(
        self,
        label: tk.Label,
        win: tk.Toplevel,
        words: Sequence[tuple[float, str]],
        song_origin: float,
        on_done=None,
        resize: bool = True,
    ) -> None:
        """Reveal characters paced between absolute song timestamps."""
        if not words:
            if on_done:
                on_done()
            return

        events: list[tuple[float, str]] = []
        prefix = ""
        timed = list(words)
        for index, (start, frag) in enumerate(timed):
            if not frag:
                continue
            if index + 1 < len(timed):
                end = timed[index + 1][0]
            else:
                end = start + max(0.25, len(frag) * 0.06)
            span = max(end - start, 0.01)
            for char_index, char in enumerate(frag):
                prefix += char
                events.append((start + span * char_index / len(frag), prefix))

        if not events:
            if on_done:
                on_done()
            return

        def show_at(index: int, text: str, is_last: bool) -> None:
            def show() -> None:
                try:
                    label.config(text=text)
                    if resize:
                        self.resize_typed_window(label, win)
                except tk.TclError:
                    return
                if is_last and on_done:
                    on_done()

            delay_ms = max(0, int((song_origin + events[index][0] - time.time()) * 1000))
            win.after(delay_ms, show)

        for index, (_, text) in enumerate(events):
            show_at(index, text, index == len(events) - 1)

    # ── shout ────────────────────────────────────────────────────────────────

    def show_shout_collage(self, text: str, hold: float | None = None) -> None:
        del hold  # the next cue clears the collage
        self._shout_spawn_id += 1
        spawn_id = self._shout_spawn_id
        style = self.style
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        margin = 20
        max_x = max(margin, screen_w - style.shout_w - margin)
        max_y = max(margin, screen_h - style.shout_h - margin)

        def spawn(i: int = 0) -> None:
            if spawn_id != self._shout_spawn_id or i >= style.shout_count:
                return
            end = min(i + max(1, style.shout_batch), style.shout_count)
            for _ in range(i, end):
                ShoutTile(
                    self,
                    text,
                    random.randint(margin, max_x),
                    random.randint(margin, max_y),
                    style.shout_w + random.randint(-30, 40),
                    style.shout_h + random.randint(-10, 14),
                )
            self.root.after(style.shout_interval_ms, lambda end=end: spawn(end))

        spawn()

    # ── tinker swarm ─────────────────────────────────────────────────────────

    def tinker_keepout_rect(self, screen_w: int, screen_h: int) -> tuple[int, int, int, int] | None:
        style = self.style
        if style.tinker_keepout_w <= 0 or style.tinker_keepout_h <= 0:
            return None
        keep_w = min(style.tinker_keepout_w, screen_w - 80)
        keep_h = min(style.tinker_keepout_h, screen_h - 80)
        left = (screen_w - keep_w) // 2
        top = (screen_h - keep_h) // 2
        return left, top, left + keep_w, top + keep_h

    def tinker_random_pos(self, screen_w: int, screen_h: int, width: int, height: int, margin: int = 20) -> tuple[int, int]:
        max_x = max(margin, screen_w - width - margin)
        max_y = max(margin, screen_h - height - margin)
        keepout = self.tinker_keepout_rect(screen_w, screen_h)
        if keepout is None:
            return random.randint(margin, max_x), random.randint(margin, max_y)

        left, top, right, bottom = keepout
        bands = []
        if top - margin > margin + height:
            bands.append((margin, max_x, margin, max(margin, top - height)))
        if max_y > bottom:
            bands.append((margin, max_x, bottom, max_y))
        if left - margin > margin + width:
            bands.append((margin, max(margin, left - width), margin, max_y))
        if max_x > right:
            bands.append((right, max_x, margin, max_y))
        if not bands:
            return random.randint(margin, max_x), random.randint(margin, max_y)

        x0, x1, y0, y1 = random.choice(bands)
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return random.randint(x0, max(x0, x1)), random.randint(y0, max(y0, y1))

    def show_tinker_swarm(
        self,
        phrases: str | Sequence[str],
        hold: float | None = None,
        count: int | None = None,
    ) -> None:
        del hold  # a later slam closes the swarm
        self._stop_tinker_animator()
        self._tinker_spawn_id += 1
        spawn_id = self._tinker_spawn_id
        style = self.style

        if isinstance(phrases, str):
            phrases = [phrases]
        else:
            phrases = list(phrases)
        if not phrases:
            phrases = ["…"]

        total = style.tinker_count if count is None else count
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        margin = 20
        batch = max(1, style.tinker_batch)

        def spawn(i: int = 0) -> None:
            if spawn_id != self._tinker_spawn_id or i >= total:
                return
            end = min(i + batch, total)
            for j in range(i, end):
                text = phrases[j % len(phrases)]
                width = style.tinker_w + random.randint(-30, 50)
                height = style.tinker_h + random.randint(-8, 18)
                x, y = self.tinker_random_pos(screen_w, screen_h, width, height, margin)
                speed = random.uniform(style.tinker_speed_min, style.tinker_speed_max)
                angle = random.uniform(0, math.tau)
                vx = speed * _sign() * max(0.35, abs(math.cos(angle)))
                vy = speed * _sign() * max(0.35, abs(math.sin(angle)))
                floor = style.tinker_speed_floor
                if abs(vx) < floor:
                    vx = floor if vx >= 0 else -floor
                if abs(vy) < floor:
                    vy = floor if vy >= 0 else -floor
                TinkerTile(self, text, x, y, width, height, vx, vy)
            if self._tinker_anim_id is None and self.tinkers:
                self._tinker_anim_id = self.root.after(
                    int(1000 / style.tinker_fps),
                    self._tinker_animate,
                )
            self.root.after(style.tinker_spawn_ms, lambda end=end: spawn(end))

        spawn()

    def _stop_tinker_animator(self) -> None:
        if self._tinker_anim_id is not None:
            try:
                self.root.after_cancel(self._tinker_anim_id)
            except Exception:
                pass
        self._tinker_anim_id = None

    def _tinker_animate(self) -> None:
        alive = False
        for tile in list(self.tinkers):
            if tile.alive:
                tile.step()
                alive = True
        if alive and self.tinkers:
            self._tinker_anim_id = self.root.after(
                int(1000 / self.style.tinker_fps),
                self._tinker_animate,
            )
        else:
            self._tinker_anim_id = None

    # ── side by side ─────────────────────────────────────────────────────────

    def show_side_by_side(
        self,
        phrases: Sequence[str],
        delay: float,
        hold: float | None,
        size: tuple[int, int] | None = None,
        y_offset: int = 0,
        gap: int | None = None,
        keep_previous: bool = False,
        type_speed: float | None = None,
    ) -> None:
        """Open panels on this thread so the scheduler can wait out the row.

        That matches the original timing: setup cost is subtracted from the
        sleep, and the next cue is not late by the whole animation.
        """
        setup_start = time.time()
        if not keep_previous:
            self.close_side_windows()

        style = self.style
        if gap is None:
            gap = style.sbs_gap
        speed = type_speed if type_speed is not None else style.sbs_type_speed
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        measured = [_phrase_size(phrase, style) for phrase in phrases]
        panel_w = max(w for w, _ in measured)
        panel_h = max(h for _, h in measured)
        if size:
            panel_w = max(panel_w, size[0])
            panel_h = max(panel_h, size[1])

        layout_w = panel_w + style.sbs_frame_pad
        total = layout_w * len(phrases) + gap * (len(phrases) - 1)
        start_x = (screen_w - total) // 2
        windows: list[SideBySideWindow] = []

        def open_panel(i: int) -> None:
            if i >= len(phrases):
                if hold is not None:
                    hold_id = self.root.after(
                        int(hold * 1000),
                        lambda: self.close_side_group(windows),
                    )
                    for window in windows:
                        window.hold_id = hold_id
                return

            def on_typed(index: int = i) -> None:
                self.root.after(int(delay * 1000), lambda: open_panel(index + 1))

            window = SideBySideWindow(
                self,
                phrases[i],
                start_x + i * (layout_w + gap),
                (screen_h - panel_h) // 2 + y_offset,
                (panel_w, panel_h),
                speed,
                on_typed,
            )
            windows.append(window)
            self.side_windows.append(window)

        self.root.after(0, lambda: open_panel(0))

        needed = sum(len(phrase) * speed for phrase in phrases)
        needed += delay * max(0, len(phrases) - 1)
        needed += hold if hold is not None else 0
        time.sleep(max(0.0, needed - (time.time() - setup_start)))

        for window in list(windows):
            if window in self.side_windows:
                self.side_windows.remove(window)

    # ── teardown ─────────────────────────────────────────────────────────────

    def close_side_group(self, windows: Sequence[SideBySideWindow]) -> None:
        for window in windows:
            window.close()

    def close_side_windows(self) -> None:
        windows = list(self.side_windows)
        self.side_windows.clear()
        self.close_side_group(windows)

    def close_sentences(self) -> None:
        windows = list(self.sentences)
        self.sentences.clear()
        for window in windows:
            window.close()

    def close_shouts(self) -> None:
        self._shout_spawn_id += 1
        windows = list(self.shouts)
        self.shouts.clear()
        for window in windows:
            window.close()

    def close_tinkers(self) -> None:
        self._tinker_spawn_id += 1
        self._stop_tinker_animator()
        tiles = list(self.tinkers)
        self.tinkers.clear()
        if not tiles:
            return
        for tile in tiles:
            tile.alive = False
            try:
                tile.win.withdraw()
            except tk.TclError:
                pass
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass

        def destroy_next(i: int = 0) -> None:
            if i >= len(tiles):
                return
            try:
                tiles[i].win.destroy()
            except tk.TclError:
                pass
            self.root.after(20, lambda: destroy_next(i + 1))

        destroy_next()

    def close_all(self, include_tinkers: bool = False) -> None:
        """Clear lyric windows. Tinkers stay until a slam ends, unless forced."""
        self.close_side_windows()
        self.close_sentences()
        self.close_shouts()
        if include_tinkers:
            self.close_tinkers()


class SentenceWindow:
    """Floating window that types a line and grows with the text."""

    def __init__(
        self,
        stage: Stage,
        sentence: str,
        hold: float | None,
        width: int | None = None,
        type_speed: float | None = None,
        centered: bool = True,
        font_size: int | None = None,
        words: tuple[tuple[float, str], ...] | None = None,
        song_origin: float | None = None,
        y_shift: int = 0,
    ) -> None:
        style = stage.style
        self.stage = stage
        self.hold = hold
        self.win = tk.Toplevel(stage.root)
        self.win.configure(bg="white")
        self.win.resizable(False, False)

        used_width = style.line_w if width is None else width
        used_font = style.font_size if font_size is None else font_size
        init_h = style.line_pad * 2
        if centered:
            x, y = stage.centered_pos(used_width, init_h)
            y += y_shift
        else:
            x, y = stage.random_top_pos(used_width)
        self.win._recenter = centered  # type: ignore[attr-defined]
        self.win._y_shift = y_shift  # type: ignore[attr-defined]
        self.win._lock_x = x  # type: ignore[attr-defined]
        self.win._lock_y = y  # type: ignore[attr-defined]
        self.win.geometry(f"{used_width}x{init_h}+{x}+{y}")

        self.label = tk.Label(
            self.win,
            text="",
            font=(style.font_name, used_font, "bold"),
            fg=style.fg,
            bg="white",
            wraplength=used_width - style.line_pad * 2,
            justify="center" if centered else "left",
        )
        self.label.place(x=style.line_pad, y=style.line_pad, anchor="nw")
        stage.apply_window_style(self.win)
        stage.sentences.append(self)

        if words and song_origin is not None:
            stage.type_timed(self.label, self.win, words, song_origin, on_done=self._start_hold)
        else:
            speed_ms = int((type_speed if type_speed is not None else style.type_speed) * 1000)
            stage.type_chars(self.label, self.win, sentence, speed_ms, on_done=self._start_hold)

    def _start_hold(self) -> None:
        if self.hold is not None:
            self.win.after(int(self.hold * 1000), self.close)

    def close(self) -> None:
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self in self.stage.sentences:
            self.stage.sentences.remove(self)


class SideBySideWindow:
    """One fixed-size panel in a side-by-side row."""

    def __init__(
        self,
        stage: Stage,
        word: str,
        x: int,
        y: int,
        size: tuple[int, int],
        type_speed: float,
        on_typed=None,
    ) -> None:
        style = stage.style
        self.stage = stage
        self.hold_id = None
        self.win = tk.Toplevel(stage.root)
        self.win.configure(bg="white")
        self.win.resizable(False, False)
        width, height = size
        self.win.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.win,
            text="",
            font=(style.font_name, style.font_size, "bold"),
            fg=style.fg,
            bg="white",
            wraplength=width - style.line_pad * 2,
            justify="left",
        )
        self.label.place(x=style.line_pad, y=style.line_pad, anchor="nw")
        stage.apply_window_style(self.win)

        speed_ms = int(type_speed * 1000)

        def step(i: int = 0) -> None:
            try:
                self.label.config(text=word[:i])
            except tk.TclError:
                return
            if i < len(word):
                self.label.after(speed_ms, lambda: step(i + 1))
            elif on_typed:
                on_typed()

        step()

    def close(self) -> None:
        if self.hold_id is not None:
            try:
                self.stage.root.after_cancel(self.hold_id)
            except Exception:
                pass
            self.hold_id = None
        try:
            self.win.destroy()
        except tk.TclError:
            pass


class SlamWindow:
    """Oversized centered payoff. Closing it clears any tinker swarm."""

    def __init__(
        self,
        stage: Stage,
        text: str,
        hold: float | None,
        words: tuple[tuple[float, str], ...] | None = None,
        song_origin: float | None = None,
    ) -> None:
        style = stage.style
        self.stage = stage
        self.hold = hold
        self.win = tk.Toplevel(stage.root)
        self.win.configure(bg="white")
        self.win.resizable(False, False)

        screen_w = stage.root.winfo_screenwidth()
        screen_h = stage.root.winfo_screenheight()
        width = style.slam_width
        font_size = style.slam_font()
        wrap = width - style.line_pad * 2
        full = _join_words(words) if words else text

        if style.slam_presize:
            probe = tk.Label(
                self.win,
                text=full,
                font=(style.font_name, font_size, "bold"),
                wraplength=wrap,
                justify="left",
            )
            probe.update_idletasks()
            height = max(probe.winfo_reqheight() + style.line_pad * 2, 120)
            probe.destroy()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            justify = "left"
            self.win._recenter = False  # type: ignore[attr-defined]
        else:
            height = style.line_pad * 2
            x = (screen_w - width) // 2
            y = (screen_h - 200) // 2
            justify = "center"
            self.win._recenter = False  # type: ignore[attr-defined]

        self.win._lock_x = x  # type: ignore[attr-defined]
        self.win._lock_y = y  # type: ignore[attr-defined]
        self.win.geometry(f"{width}x{height}+{x}+{y}")

        self.label = tk.Label(
            self.win,
            text="",
            font=(style.font_name, font_size, "bold"),
            fg=style.fg,
            bg="white",
            wraplength=wrap,
            justify=justify,
            anchor="nw",
        )
        self.label.place(x=style.line_pad, y=style.line_pad, anchor="nw")
        stage.apply_window_style(self.win)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        stage.sentences.append(self)

        if words and song_origin is not None:
            stage.type_timed(
                self.label,
                self.win,
                words,
                song_origin,
                on_done=self._start_hold,
                resize=not style.slam_presize,
            )
        elif style.slam_presize:
            self._type_fixed(full, int(style.slam_type_speed * 1000))
        else:
            stage.type_chars(
                self.label,
                self.win,
                full,
                int(style.slam_type_speed * 1000),
                on_done=self._start_hold,
            )

    def _type_fixed(self, text: str, speed_ms: int) -> None:
        def step(i: int = 0) -> None:
            try:
                self.label.config(text=text[:i])
            except tk.TclError:
                return
            if i < len(text):
                self.win.after(speed_ms, lambda: step(i + 1))
            else:
                self._start_hold()

        step()

    def _start_hold(self) -> None:
        if self.hold is not None:
            self.win.after(int(self.hold * 1000), self.close)

    def close(self) -> None:
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self in self.stage.sentences:
            self.stage.sentences.remove(self)
        self.stage.close_tinkers()


class ShoutTile:
    """One box in a shout collage. Text is shown at once."""

    def __init__(self, stage: Stage, text: str, x: int, y: int, width: int, height: int) -> None:
        style = stage.style
        self.stage = stage
        self.win = tk.Toplevel(stage.root)
        self.win.configure(bg="white")
        self.win.resizable(False, False)
        if sys.platform == "darwin":
            try:
                self.win.overrideredirect(True)
            except tk.TclError:
                pass
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        tk.Label(
            self.win,
            text=text,
            font=(style.font_name, style.shout_font(), "bold"),
            fg=style.fg,
            bg="white",
            wraplength=width - 16,
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")
        stage.shouts.append(self)

    def close(self) -> None:
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self in self.stage.shouts:
            self.stage.shouts.remove(self)


class TinkerTile:
    """Small lyric chip moved by the shared animator."""

    def __init__(
        self,
        stage: Stage,
        text: str,
        x: int,
        y: int,
        width: int,
        height: int,
        vx: float,
        vy: float,
    ) -> None:
        style = stage.style
        self.stage = stage
        self.alive = True
        self.w = width
        self.h = height
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.sw = stage.root.winfo_screenwidth()
        self.sh = stage.root.winfo_screenheight()
        self.keepout = stage.tinker_keepout_rect(self.sw, self.sh)
        self.win = tk.Toplevel(stage.root)
        self.win.configure(bg="white")
        self.win.resizable(False, False)
        stage.apply_window_style(self.win)
        self.win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
        tk.Label(
            self.win,
            text=text,
            font=(style.font_name, style.tinker_font(), "bold"),
            fg=style.fg,
            bg="white",
            wraplength=width - 12,
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")
        stage.tinkers.append(self)

    def _hits_keepout(self, x: float, y: float) -> bool:
        if self.keepout is None:
            return False
        left, top, right, bottom = self.keepout
        return not (x + self.w <= left or x >= right or y + self.h <= top or y >= bottom)

    def step(self) -> None:
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy
        margin = 8
        max_x = max(margin, self.sw - self.w - margin)
        max_y = max(margin, self.sh - self.h - margin)

        if self.x <= margin:
            self.x = margin
            self.vx = abs(self.vx)
        elif self.x >= max_x:
            self.x = max_x
            self.vx = -abs(self.vx)

        if self.y <= margin:
            self.y = margin
            self.vy = abs(self.vy)
        elif self.y >= max_y:
            self.y = max_y
            self.vy = -abs(self.vy)

        if self.keepout is not None and self._hits_keepout(self.x, self.y):
            left, top, right, bottom = self.keepout
            center_x = (left + right) / 2
            center_y = (top + bottom) / 2
            tile_cx = self.x + self.w / 2
            tile_cy = self.y + self.h / 2
            if abs(tile_cx - center_x) * (bottom - top) > abs(tile_cy - center_y) * (right - left):
                if tile_cx < center_x:
                    self.x = left - self.w
                    self.vx = -abs(self.vx)
                else:
                    self.x = right
                    self.vx = abs(self.vx)
            else:
                if tile_cy < center_y:
                    self.y = top - self.h
                    self.vy = -abs(self.vy)
                else:
                    self.y = bottom
                    self.vy = abs(self.vy)
            self.x = min(max(self.x, margin), max_x)
            self.y = min(max(self.y, margin), max_y)

        try:
            self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        except tk.TclError:
            self.alive = False

    def close(self) -> None:
        self.alive = False
        try:
            self.win.withdraw()
        except tk.TclError:
            pass
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self in self.stage.tinkers:
            self.stage.tinkers.remove(self)


def _sign() -> int:
    return 1 if random.random() < 0.5 else -1


def _join_words(words: Sequence[tuple[float, str]] | None) -> str:
    if not words:
        return ""
    return "".join(frag for _, frag in words)


def _text_size(text: str, font_size: int) -> tuple[int, int]:
    # Approximate metrics. A second Tk() segfaults on macOS.
    average = font_size * 0.58
    return max(1, int(len(text or " ") * average)), int(font_size * 1.45)


def _phrase_size(phrase: str, style: Style, size: tuple[int, int] | None = None) -> tuple[int, int]:
    if size:
        return size
    width, height = _text_size(phrase, style.font_size)
    return max(width + style.sbs_pad, style.sbs_min_w), height + style.sbs_pad


def _solid_icon(color: str, size: int = 32) -> tk.PhotoImage:
    icon = tk.PhotoImage(width=size, height=size)
    icon.put(color, to=(0, 0, size, size))
    return icon


def _solid_ico_path(hex_color: str, size: int = 32) -> str:
    red = int(hex_color[1:3], 16)
    green = int(hex_color[3:5], 16)
    blue = int(hex_color[5:7], 16)
    row = bytes([blue, green, red, 255] * size)
    xor = b"".join(reversed([row] * size))
    and_row_bytes = ((size + 31) // 32) * 4
    and_mask = b"\x00" * (and_row_bytes * size)
    bitmap_header = struct.pack(
        "<IIIHHIIIIII",
        40, size, size * 2, 1, 32, 0, len(xor) + len(and_mask), 0, 0, 0, 0,
    )
    image = bitmap_header + xor + and_mask
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(image), 22)
    handle = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
    handle.write(header + entry + image)
    handle.close()
    return handle.name
