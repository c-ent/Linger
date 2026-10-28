# Linger

Timed lyric windows. One shared player runs every song. A song file is the timing, the words, and the look.

## Run

From this folder:

```bash
python kiss_me.py
python stupid_song.py
python nowhere_nobody.py
```

Requires Python 3.10 or newer. `tkinter` ships with standard Python installs.

Audio is optional. Set `audio="path/to/song.mp3"` on a `Song` and install pygame (`pip install pygame`). The windows still run without it.

## Layout

- `kiss_me.py`, `stupid_song.py`, and `nowhere_nobody.py` are the songs. Add another file like these.
- `player/` is the shared player. Do not copy it into a song.

## Add a song

Create `your_song.py` in this folder:

```python
from player import play
from player.song import Song, line, linger, slam
from player.style import Style

SONG = Song(
    id="your_song",
    title="Your Song",
    style=Style(font_size=32),
    cues=(
        line(0.00, "First line", width=380, type_speed=0.04),
        linger(8.00, "This one stays put"),
        slam(12.00, "Last line", hold=3.5),
    ),
)

if __name__ == "__main__":
    play(SONG)
```

Run it with `python your_song.py`.

Cue helpers in `player/song.py`:

- `line` types a sentence. `hold=None` keeps it until the next cue.
- `words` reveals fragments on absolute song times: `(5.14, "We"), (5.71, " could")`.
- `linger` is a centered line that stays. It accepts a string or word-timed fragments.
- `slam` is the oversized payoff. Closing it also clears a tinker swarm.
- `shout` floods the screen with copies of one line.
- `tinker` bounces small chips until the next slam.
- `side` opens panels one after another. When another cue follows, the hold is fitted so the row ends as that cue starts.

`at` is seconds from the start and must not go backwards. `Style` is where a song changes font size, shout density, tinker speed, and whether ordinary lines sit in the center.
