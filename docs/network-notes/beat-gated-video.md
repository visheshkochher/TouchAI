# Beat-gated video jukebox — network notes

*Source project: `BeatMovie.toe` (private, gitignored).*

Beat-gated video jukebox: a folder of movies on disk, cycled with the keyboard, whose
playback is *gated and scrubbed by the audio input* — the movie only plays while bass
is present, and highs spin/zoom the frame. Everything lives in `/project1`.

## Playback gating (the money recipe)

Two parallel band chains from `audiodevin1`:

```
audiodevin1 → audiofilter1 (lowpass 400 Hz) → envelope1 (bypassed) → low_bass_logic
audiodevin1 → c            (highpass 2 kHz, rolloff 12.41)         → high_pass_logic
```

Both `logic` CHOPs use **convert = bound** as a threshold gate: `low_bass_logic`
bounds 0.05..1000 (any bass above 0.05 → 1), `high_pass_logic` bounds 0.1..10.
A Logic CHOP is the idiomatic "is the band active right now" boolean.

The gates drive `moviefilein3` parameter expressions:

- `play = 1 if op('low_bass_logic')['chan1'] else 0` — **video only runs on the beat.**
- `speed = 3 if op('noise1')['chan1']>0.3 else -2` — a hermite noise CHOP
  (`tx = absTime.frame`) randomly flips between 3× forward and 2× reverse: chaotic scrub.
- `cuepoint = absTime.seconds` — cue follows the clock, so re-triggering doesn't rewind.

## Frame-echo composite

```
moviefilein3 → cache1 (cachesize 11) → cacheselect1 (index -4)
moviefilein3 + cacheselect1 → comp1 (operand: exclude)
→ transform1 → out1
```

Cache TOP + Cache Select at a negative index = a frames-ago tap; `exclude`-compositing
the current frame with its 4-frames-ago self gives a psychedelic motion echo that is
black wherever the image is static (exclude ≈ per-channel XOR). Note `cacheselect1` is
forced to 1280×256 — a stretched letterbox look, deliberate or leftover.

`transform1` reacts to highs: `rotate = 0.1+op('c')['chan1'] if high gate else 0`,
`sx/sy = 1+op('c')['chan1'] if high gate else 1`.

## File cycling UI

`folder1` (Folder DAT on `~/Desktop`) → `select1` (rows `*.mp4`) is the playlist.
`keyboardin1` → `chopexec1` (Off-to-On): each keypress writes the next filename into
the `output` Text DAT and wraps `current_index` at 24; `moviefilein3.file` is the
expression `op('output').text`. A Text DAT as a mutable variable + parameter
expression is the pre-custom-parameter way to do state.

## Reusable ideas

- Logic CHOP (convert=bound) as a per-band on/off gate for conditional expressions.
- `play`/`speed` expressions to make *footage itself* the audio-reactive element.
- Cache + Cache Select (negative index) + exclude comp = frame-difference echo.
- Folder DAT → Select DAT → keyboard-cycled Text DAT as a media playlist.
