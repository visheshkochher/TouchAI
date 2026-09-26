# Delhi

A year of Delhi's weather as a data sculpture, after Refik Anadol, and the same year
twenty years earlier stacked beneath it, so the difference between them is climate
change. It uses real data and a GPU particle simulation, it is audio reactive, and it
tells the year as a story.

Build:

```python
code = open('scenes/delhi/build.py', encoding='utf-8').read()
g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
```

The builder is idempotent. It destroys and recreates `/project1/delhi` and
`/project1/delhi_out`, and touches nothing else. **No media or data files:** the
datasets are constants, `DELHI_2024` and `DELHI_2004`, inside `delhi_template.py`
(and so inside the generated `build.py`), with their sources in the comment above
them.

**`build.py` is generated.** It is `delhi_template.py` plus three verbatim blocks of
`scenes/homestead/build.py` (the helpers, the audio front end with tempo and drop
detection, and the director), assembled by `gen_delhi.py`. After editing the
template, regenerate with `python3 scenes/delhi/gen_delhi.py`.

## The data

New Delhi (28.61 N, 77.21 E), every day of **2024 and 2004**. Both are leap years,
so row *n* is the same date in both. The data was retrieved on 2026-09-26 and 27.

- **Weather, both years**, from the Open-Meteo Historical Weather API (ERA5
  reanalysis, CC BY 4.0): daily max, min and mean temperature, precipitation, mean
  relative humidity, max wind, dominant wind direction, and cloud cover. It is the
  same source for both years.
- **Haze, both years**: aerosol optical depth at 550 nm (`AOD_55`), from the NASA
  POWER daily API (CERES SYN1deg). The same source for both years, so the smoke and
  haze compare fairly. It drives the smog particles, the haze halo and the veil.
- **PM2.5, 2024 only**, from the Open-Meteo Air Quality API (CAMS), hourly and
  averaged to daily means. It is shown in the readout. The API has no data before
  2013, which is why the haze uses AOD. CAMS values run lower than Delhi's ground
  stations, but the seasonal shape is right.

### What the two years say

| | 2004 | 2024 |
|---|---|---|
| days at or above 44 C | 3 | **17** |
| hottest day | 44.6 C | **46.0 C** |
| rain, whole year | 475 mm (a drought monsoon) | **1101 mm** |
| mean aerosol optical depth | 0.63 | **0.76** |
| winter haze, AOD Jan / Nov / Dec | 0.61 / 0.47 / 0.48 | **0.87 / 0.88 / 0.81** |

The piece shows this day by day. For example, 25 May 2024 was 5.0 C hotter and 21%
drier than 25 May 2004. The difference is not always warmer: on 10 January 2024 a cold
fog spell made it 4.7 C *colder* than 2004, and hazier. The readout gives both days and
the difference, and does not editorialise.

### The 2024 year

The year has a shape, and the piece is built on it:

| month | mean temp | rain | humidity | PM2.5 |
|---|---|---|---|---|
| January | 10.8 C | 9 mm | 85% | 123 |
| May | 34.5 C | 2 mm | 25% | 53 |
| July-September | 27-30 C | 250-356 mm/month | 78-85% | 34-48 |
| November | 22.3 C | 0 mm | 58% | 115 |

The extremes are real events:

- 46.0 C at the height of the May heatwave
- 116 mm on 28 June
- 3.9 C on the coldest January night

## Two rings, stacked

2024 is the upper ring and 2004 the lower, 1.56 units apart. There are 30,976
particles, interleaved so each year gets half, and every scale is shared between the
years, so the same colour means the same heat in both.

- The same day of the year melts in both rings at once.
- The **attended** year (key `y`) melts fully and draws at full brightness. The other
  melts at 45% and draws at half brightness.
- The camera rises or sinks toward the attended ring. It aims between the two, so both
  always stay in frame.

## The spin

The camera chases the present round the ring with a lag (a 1.5 s time constant). So
when the present jumps, the chase becomes a sweep, and the whole year turns past like
a radial. Before this, only a season jump did that. Now the music plays it, by
knocking the camera backwards:

| event | sweep |
|---|---|
| every kick | a notch of 0.06 rad, scaled by the kick's strength, so the ring ticks round on the beat |
| a build-up | winds the camera back by up to 0.5 rad; the drop lets it go |
| a drop, or `b`, or `s` | a big sweep: 1.4–2.6 rad, either direction |
| a season turning | a 0.9 rad sweep |
| switching year (`y`) | a 1.6 rad sweep |

