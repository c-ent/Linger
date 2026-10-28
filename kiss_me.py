"""Kiss Me. Word-timed lines, then a slam."""

from player.song import Song, linger, slam, tinker, words

SONG = Song(
    id="kiss_me",
    title="Kiss Me",
    cues=(
        linger(0.00, [
            (0.00, "Kiss"), (0.38, " me"), (0.70, " like"), (0.98, " you"),
            (1.30, " know"), (1.88, " this"), (2.47, " is"), (3.05, " good"),
            (3.70, "bye"),
        ]),
        words(5.14, [
            (5.14, "We"), (5.71, " could"), (6.09, " try"), (6.66, " to"),
            (6.96, " make"), (7.32, " it"), (7.62, " all"), (7.93, " the"),
            (8.25, " way"), (8.80, " out"),
        ], width=420),
        words(9.68, [
            (9.68, "Grab"), (10.02, " me"), (10.32, " like"), (10.60, " my"),
            (10.92, " life"), (11.55, " is"), (12.10, " on"), (12.70, " the"),
            (13.32, " line"),
        ], width=400),
        words(14.82, [
            (14.82, "We"), (15.40, " decide"), (16.26, " to"), (16.54, " make"),
            (16.91, " it"), (17.19, " all"), (17.52, " the"), (17.83, " way"),
            (18.43, " out"),
        ], width=420),
        linger(19.27, [
            (19.27, "My"), (19.62, " heart"), (19.96, " in"), (20.23, " your"),
            (20.52, " hands"), (21.69, " despite"), (22.26, " all"),
            (22.56, " of"), (22.87, " my"), (23.22, " plans"),
        ]),
        tinker(20.70, ["heart", "hands", "plans", "make it count"]),
        words(24.39, [
            (24.39, "We"), (24.97, " could"), (25.34, " try"), (25.86, " to"),
            (26.17, " make"), (26.47, " it,"), (26.81, " make"), (27.10, " it"),
            (27.42, " all"), (27.96, " count"),
        ], width=440),
        slam(28.87, [
            (28.87, "Kiss"), (29.21, " me"), (29.53, " like"), (29.80, " you"),
            (30.08, " know"), (30.76, " this"), (31.32, " is"), (31.89, " good"),
            (32.47, "bye"),
        ], hold=4.0),
    ),
)


if __name__ == "__main__":
    from player import play

    play(SONG)
