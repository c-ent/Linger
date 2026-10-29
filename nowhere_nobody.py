"""nowhere nobody. Quiet centered lines, a swarm, then a slam."""

from player.song import Song, line, linger, slam, tinker
from player.style import Style

SONG = Song(
    id="nowhere_nobody",
    title="nowhere nobody",
    style=Style(
        font_size=18,
        shout_font_size=18,
        tinker_font_size=16,
        linger_font_size=28,
        slam_font_size=28,
    ),
    cues=(
        linger(0.00, "Deep breaths, honey"),
        line(2.81, "There's no more running", width=380, type_speed=0.060),
        linger(5.81, "And there's nowhere with nobody else that I'd rather be"),
        tinker(9.50, "nowhere nobody"),
        line(12.03, "I'm taking you", width=300, type_speed=0.070),
        linger(13.23, "Deep breaths, honey"),
        line(15.95, "We've at least till morning", width=400, type_speed=0.055),
        slam(19.28, "Then there's nowhere, nobody else that I'd rather be with", hold=7.6),
        linger(28.92, "No, there's nowhere else"),
        line(32.35, "And there's no more running", width=380, type_speed=0.060),
        linger(35.22, "Nobody else that I'd rather be with"),
    ),
)


if __name__ == "__main__":
    from player import play

    play(SONG)