The `Spin` knob scales all of it (0 turns it off).

## After Refik Anadol

What was taken:

- **Data as pigment.**
- **Chapters, not a timeline.** *Wind of Boston: Data Paintings* turned a year of
  wind readings into four chapters, each with its own painterly aesthetic.
- **A particle mass advected by a flow field**, leaving silk.
- **The data sculpture as an object in a space.**

Here:

- **The data forms the sculpture.** 16,384 large, soft particles, each belonging to
  one day of the year. At rest they sit in a ring of the year, one day per step
  around it, and the ring is the data:
  - it bulges outward on hot days and rises where the air was wet
  - its tube fattens with humidity and rain
  - smog days wear a diffuse haze of big soft particles
  - every particle is coloured by its own day: indigo cold, teal, gold, orange and
    crimson heat, monsoon green (humid and warm), and smog grey
- **The story walks around the ring.** The present day travels through the year (one
  year per `One Year (s)`, default 8 minutes, looping), and the camera pans to follow
  it. The present **melts** and is pushed by its own day's real forces:
  - heat rises in plumes
  - rain falls in curtains from the ring and is reborn in its cloud
  - the wind blows from where it came
  - the cold is viscous
  - smog thickens and slows everything

  The rest of the year holds its shape and drifts slowly along itself.
- **Six chapters** fall out of the data: I Winter, fog · II Spring · III Loo, the
  heat · IV Monsoon · V Smoke · VI Chill. A chapter title fades in when one begins.
  The day's own numbers are always shown, quietly: date, °C, humidity, rain, PM2.5.

## The music is the feeling

| signal | means |
|---|---|
| build-up (tension: energy rise, filter sweep, roll density, from `fault`'s detector) | the present is **gathered** back into its data form and swirled round itself: the pressure building, the clouds gathering. The camera draws in |
| drop | the **release**: the present bursts outward through whatever the weather is (the heat breaking, the monsoon arriving). The camera pulls back, a soft exposure lift, and the present stays loose for a few seconds |
| kick | felt through the season: in the heat it is a heat pulse (buoyancy doubles), under the rain it is thunder (the rain falls harder), in the cold it is a shiver |
| energy | how hard the flow pushes the present |
| humidity, tension | how long the silk trails hang |

## Keys

| key | does |
|---|---|
| 1-6 | jump to a chapter: 1 winter (5 Jan), 2 spring (11 Mar), 3 the heat (20 May), 4 the monsoon (28 Jun, 116 mm), 5 smoke (4 Nov), 6 chill (14 Dec) |
| 0 | 1 January |
| y | **YEAR**: attend to 2004 or 2024 (toggle). Both stay in frame |
| s | **SWEEP**: spin the year past |
| b | **BURST**: a release, now |
| g | **GATHER**: hold the year in its data form (toggle) |
| n | **RESEED**: a new flow field |

The performance page also has:

- One Year (s), Present Width (days), Flow, Spin
- Particle Size, Particle Brightness, Exposure
- Trails, Glow, Smog Veil
- Data Readout, Vignette

## The full works

1. **The data texture.** A Script TOP writes a 366 × 4 float texture once. Each
   year has two rows: T, RH, rain and wind, then wind sin/cos, cloud and haze (AOD).
   2024 is rows 0-1 and 2004 is rows 2-3. It never cooks again.
2. **The simulation.** A GLSL TOP at 176 × 176 with two colour buffers: position and
   life, and velocity and "presentness". Each is fed back through a Render Select and
   a Feedback TOP at 32-bit float. Per particle, per frame:
   - it computes its year (index mod 2), its day, and its home in its year's ring from
     the data
   - a spring holds it to that home, firmly for the far year and as the music allows
     for the present
   - the curl of simplex noise (the smoke drift), heat buoyancy, rain, wind, the kick
     and the build-up swirl push it
   - a drop bursts it outward
   - viscosity (the cold is thicker) and a soft horizontal leash keep it in check
   - rain circulates back into its cloud
   - its life runs down, and it is reborn at home
3. **The render.** A GLSL MAT instanced straight from the position texture: 16,384
   quads with no CPU hop. Each quad faces the camera and stretches along the
   particle's velocity, like wet pigment. Its size, colour and brightness come from
   its own day's data, read in the vertex shader by instance ID. The fragment is a
   soft disc, blended additively.
4. **The sculpture's scale.** Twelve month ticks and a dashed circle under each
   ring (static), and a "today" marker under both that turns with the present.
5. **Post.**
   - silk trails (max-blended feedback)
   - a grade shader: the sky is the present day's weather (winter blue-grey, summer
     dusk, monsoon teal, smog brown); heat shimmer when it is hot; an ACES filmic
     curve; the smog veil (lifted blacks from PM2.5 and winter fog); vignette and
     grain
   - bloom, then the readout

