"""stupid song. Scattered lines, a loud collage, then a slam."""

from player.song import Song, line, linger, shout, side, slam, tinker
from player.style import Style

STYLE = Style(
    font_size=36,
    line_pad=20,
    lines_centered=False,
    shout_count=80,
    shout_interval_ms=85,
    shout_batch=1,
    shout_w=600,
    shout_h=182,
    shout_font_size=32,
    tinker_count=8,
    tinker_spawn_ms=160,
    tinker_batch=1,
    tinker_fps=14,
    tinker_w=170,
    tinker_font_size=20,
    tinker_speed_min=1.8,
    tinker_speed_max=4.5,
    tinker_speed_floor=1.0,
    tinker_keepout_w=0,
    tinker_keepout_h=0,
    linger_width=460,
    linger_font_size=40,
    slam_width=720,
    slam_font_size=52,
    slam_presize=False,
)

SONG = Song(
    id="stupid_song",
    title="stupid song",
    style=STYLE,
    cues=(
        line(0.00, "Every night like the one before", width=380, type_speed=0.038),
        line(1.81, "Dream of you from like 1 to 4", width=380, type_speed=0.050),
        line(3.70, "Positively and truly sure", width=340, type_speed=0.034),
        shout(5.35, "Nobody's wanted somebody more"),
        line(7.41, "It's a thing that i can't ignore", width=360, type_speed=0.038),
        line(9.26, "Tell your friends that you're mine, i'm yours", width=420, type_speed=0.022),
        line(11.17, "With the hand on my heart, i swore", width=380, type_speed=0.038),
        shout(12.78, "Nobody's wanted somebody more"),
        line(15.01, "It's a thing that i can't ignore", width=360, type_speed=0.038),
        line(16.82, "Tell your friends that you're mine, i'm yours", width=420, type_speed=0.022),
        linger(18.70, "With a hand on my heart, i swore"),
        tinker(21.20, ["i swore", "mine", "yours", "more", "heart"]),
        side(
            30.61,
            ["I'm going crazy,", "i'm going mad"],
            delay=0.45,
            hold=2.0,
            size=(300, 160),
            gap=48,
            type_speed=0.05,
        ),
        slam(34.43, "I want you, baby, so bad", hold=3.5),
    ),
)


if __name__ == "__main__":
    from player import play

    play(SONG)