## Performance

- **60 fps with the simulation and engine verified cooking at 60 cooks/s** (counted
  with `totalCooks`), at 30,976 particles.
- GPU: particle render 0.53 ms, trails 0.25 ms, grade 0.12 ms, bloom 0.11 ms.
- CPU: the engine costs 0.06 ms median and 0.12 ms max per frame, sampled over 240
  consecutive frames with a frame-end probe. A single `cookTime` read had said 14 ms:
  that was one cook straight after a parameter change, not the steady state.
- The tension detector costs 0.3 ms.
- The data texture, ticks and quad cooked once at build and 0 times since (checked).
- 100 operators, zero errors, zero warnings.

The particle count is a balanced judgement: about 15k large soft particles per year
read as pigment at a fraction of the cost of a million small ones. `NP` in the
template scales it (256 gives 65k).

## Built to run all night

- **Script CHOP channels are built once**, then only written: the engine, the
  tension detector (whose original in `fault` rebuilt them every cook, the known
  native leak), and the director and tempo detector inherited verbatim from
  homestead.
- **Lists are capped.** The tension detector's onset list is capped at 400 as well as
  aged. The particle state is fixed-size textures.
- **Every phase wraps.** The clock is modulo 1000 s and the camera angle is wrapped.
  The story loops through the year.

**Long-run memory audit: pending.** Per the repo rule, the soak is the final
iteration, run once the visual style is approved. On this Mac, trend `footprint`,
not RSS (see `debugging.md`).

## What went wrong on the way

- **`TDCamToProj(vec4)` does not exist on this build.** It has no single-argument
  overload. The billboard multiplies by `uTDMats[TDCameraIndex()].proj` directly.
- **A shader local named `P` shadows the vertex position attribute `P`.** Rain became
  `Pr`, and the compiler's "vector swizzle out of range" error pointed at the right
  line.
- **COMP operator parameters resolve relative to the COMP's parent**, so
  `instanceop='../pos'` is invalid and a sibling is just `pos`. Nothing errors: the
  instancing and the material silently drop out and a single grey quad renders.
- **The Render Select TOP's buffer parameter is `bufferindex`**, not
  `colorbufferindex`.
- **The first pass was a blizzard.** The drop burst was about 5 times too strong,
  and particles reached ±7 units from a ring of radius 1.55. The winter shiver
  injected a fresh random kick every frame, which the trails drew as hair. Now: a
  gentler burst, a larger-scale curl, a smooth shiver, a horizontal leash, and more
  damping.
- **The monsoon was straw.** Rain pulled the present down, the leash yanked it back,
  and the kick pushed it outward, so it streaked in every direction. Rain now
  circulates (a fallen drop is reborn in its cloud), the leash is horizontal, and the
  kick is softer.
- **July wasn't green.** Most July days had no rain that day, so they stayed gold.
  Monsoon colour now comes from warm humidity as well as rain. It is gated on warmth,
  because January is 85% humid too.
- **Open-Meteo's air-quality API starts in 2013**, so PM2.5 can't cover 2004.
  Comparing 2024 PM2.5 with some other 2004 measure would have been apples and
  oranges. Both years' haze comes from one source instead: NASA POWER aerosol optical
  depth.
- **`TOP.cookTime` read once is a sample, not a measurement.** The engine read 14 ms
  once. 240 frames sampled from an `executeDAT` `onFrameEnd` said 0.06 ms. Forcing
  cooks in a loop inside one call measures nothing either: the repeat cooks in one
  frame are skipped (0.02 ms, too fast to have run the Python).
- **A chapter jump pulsed in the same call as a rebuild did nothing.** The director
  re-derives its playhead on its first cook after a reload, and overwrites the seek.
  Seek after the first frame.
