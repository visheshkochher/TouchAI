# Delhi — a year of Delhi's weather as a data sculpture, after Refik Anadol.
#
# DATA AS PIGMENT. 16,384 large soft particles, and every one of them belongs to one
# day of 2024. At rest they sit in the shape of the year — a ring, one day per step
# around it — and the ring is the data: it bulges outward on hot days, rises where
# the air was wet, fattens with rain, and wears a diffuse haze of big soft particles
# on the smog days. Each particle is coloured by its own day: indigo cold, teal,
# gold, orange, crimson heat; monsoon green where it rained; smog grey where the air
# was thick.
#
# THE STORY WALKS AROUND THE RING. The present day travels through the year (one
# year every Storylen seconds) and the camera pans to follow it. The present MELTS:
# its particles leave the ring and are pushed by that day's real forces —
#   heat rises in convection plumes      (the May 2024 heatwave reached 46 C)
#   rain falls, and streaks              (116 mm on 28 June 2024)
#   the wind blows from where it came
#   the cold is viscous and shivers      (3.9 C on the coldest January night)
#   smog thickens and slows everything   (the October-November haze)
# while the rest of the year holds its shape, a sculpture the present flows through.
#
# THE MUSIC IS THE FEELING. A BUILD-UP (tension: rise, filter sweep, roll density)
# gathers the present back into its data form and swirls it — the pressure
# building, the clouds gathering. A DROP releases it: a burst outward through
# whatever the weather is, the heat breaking, the monsoon arriving. The KICK is felt
# through the season: a heat pulse in May, thunder under the monsoon rain, a shiver
# in January.
#
# THE FULL WORKS, KEPT LIGHT: a GPU particle simulation in a GLSL TOP (position and
# velocity in two 32-bit float buffers, fed back; curl noise, data forces, life
# cycle), rendered as soft velocity-stretched billboards by a GLSL MAT instanced
# straight from the position texture (no CPU hop), silk trails, a filmic tonemap
# with a smog veil and heat shimmer, bloom, and a panning camera. 16k particles, not
# millions: large and soft reads as pigment, and costs little.
#
# BUILT TO RUN ALL NIGHT: Script CHOP channels are built once and then only written;
# every list is capped; every phase wraps; the story loops.
#
# Idempotent: destroys and recreates /project1/delhi and its project-level Out TOP,
# and touches nothing else. No media files: the dataset is below.
#     code = open('scenes/delhi/build.py', encoding='utf-8').read()
#     g = dict(globals()); exec(compile(code, 'build.py', 'exec'), g)
#
# GENERATED: this file is delhi_template.py + verbatim blocks of
# scenes/homestead/build.py (BEGIN/END HOMESTEAD), assembled by gen_delhi.py.

import math
import os

SCENE = 'delhi'
OUTW, OUTH = 1280, 720
ASPECT = OUTW / OUTH
CLOCKLEN = 60.0
STORYDEF = 480.0          # one year every eight minutes
NP = 128                  # particles: NP x NP = 16384
RING = 1.55               # the year's radius, world units

# DELHI 2024, one row per day, 1 January to 31 December (366 days, a leap year).
# (tmax C, tmin C, tmean C, precipitation mm, relative humidity %, max wind km/h,
#  dominant wind direction deg, cloud cover %, PM2.5 daily mean ug/m3)
# Weather: Open-Meteo Historical Weather API (ERA5 reanalysis), New Delhi 28.6139 N 77.2090 E:
#   https://archive-api.open-meteo.com/v1/archive?latitude=28.6139&longitude=77.2090&start_date=2024-01-01&end_date=2024-12-31&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max,wind_direction_10m_dominant,cloud_cover_mean&timezone=Asia%2FKolkata
# PM2.5: Open-Meteo Air Quality API (CAMS global atmospheric composition forecasts), hourly,
#   averaged here to daily means:
#   https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.6139&longitude=77.2090&start_date=2024-01-01&end_date=2024-12-31&hourly=pm2_5&timezone=Asia%2FKolkata
# Retrieved 2026-09-26. Open-Meteo data is CC BY 4.0 (https://open-meteo.com/en/license).
DELHI_2024 = (
    (16.2, 5.9, 10.4, 0, 85, 8.2, 324, 43, 101.7),
    (15.3, 4.6, 9.1, 0, 86, 8.2, 320, 30, 104),
    (15.9, 4.8, 9.5, 0, 89, 10.4, 343, 47, 118.5),
    (17.9, 5.2, 11.5, 0, 82, 10.2, 318, 36, 118.3),
    (17.3, 7.3, 11.7, 0.1, 85, 9.7, 337, 58, 114.6),
    (16.9, 6.3, 11.6, 0, 82, 9, 332, 64, 114), (17.5, 6.1, 11.4, 0, 81, 7.1, 291, 17, 138),
    (18.4, 5.5, 10.9, 0, 86, 8.9, 333, 11, 150.8),
    (18, 6.2, 10.8, 0, 86, 13.9, 316, 15, 102.9), (15.8, 4.6, 9.2, 0, 84, 15, 292, 2, 81),
    (15.5, 5.6, 9.3, 0, 88, 12, 298, 26, 97.3),
    (17.4, 5.6, 10.1, 0, 86, 12.4, 290, 31, 94.4),
    (18.1, 5.9, 10.3, 0, 84, 10.2, 327, 72, 121.1),
    (18, 4.8, 9.7, 0, 86, 10, 313, 35, 102.7), (16.1, 5, 9, 0, 85, 9, 310, 62, 96.2),
    (17.5, 3.9, 8.9, 0, 86, 11, 78, 48, 145.5), (17.8, 4, 9.9, 0, 84, 10.7, 135, 3, 148.7),
    (17.5, 6, 11, 0, 86, 8, 159, 43, 157), (16.8, 6.3, 10.2, 0, 89, 9.2, 160, 41, 174.1),
    (16.1, 5.1, 9.6, 0, 88, 10.3, 343, 32, 161.9),
    (16.1, 5.2, 9, 0, 89, 14.1, 294, 49, 118.1),
    (16.9, 5, 9.2, 0, 86, 10.6, 84, 52, 127.9),
    (17.3, 4.9, 10.4, 0, 88, 8.9, 195, 48, 157.3),
    (18.2, 6.4, 11.3, 0, 84, 8.3, 324, 17, 115.4),
    (17.5, 5.6, 10.2, 0, 88, 10.4, 329, 79, 124.2),
    (18.5, 6, 11.4, 0, 84, 11.3, 294, 86, 147.4),
    (20.6, 6.9, 12.5, 0, 77, 16.8, 289, 12, 73.5),
    (20.3, 7, 13.8, 0, 79, 13.8, 113, 100, 93.5),
    (21.3, 9.5, 14.5, 0, 85, 12.2, 104, 6, 109),
    (20.5, 10, 13.8, 0, 89, 9.4, 320, 51, 150.3),
    (20.2, 9.9, 14, 9, 92, 14.5, 124, 83, 155.1),
    (21.2, 12.2, 15.4, 30, 86, 21.5, 115, 33, 73.6),
    (19.3, 8.5, 13, 0, 84, 15.5, 316, 34, 61.4),
    (20.7, 8.2, 14.1, 0, 70, 11.5, 306, 63, 46),
    (20.7, 12.9, 16, 7.1, 85, 16.2, 156, 71, 70.3),
    (19.8, 10.3, 15.1, 2.1, 83, 12.2, 329, 37, 36.2),
    (18.7, 7.5, 12.2, 0, 75, 15.6, 308, 19, 39.1),
    (18.4, 7.9, 12.5, 0, 66, 23.7, 303, 33, 41.2),
    (19.1, 8.2, 13.1, 0, 64, 27.4, 289, 19, 37.7),
    (20.5, 8.1, 13.4, 0, 66, 15.7, 304, 0, 53.5),
    (19.7, 7.2, 13.1, 0, 78, 11.8, 5, 20, 93.8),
    (21.5, 8.1, 14.1, 0, 75, 9.7, 321, 0, 77.6),
    (21.5, 7.7, 14.3, 0, 75, 9.7, 333, 66, 90.4),
    (21.2, 8.5, 14.9, 0, 73, 10.5, 340, 85, 108.7),
    (22.7, 9.6, 15.8, 0, 74, 13.6, 307, 20, 92.9),
    (23.6, 9.7, 15.8, 0, 69, 15, 304, 0, 73.1),
    (24.5, 8.6, 15.7, 0, 64, 12.8, 312, 0, 68.2),
    (24.6, 9.7, 16.2, 0, 61, 14.9, 289, 2, 58.8),
    (27.1, 10, 18.6, 0, 59, 15.9, 152, 59, 77.4),
    (26.8, 14.7, 20.3, 0, 61, 28.5, 131, 18, 65.2),
    (27.3, 15.3, 20.2, 0.2, 66, 20, 117, 17, 59.5),
    (25.9, 12.2, 18.5, 0, 58, 17.3, 340, 6, 53.8),
    (24, 10.9, 17.4, 0, 51, 16.7, 323, 12, 39.5),
    (22.8, 8.5, 15.6, 0, 48, 15.2, 319, 0, 36.7),
    (23.4, 9.3, 16.2, 0, 45, 12.1, 49, 28, 50.9),
    (25, 10.5, 17.3, 0, 39, 17.7, 35, 45, 39.5),
    (24.6, 11.1, 17.6, 0, 46, 12, 357, 88, 48),
    (24.5, 14.1, 18, 0.9, 46, 16, 324, 48, 44.8),
    (24, 11.4, 17.3, 0, 57, 20.7, 303, 0, 38.8),
    (26.3, 12, 18.4, 0, 56, 13.2, 297, 3, 45.3),
    (26.5, 13.9, 20, 1.7, 60, 16, 100, 91, 61.4),
    (24.7, 17.3, 19.8, 6.5, 74, 33.4, 143, 83, 38.6),
    (22.7, 13.4, 17.6, 10.4, 70, 15.4, 299, 23, 35.8),
    (21.7, 11.1, 15.8, 0, 62, 14.7, 341, 43, 33),
    (20.9, 8.9, 14.7, 0, 54, 15.6, 308, 40, 39.1),
    (21.1, 9.2, 15.1, 0, 56, 15.3, 300, 60, 52),
    (24.2, 10.1, 17.1, 0, 56, 15.1, 316, 3, 56.9),
    (25.4, 11.3, 17.9, 0, 53, 16.8, 323, 0, 38.1),
    (25.2, 11.8, 17.9, 0, 50, 17.4, 301, 43, 40.2),
    (26.6, 12, 19.2, 0, 51, 11.6, 300, 78, 56.1),
    (29.5, 14.8, 22.3, 0, 47, 13.8, 21, 23, 75.3),
    (29.1, 13.9, 21.9, 0, 47, 16.9, 336, 3, 48.7),
    (29.4, 13.9, 21.4, 0.2, 52, 18.2, 319, 8, 46.2),
    (29.2, 14.1, 21.6, 0, 53, 15.8, 346, 4, 40.1),
    (27.2, 14.3, 20.3, 0, 43, 16.9, 300, 13, 36.8),
    (27.6, 12.7, 19.7, 0, 45, 12.9, 310, 39, 44.6),
    (28.8, 11.8, 20.5, 0, 46, 11.5, 301, 50, 50.4),
    (28.5, 13, 20.6, 0, 48, 13, 298, 12, 48.8),
    (29.8, 13.6, 21.5, 0, 45, 16.3, 312, 3, 50.9),
    (32, 14.2, 23.2, 0, 44, 11.6, 328, 4, 59.1),
    (29.2, 16.9, 22.7, 0, 55, 18.7, 115, 43, 64.8),
    (32.4, 17.8, 24.8, 0, 51, 13.3, 124, 3, 64.6),
    (33.8, 18.1, 25.7, 0, 46, 19.6, 315, 7, 51.7),
    (31, 18.6, 24.4, 0.1, 45, 35.3, 345, 73, 53.2),
    (32.8, 16.6, 25, 0, 47, 21.2, 307, 3, 42.7),
    (33.6, 18.5, 26, 0, 42, 14.2, 294, 76, 43.7),
    (36.4, 21.6, 28.4, 0, 41, 20.4, 337, 34, 53.8),
    (37, 21.9, 29, 0, 41, 16.3, 313, 93, 49.5),
    (36.5, 20.9, 28.2, 0, 46, 19.4, 79, 95, 57.1),
    (35.2, 22.8, 28.4, 0, 39, 19.2, 14, 32, 48.2),
    (34.4, 20, 27.4, 0, 36, 21.4, 319, 2, 40.9),
    (31.3, 18.7, 24.9, 0, 38, 20.8, 300, 67, 40.2),
    (32.9, 17.1, 25.3, 0, 33, 21.4, 313, 54, 29.1),
    (35.9, 21.8, 28.3, 0, 24, 18.8, 22, 74, 32.4),
    (36.4, 20.5, 29.2, 0, 26, 18, 2, 69, 29.3),
    (35.6, 21.2, 28.2, 0, 24, 28.2, 306, 80, 33.7),
    (35, 19.6, 27.3, 0, 21, 21.3, 315, 0, 33.9),
    (35.4, 17.5, 26.9, 0, 21, 21.1, 305, 0, 30.1), (36.8, 19, 28, 0, 20, 20, 307, 3, 31.3),
    (37.8, 19.9, 29, 0, 18, 16.6, 335, 50, 34),
    (38.6, 19.8, 28.9, 0, 21, 13.4, 47, 14, 38.2),
    (38, 22.2, 30, 0, 21, 14.2, 84, 15, 43.8),
    (38.8, 21.8, 30.5, 0, 21, 11.3, 86, 62, 37.1),
    (38.5, 25.3, 30.8, 1.2, 27, 16, 150, 73, 56.3),
    (33.8, 22.8, 27.5, 0.5, 45, 15.5, 5, 91, 63.9),
    (36.3, 22.3, 28.8, 1.3, 48, 20.9, 307, 95, 49.2),
    (35.7, 23.5, 29.8, 0, 36, 21.6, 295, 59, 49.4),
    (35.3, 22.2, 29.3, 0, 27, 29.3, 300, 41, 39.5),
    (37.8, 23.7, 30.9, 0, 24, 17.3, 293, 61, 32.8),
    (38.3, 24.6, 31.7, 0, 29, 18.9, 282, 18, 44.4),
    (36.7, 22.3, 30, 0, 28, 21.1, 304, 27, 40.3),
    (36.6, 23.6, 30.1, 0, 27, 17.6, 310, 64, 33.4),
    (37, 24.5, 31.1, 0, 25, 25.5, 311, 30, 26.6),
    (38, 22.6, 30, 0, 26, 23.2, 306, 8, 37.1), (36.9, 21, 29.8, 0, 28, 21.9, 303, 1, 39.3),
    (38.3, 21.5, 30, 0, 24, 23.7, 316, 4, 34.3),
    (39.2, 23.4, 32.2, 0, 23, 32.9, 248, 21, 28.9),
    (37.9, 26, 32, 0, 27, 21.3, 284, 41, 30.6),
    (37.5, 22.7, 30.6, 0, 28, 17, 329, 63, 35.2),
    (38.1, 23.6, 30.8, 0, 26, 23.7, 323, 28, 37.8),
    (36.2, 23.3, 29.7, 0, 25, 19, 304, 0, 40.4),
    (32.7, 20.5, 26.9, 0, 22, 23.6, 314, 0, 57.1),
    (35, 19.3, 27.6, 0, 26, 19.5, 308, 20, 44.8),
    (38.1, 20.7, 30.2, 0, 22, 23.9, 300, 70, 44.3),
    (40.6, 26.5, 33, 0, 19, 16.4, 301, 44, 45.6),
    (40.9, 25, 33.3, 0, 20, 19.2, 306, 4, 41.7),
    (40.6, 26, 33.8, 0, 22, 23.6, 306, 6, 48.3),
    (41.4, 26.2, 34, 0, 25, 18.1, 25, 6, 52.2),
    (39.7, 27, 32.7, 0, 39, 21.1, 111, 16, 60.3),
    (39.6, 26.2, 32.5, 0, 37, 25.3, 106, 6, 65.8),
    (39.5, 26, 32.1, 1.1, 43, 20.9, 106, 23, 60.9),
    (38.8, 26, 31.9, 0.1, 42, 18.5, 3, 29, 64.9),
    (37.8, 27.5, 32.3, 0.1, 38, 15.9, 20, 26, 64.1),
    (40.3, 27.2, 33, 0, 29, 16.4, 335, 32, 51.2),
    (40.7, 24.6, 32.8, 0, 21, 20.5, 316, 10, 33),
    (42.3, 25.4, 34.2, 0, 19, 17.8, 316, 0, 47),
    (42.7, 26.5, 34.5, 0, 18, 18, 339, 0, 57.1),
    (44, 28.1, 36.3, 0, 18, 16.3, 303, 8, 66.3), (44, 27.1, 37, 0, 19, 26.6, 295, 6, 53.5),
    (44.9, 27.7, 36.7, 0, 17, 26.4, 300, 3, 55.6),
    (43.6, 29.1, 36.4, 0, 19, 28.3, 304, 33, 60.4),
    (42.6, 29.1, 35.2, 0, 28, 15.8, 90, 2, 63.6),
    (41.1, 29.8, 35.2, 0.3, 36, 24.4, 108, 5, 54.9),
    (41.1, 30.5, 35.7, 0, 36, 22.9, 125, 7, 52.5),
    (40.9, 30.4, 35.6, 0, 36, 20.6, 112, 3, 51.7),
    (44.4, 30.6, 37.4, 0, 27, 27.4, 311, 6, 56.1),
    (46, 29.5, 38.1, 0, 17, 25.9, 333, 0, 45.7),
    (45.7, 30.2, 38.2, 0, 18, 22.1, 330, 2, 51.3),
    (45.8, 28.9, 37.3, 0, 14, 19.2, 317, 0, 48.2),
    (45.7, 31.1, 38.6, 0, 18, 17.9, 272, 15, 54.6),
    (45.8, 33, 39.2, 0, 16, 25.2, 276, 8, 45.7),
    (45.9, 28.5, 37.6, 0, 12, 25.5, 295, 5, 46.3),
    (44, 31.3, 37.4, 0, 17, 26.4, 283, 60, 45.2),
    (41.4, 30.5, 36.4, 0, 25, 20.7, 293, 37, 42.6),
    (44.4, 29.6, 36.9, 0, 25, 20.2, 284, 7, 48.3),
    (43.1, 30.9, 36.9, 0, 19, 24.1, 278, 8, 51.6),
    (41.7, 30.2, 36.6, 0, 23, 25.4, 289, 19, 62.2),
    (40.8, 28.2, 35, 0, 28, 20, 308, 4, 64.9),
    (42.2, 28.9, 35.2, 0, 30, 22.4, 296, 7, 67.4),
    (40.2, 28.3, 34.7, 0, 27, 25.6, 304, 15, 73.1),
    (42.2, 28.3, 35.1, 0, 23, 19.8, 310, 1, 45.6),
    (43, 27.9, 36, 0, 18, 22.2, 292, 13, 37.6), (43.2, 28.9, 36.3, 0, 19, 20, 290, 11, 37),
    (44.1, 28.8, 36.9, 0, 17, 18.2, 288, 1, 35.4),
    (44.9, 29.6, 37.6, 0, 20, 28.1, 282, 4, 47.9),
    (43.4, 32.8, 37.5, 0, 28, 31.5, 275, 21, 52.4),
    (43.3, 32.2, 37.7, 0, 27, 28.3, 286, 3, 54),
    (44.1, 32.8, 38.4, 0, 25, 25.1, 284, 4, 44.8),
    (44, 33.7, 38.9, 0, 25, 26.8, 280, 9, 45.7),
    (44.2, 34.5, 38.9, 0, 25, 30.9, 279, 6, 50.5),
    (41.3, 33.7, 37, 0.8, 35, 32.1, 269, 29, 61.1),
    (39.3, 25.5, 34, 4.9, 45, 14.5, 219, 35, 61.6),
    (38.3, 25.4, 32.5, 2.1, 53, 28.2, 331, 32, 72.2),
    (38.5, 29.9, 33.7, 0, 51, 12.3, 30, 46, 79.3),
    (39.5, 30.2, 34.5, 0.3, 51, 15.5, 96, 28, 68.2),
    (39.5, 31, 34.1, 1.7, 54, 15.1, 96, 38, 76.5),
    (36.6, 29.8, 32.9, 4, 62, 15.3, 122, 71, 66.6),
    (34.3, 26.8, 31, 23.3, 73, 19.4, 106, 94, 74.1),
    (30.4, 25.4, 28.3, 11.5, 84, 21.7, 108, 92, 34.3),
    (30.6, 25.6, 27.8, 20.9, 85, 14.8, 127, 77, 35.8),
    (32.9, 26.5, 29.3, 18.9, 80, 11.7, 196, 56, 38.7),
    (34.8, 26.8, 30.7, 11.9, 74, 15.6, 304, 39, 50),
    (34.1, 25.9, 30.1, 11.5, 79, 11.8, 275, 75, 45.1),
    (33.6, 26.4, 29.3, 14.1, 84, 14.9, 178, 99, 44.2),
    (32.9, 26, 29.3, 2.5, 83, 16.1, 149, 100, 31.7),
    (31.6, 25.5, 28, 7.3, 83, 11.3, 84, 99, 30.6),
    (30.4, 26.2, 27.8, 0.7, 85, 16.2, 70, 100, 27.1),
    (33, 26, 28.6, 1, 80, 15.8, 67, 91, 19.4),
    (33.5, 25.6, 28.6, 0.1, 76, 14.2, 67, 84, 22.8),
    (33.2, 25.3, 28.9, 0, 76, 11.4, 34, 64, 31.7),
    (32.4, 26.2, 29.5, 4.9, 80, 11.4, 97, 37, 54.6),
    (34.1, 26.5, 30.4, 11.3, 79, 14.8, 161, 79, 75.1),
    (36.4, 26.8, 31.2, 3.9, 76, 21, 230, 77, 61.5),
    (35.3, 27, 30.3, 0.5, 74, 23.4, 266, 56, 62.7),
    (34.3, 25.2, 29.9, 12.4, 77, 11.7, 324, 19, 66.7),
    (34.9, 27, 31.1, 0.3, 72, 8.5, 90, 14, 84.2),
    (33.2, 25.5, 30.2, 3, 76, 21.4, 90, 65, 65.7),
    (34.3, 25.6, 30.7, 17, 77, 15.5, 98, 53, 43.7),
    (34.7, 28.2, 31.2, 0.2, 75, 13.7, 102, 28, 40.5),
    (34.7, 27.7, 31.2, 2, 76, 12.1, 117, 81, 41.9),
    (34.4, 27.3, 30.5, 0.9, 77, 12, 113, 72, 45.9),
    (35.1, 27.1, 31, 0.2, 75, 13, 118, 46, 50.4),
    (34.8, 27.2, 31.1, 1.9, 78, 16.3, 118, 41, 59.6),
    (34.6, 27.8, 31, 5, 78, 10.9, 116, 91, 43.8),
    (34.8, 27, 30.4, 4.3, 80, 14.9, 102, 66, 55.4),
    (33.7, 26.4, 29.5, 6.9, 82, 9.5, 91, 75, 62.5),
    (34.7, 27.2, 30.8, 0.6, 76, 11.1, 36, 81, 57.9),
    (33, 27.4, 29.9, 10.2, 81, 13, 41, 98, 54.8),
    (34, 28, 30.5, 4.5, 81, 16.1, 83, 84, 48.2),
    (35.1, 28.6, 31.4, 6, 77, 15.7, 98, 39, 40.9),
    (35.7, 28.3, 31.8, 0.3, 73, 15.8, 107, 52, 37.3),
    (36.4, 29, 32.8, 0.1, 70, 13.7, 130, 60, 45.6),
    (37.1, 26.5, 31, 116, 78, 17.4, 199, 100, 35.4),
    (31.2, 25.5, 28.2, 34.7, 85, 17.8, 157, 99, 34.7),
    (32.2, 25.5, 28.4, 3, 83, 17.6, 115, 82, 32),
    (32.4, 26, 28.9, 1.9, 82, 20.9, 123, 45, 26.9),
    (33.5, 26.9, 29.7, 0.1, 74, 25.9, 91, 37, 25.6),
    (32.6, 26.4, 29, 1.2, 76, 31, 112, 55, 21.6),
    (31.8, 26.4, 29, 0.1, 76, 14.7, 178, 70, 25.3),
    (30.1, 25.5, 27.3, 16.4, 86, 11.2, 209, 98, 29.8),
    (31.5, 25.5, 27.6, 10.8, 87, 12.3, 133, 82, 34.5),
    (31.8, 25.3, 27.8, 30.8, 87, 8.4, 101, 99, 34.9),
    (31.3, 24.9, 27.6, 16.7, 87, 9.8, 75, 100, 44.4),
    (30.9, 25.6, 27.3, 11.4, 89, 11.1, 106, 99, 37.2),
    (30, 25.6, 26.7, 10.9, 91, 13.6, 79, 98, 28.7),
    (30.8, 25.2, 27.3, 9.1, 90, 15.1, 84, 94, 30.8),
    (30.7, 25.9, 28, 7.8, 89, 10.8, 84, 98, 35.6),
    (32.2, 25.9, 28.4, 10.9, 87, 14.1, 106, 85, 37),
    (32.3, 25.5, 27.8, 15, 88, 15.5, 113, 97, 24),
    (31.9, 25.7, 28.5, 7.7, 86, 9.6, 353, 97, 31.3),
    (32.7, 26.2, 29.1, 2.3, 83, 14.7, 281, 63, 41.3),
    (32.7, 26.2, 29, 1.6, 82, 17, 284, 87, 30.4),
    (31.6, 26.4, 28.2, 4.3, 85, 12.7, 231, 97, 37.5),
    (32, 25.1, 28.4, 5.4, 86, 8.7, 123, 90, 38.6),
    (32.8, 24.7, 28.2, 7, 86, 10.7, 255, 66, 43.5),
    (30.7, 24.9, 27.4, 0.9, 86, 10.5, 77, 74, 44),
    (31.5, 25.3, 28.3, 8.8, 84, 16.6, 50, 71, 54),
    (32.2, 24.9, 28.8, 15.2, 79, 22, 88, 45, 24.5),
    (31.6, 26, 28.2, 3.8, 83, 22.7, 100, 44, 28),
    (31.2, 24.3, 27.2, 11.1, 85, 24.1, 114, 88, 25.1),
    (30.3, 24.2, 26.8, 7.9, 87, 16.2, 120, 91, 19.8),
    (30.9, 24.4, 26.9, 19.5, 87, 19.4, 124, 81, 31.1),
    (31.3, 25, 27.5, 7.5, 88, 9.1, 95, 53, 46.6),
    (33.3, 25.6, 29.2, 0, 79, 13.3, 314, 22, 42.9),
    (33.5, 25.9, 29.6, 0.1, 76, 13.9, 327, 38, 39.5),
    (31.5, 25.1, 28, 11.7, 84, 14.1, 110, 83, 33.9),
    (31.6, 25.4, 27.4, 17.8, 87, 13.4, 87, 66, 31.7),
    (30.8, 24.4, 27.2, 0.9, 87, 10.6, 320, 87, 33.1),
    (31.6, 24.8, 27.5, 2.9, 84, 12.8, 282, 40, 48.7),
    (30.6, 24.2, 26.5, 14.7, 89, 15.6, 108, 80, 34.8),
    (30.4, 24.1, 26.8, 23.6, 88, 11.8, 109, 94, 29.5),
    (31.3, 24.4, 27.6, 14.1, 87, 10.3, 313, 97, 45.1),
    (32.7, 25.2, 28.4, 3.4, 82, 13.2, 321, 55, 47.5),
    (30.7, 24.9, 27.2, 11.8, 89, 11.5, 69, 86, 42.8),
    (31.7, 25, 27.5, 26.7, 89, 16.6, 356, 75, 43.4),
    (27.2, 23.9, 25.4, 100.8, 91, 24.4, 7, 97, 24),
    (30, 23.3, 25.4, 54.7, 89, 22.7, 286, 83, 37.4),
    (29.9, 22.6, 26, 4.7, 84, 18.7, 294, 47, 47.4),
    (31.2, 22.5, 26.4, 0.1, 79, 19.8, 290, 15, 45),
    (32.1, 23.7, 27.2, 0, 73, 17.3, 289, 4, 57.3),
    (31.5, 23.9, 27.6, 0, 74, 11.6, 303, 62, 66.4),
    (27.7, 22.8, 24.9, 62.7, 86, 17.9, 35, 99, 39.5),
    (29.8, 22.8, 26.2, 3.7, 85, 15.7, 88, 59, 43.7),
    (31.1, 24, 27.2, 0, 80, 12.2, 134, 28, 57.9),
    (31.6, 24.8, 27.9, 0.2, 79, 9.2, 188, 45, 70),
    (33.1, 25.3, 29, 0, 77, 6.9, 305, 27, 72.5),
    (33.3, 25.1, 28.9, 0, 78, 10.7, 295, 1, 66),
    (33.6, 25.2, 29.3, 0, 77, 6.9, 229, 7, 95.4),
    (33, 26.4, 29, 0.4, 81, 16.1, 119, 50, 84.2),
    (31.4, 25.3, 27.9, 0.4, 82, 13.2, 116, 86, 28),
    (30.9, 24.8, 27.3, 0.8, 80, 16, 95, 31, 20.4),
    (30.5, 23.1, 26.3, 0, 81, 11.6, 74, 73, 24.5),
    (30.7, 22.6, 26.4, 0.3, 83, 10.1, 59, 61, 35.1),
    (32.7, 23.5, 27.7, 0, 77, 15.2, 288, 29, 49.6),
    (33.2, 24, 28.3, 0, 76, 14.9, 283, 1, 61.9),
    (34.6, 24.7, 28.9, 0, 73, 17.7, 270, 0, 73.8),
    (33.9, 24.5, 28.6, 0, 66, 18.4, 284, 0, 72.6),
    (33.5, 23.8, 28.3, 0, 68, 13.4, 269, 0, 68.3),
    (33.6, 24.2, 28.4, 0, 66, 17.8, 272, 7, 59.3),
    (33.6, 23.7, 27.8, 0, 65, 15.9, 306, 5, 42.3),
    (32.4, 21.9, 26.7, 0, 71, 9.1, 318, 0, 44.2),
    (32.5, 22.2, 27, 0, 70, 10, 334, 1, 46.6),
    (32.2, 20.6, 26.5, 0, 65, 14.8, 301, 2, 36.9),
    (32.3, 21, 26.1, 0, 60, 13.9, 299, 8, 37.8),
    (31.7, 19.1, 25, 0, 56, 13.7, 282, 5, 39.7),
    (32, 19.1, 25.3, 0, 61, 10.6, 279, 0, 45.9), (32.1, 19.7, 26, 0, 57, 8.7, 303, 25, 62),
    (31.8, 20.5, 25.7, 0, 55, 10.4, 312, 5, 53.4),
    (31.9, 19.4, 25.2, 0, 57, 13.1, 284, 0, 52.1),
    (32.4, 19.6, 25.7, 0, 57, 9, 260, 53, 67.8),
    (32.8, 20.6, 26.3, 0, 63, 9.2, 104, 33, 90.8),
    (33.4, 20.1, 26.1, 0, 65, 10.1, 136, 0, 88.3),
    (33.7, 21, 26.8, 0, 63, 9.9, 178, 1, 92.3), (33, 20.2, 26.5, 0, 68, 10.5, 94, 4, 99.9),
    (32.3, 20, 25.6, 0, 70, 9.1, 63, 0, 99), (31.5, 20.1, 25.6, 0, 67, 9.5, 41, 0, 103.7),
    (32.1, 20.1, 26.1, 0, 61, 17.5, 312, 1, 78.5),
    (32.6, 20.2, 25.5, 0, 59, 14.8, 309, 0, 68.3),
    (32.1, 19.1, 25, 0, 61, 17.9, 302, 0, 58.2),
    (31.6, 19, 24.6, 0, 66, 13.2, 338, 0, 58.7),
    (31.1, 20.4, 25.2, 0, 74, 8.5, 114, 0, 90.9),
    (31.4, 21, 25.7, 0, 71, 10.9, 154, 0, 99.1),
    (32.9, 20.6, 26.4, 0, 70, 8.9, 159, 0, 91),
    (34.3, 21.3, 27, 0, 65, 12.4, 330, 0, 86.3),
    (32.8, 20.8, 26.1, 0, 63, 18, 295, 0, 72.5),
    (32, 19.3, 24.9, 0, 53, 17.6, 293, 0, 55.3),
    (31.7, 17.7, 24.4, 0, 54, 10.7, 293, 0, 70.9),
    (31.3, 18.2, 24.4, 0, 54, 9.3, 31, 0, 93),
    (30.4, 17.5, 23.7, 0, 62, 9.5, 297, 0, 121.6),
    (29.4, 18.1, 23.4, 0, 71, 10.5, 86, 1, 133.8),
    (30.2, 18.1, 23.9, 0, 67, 8.9, 296, 0, 145), (30.1, 19, 24.2, 0, 67, 7.4, 147, 0, 143),
    (30.3, 19, 24.6, 0, 66, 8.1, 146, 2, 154.4),
    (30.6, 19.7, 24.5, 0, 68, 11.4, 145, 2, 124.2),
    (30.2, 19.3, 24.3, 0, 69, 9.6, 109, 0, 107.8),
    (29.8, 18.5, 23.9, 0, 74, 8, 77, 1, 122.2), (31.2, 19, 24.9, 0, 60, 15, 260, 0, 107.6),
    (30, 18.8, 24.1, 0, 56, 10.5, 299, 0, 140.9),
    (30, 19, 24.1, 0, 55, 9.6, 304, 0, 156.3),
    (29, 18.7, 23.7, 0, 51, 12.6, 299, 0, 110.5),
    (28.8, 17.6, 23.3, 0, 55, 10.5, 298, 1, 125.7),
    (28.5, 18, 22.9, 0, 58, 8.9, 297, 1, 133.1),
    (26.4, 15.9, 20.8, 0, 60, 7.8, 292, 1, 106.5),
    (25.9, 14.2, 20.1, 0, 51, 8.7, 289, 0, 95.5),
    (25.9, 13.6, 19.8, 0, 50, 8.3, 288, 0, 105.4),
    (25.8, 13.6, 19.7, 0, 51, 7.7, 289, 0, 113.1), (26.3, 14, 20.3, 0, 54, 7, 293, 0, 153),
    (27.5, 14.1, 20.9, 0, 51, 6, 249, 0, 176.2),
    (27.7, 15.7, 21.4, 0, 48, 10.6, 271, 0, 90.5),
    (25.9, 15.1, 20.6, 0, 57, 11, 286, 0, 105),
    (25.6, 13.9, 19.7, 0, 56, 10.4, 286, 0, 72.9),
    (26, 13.6, 19.8, 0, 49, 8.1, 300, 0, 81.7),
    (25.5, 12.8, 19.4, 0, 50, 6.5, 333, 0, 101.3),
    (24.6, 12.5, 18.9, 0, 59, 5.1, 347, 0, 121.1),
    (24.9, 12.4, 18.9, 0, 60, 8, 307, 0, 97.3), (24.8, 14, 19.4, 0, 61, 8.1, 301, 0, 69.5),
    (25.8, 13.3, 19.5, 0, 58, 7.1, 300, 0, 67.8),
    (26.5, 13.5, 20.1, 0, 56, 10.7, 307, 0, 50.6),
    (25.6, 15.2, 20.1, 0, 50, 14.2, 298, 0, 35.5),
    (23.6, 12, 17.8, 0, 45, 12.7, 283, 0, 33.3),
    (23.5, 11.3, 17.5, 0, 47, 12, 287, 0, 48.9), (23.1, 9.7, 16.9, 0, 44, 5, 283, 0, 100),
    (22.3, 11, 16.1, 1.5, 56, 13.1, 124, 19, 97.8),
    (20.2, 10.4, 15.3, 0, 65, 8.7, 36, 1, 66.6),
    (20.1, 9.8, 14.5, 0, 53, 13, 304, 0, 53.9),
    (20.2, 8.2, 13.9, 0, 47, 10.5, 292, 0, 46.2),
    (20.5, 7.7, 14.2, 0, 52, 10.1, 299, 0, 70.2),
    (20.6, 9.2, 14.8, 0, 48, 15.1, 296, 1, 47.7),
    (20.7, 8.6, 14.6, 0, 44, 12.5, 287, 0, 45.8),
    (21.1, 7.3, 14.3, 0, 51, 6.5, 298, 0, 92.9), (21, 7, 14.2, 0, 67, 5.9, 314, 0, 152.8),
    (20.6, 7.7, 14.2, 0, 74, 4.4, 325, 30, 185.2),
    (20.9, 7.6, 14, 0, 69, 7.2, 279, 12, 145.8),
    (20.8, 8, 14.5, 0, 62, 8.3, 123, 0, 187.2),
    (23.2, 10.2, 16.2, 0, 62, 6.5, 5, 1, 135.9),
    (22.1, 9.2, 15.5, 0, 65, 7.3, 320, 3, 135.9),
    (22.5, 10.5, 16.3, 0, 60, 7.2, 134, 31, 179.7),
    (17.6, 11.6, 14.5, 1.4, 68, 10.1, 98, 56, 129.5),
    (18.7, 11.4, 14.7, 0.5, 77, 8.9, 46, 49, 111.1),
    (20.6, 10.8, 15.1, 0, 78, 7.6, 319, 5, 119.4),
    (22.6, 9.9, 16.1, 0, 68, 4.8, 350, 18, 164.8),
    (17.1, 13.8, 15.1, 29.9, 84, 11.3, 64, 87, 120.5),
    (18.1, 12.3, 14.9, 4.6, 89, 7.8, 338, 62, 112.4),
    (18.3, 10.6, 13.7, 0, 86, 9.6, 307, 16, 93.9),
    (18.1, 9.6, 12.7, 0, 87, 11, 290, 20, 88),
    (16.1, 7.5, 11.3, 0, 89, 5.1, 297, 41, 144.8),
)

NDAYS = len(DELHI_2024)
MONTHS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')
MLEN = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
# the chapters, as in Wind of Boston: the year falls into them by itself
CHAPTERS = [
    ('winter',  'I  -  WINTER, FOG',          4),      # day index to jump to
    ('spring',  'II  -  SPRING',              70),
    ('heat',    'III  -  LOO, THE HEAT',      140),    # the late-May heatwave
    ('monsoon', 'IV  -  MONSOON',             179),    # 28 June, 116 mm
    ('smoke',   'V  -  SMOKE',                308),    # early November haze
    ('chill',   'VI  -  CHILL',               348),
]


def _nz(x, lo, hi):
    return min(1.0, max(0.0, (x - lo) / (hi - lo)))


# the data, normalised once: T, RH, P, W / sin(wind), cos(wind), cloud, PM
NORM = []
for (tmax, tmin, tmean, pr, rh, wmax, wdir, cloud, pm) in DELHI_2024:
    T = 0.5 * _nz(tmean, 8.0, 38.0) + 0.5 * _nz(tmax, 14.0, 46.0)
    P = min(1.0, math.log1p(pr) / math.log1p(60.0))
    W = _nz(wmax, 4.0, 30.0)
    PM = _nz(math.log(max(pm, 1.0)), math.log(20.0), math.log(190.0))
    a = math.radians(wdir)
    NORM.append((round(T, 4), round(rh / 100.0, 4), round(P, 4), round(W, 4),
                 round(math.sin(a), 4), round(math.cos(a), 4), round(cloud / 100.0, 4),
                 round(PM, 4)))

proj = op('/project1')
for stale in (SCENE, SCENE + '_out'):
    o = proj.op(stale)
    if o:
        o.destroy()

s = proj.create(containerCOMP, SCENE)
s.nodeX, s.nodeY = 0, -6200
s.par.w, s.par.h = OUTW, OUTH


# ---- BEGIN HOMESTEAD (verbatim) ----
def C(type_, name, x, y, **params):
    o = s.create(type_, name)
    o.nodeX, o.nodeY = x, y
    for k, v in params.items():
        setattr(o.par, k, v)
    return o


def W(src, dst, idx=0):
    src.outputConnectors[0].connect(dst.inputConnectors[idx])


def res(o, w=OUTW, h=OUTH, fmt='rgba16float'):
    o.par.outputresolution = 'custom'
    o.par.resmult = False
    o.par.resolutionw, o.par.resolutionh = w, h
    o.par.format = fmt
    return o


def soft(o, **params):
    missed = []
    for k, v in params.items():
        if hasattr(o.par, k):
            setattr(o.par, k, v)
        else:
            missed.append(k)
    if missed:
        print('  [soft] %s: no such params %s' % (o.name, missed))
    return o


def menu_pick(par, *wanted):
    """Set a menu parameter to the first of `wanted` that actually exists.

    TD accepts an invalid menu value SILENTLY and lands on entry zero. Never assign
    a menu value you have not seen in the list.
    """
    names = list(par.menuNames or [])
    for wname in wanted:
        if wname in names:
            par.val = wname
            return wname
    print('  [menu] %s: none of %s in %s' % (par.name, wanted, names))
    return par.eval()


# EVERY INTERNAL REFERENCE IS RELATIVE (see bayou): an absolute path makes a copy
# of this COMP, or a second .tox of it, silently drive the ORIGINAL's DATs.


def hdr(**kw):
    return ''.join('%s = %r\n' % (k, v) for k, v in sorted(kw.items())) + '\n'
# ---- END HOMESTEAD ----


# ---------------------------------------------------------------------------
# PERFORMANCE SURFACE
# ---------------------------------------------------------------------------
pg = s.appendCustomPage('Delhi')
pg.appendMenu('Audiosrc', label='Audio Source')
s.par.Audiosrc.menuNames = ['device', 'file']
s.par.Audiosrc.menuLabels = ['Audio Device In', 'Audio File In (test)']
s.par.Audiosrc = 'file'

for nm, label, val, lo, hi in [
    ('Reactivity', 'Reactivity',          1.0, 0.0, 3.0),
    ('Devgain',    'Device In Gain',      6.0, 1.0, 30.0),
    ('Storylen',   'One Year (s)',   STORYDEF, 60.0, 3600.0),
    ('Refbpm',     'Reference BPM',     124.0, 60.0, 200.0),
    ('Beatdrive',  'Beat Drive',          1.0, 0.0, 1.0),
    ('Timeoffset', 'Time Offset (s)',     0.0, -600.0, 5000.0),
    ('Focus',      'Present Width (days)', 16.0, 3.0, 60.0),
    ('Flow',       'Flow',                1.0, 0.0, 3.0),
    ('Psize',      'Particle Size',       0.032, 0.005, 0.2),
    ('Pbright',    'Particle Brightness', 1.0, 0.1, 3.0),
    ('Exposure',   'Exposure',            1.0, 0.2, 3.0),
    ('Trails',     'Trails',              1.0, 0.0, 1.2),
    ('Glow',       'Glow',                1.0, 0.0, 3.0),
    ('Haze',       'Smog Veil',           1.0, 0.0, 2.0),
    ('Label',      'Data Readout',        0.8, 0.0, 1.0),
    ('Vignette',   'Vignette',            0.8, 0.0, 2.0),
]:
    pg.appendFloat(nm, label=label)
    par = getattr(s.par, nm)
    par.normMin, par.normMax = lo, hi
    par.default = val
    par.val = val

_RO = [('Bpm', 0, 200), ('Showt', 0, 5000), ('Day', 0, 366), ('Chapter', 0, len(CHAPTERS)),
       ('Coh', 0, 1), ('Tension', 0, 1), ('Labelfade', 0, 1),
       ('Bassm', 0, 1), ('Highm', 0, 1), ('Energym', 0, 1)]
for _mn, _lo, _hi in _RO:
    pg.appendFloat(_mn, label=_mn)
    _p = getattr(s.par, _mn)
    _p.normMin, _p.normMax = _lo, _hi
    _p.readOnly = True

pg.appendToggle('Loop', label='Loop the Year')
s.par.Loop.default = True
s.par.Loop.val = True
pg.appendToggle('Gather', label='G - GATHER (hold the year in its data form)')
s.par.Gather.val = False
pg.appendStr('Scaletxt', label='Chapter')
s.par.Scaletxt.readOnly = True
pg.appendStr('Datatxt', label='Data')
s.par.Datatxt.readOnly = True

for cp, label, _d in CHAPTERS:
    pg.appendPulse('Go' + cp, label=label)
pg.appendPulse('Burst', label='B - BURST (a release, now)')
pg.appendPulse('Restart', label='0 - 1 JANUARY')
pg.appendPulse('Reseed', label='N - RESEED THE FLOW')

# ---------------------------------------------------------------------------
# AUDIO FRONT END, CLOCK, TEMPO — verbatim from homestead
# ---------------------------------------------------------------------------
# ---- BEGIN HOMESTEAD (verbatim) ----
adev = C(audiodeviceinCHOP, 'audio_device', 0, 1200)
adev.par.active.expr = "parent().par.Audiosrc.menuIndex == 0"

afile = C(audiofileinCHOP, 'audio_file', 0, 1320, repeat=True, play=True)
_rel = os.path.join('Samples', 'Audio', 'JeremyCaulfield_www.dumb-unit.com.mp3')
for _base in ('', 'Contents/Resources/tfs', 'tfs', 'Contents/Resources'):
    _cand = os.path.join(str(app.installFolder), _base, _rel)
    if os.path.exists(_cand):
        afile.par.file = _cand
        break

audio = C(switchCHOP, 'audio_src', 170, 1260)
audio.par.index.expr = "parent().par.Audiosrc.menuIndex"
W(adev, audio, 0)
W(afile, audio, 1)

mono = C(mathCHOP, 'audio_mono', 340, 1260, chanop='avg')
W(audio, mono)

gain = C(mathCHOP, 'audio_gain', 500, 1260)
gain.par.gain.expr = ("parent().par.Reactivity * (parent().par.Devgain.eval() "
                      "if parent().par.Audiosrc.menuIndex == 0 else 1.0)")
W(mono, gain)

band_nulls = []
for nm, filt, cut, envw, fw, frm, to, ny in [
    ('bass', 'lowpass', 700.0, 0.15, 0.10, 0.7, 1.0, 1180),
    ('high', 'highpass', 3000.0, 0.15, 0.50, 0.5, 1.0, 1340),
]:
    af = C(audiofilterCHOP, 'af_' + nm, 660, ny, filter=filt)
    soft(af, cutofflog=math.log10(cut), cutofffrequency=cut)
    W(gain, af)
    en = C(envelopeCHOP, 'env_' + nm, 820, ny, width=envw)
    W(af, en)
    rs = C(resampleCHOP, 'rs_' + nm, 980, ny, method='rate', rate=60, timeslice=True)
    W(en, rs)
    mt = C(mathCHOP, 'math_' + nm, 1140, ny)
    mt.par.fromrange1, mt.par.fromrange2 = 0.0, frm
    mt.par.torange1, mt.par.torange2 = 0.0, to
    W(rs, mt)
    fl = C(filterCHOP, 'filt_' + nm, 1300, ny, type='gaussian')
    soft(fl, width=fw, widthunit='seconds')
    W(mt, fl)
    fl.par.renamefrom = '*'
    fl.par.renameto = nm
    band_nulls.append(fl)

env_all = C(envelopeCHOP, 'env_energy', 820, 1460, width=0.35)
W(gain, env_all)
rs_all = C(resampleCHOP, 'rs_energy', 980, 1460, method='rate', rate=60,
           timeslice=True)
W(env_all, rs_all)
math_all = C(mathCHOP, 'math_energy', 1140, 1460)
math_all.par.fromrange1, math_all.par.fromrange2 = 0.0, 0.6
math_all.par.torange1, math_all.par.torange2 = 0.0, 1.0
W(rs_all, math_all)
filt_all = C(filterCHOP, 'filt_energy', 1300, 1460, type='gaussian')
soft(filt_all, width=0.8, widthunit='seconds')
W(math_all, filt_all)
filt_all.par.renamefrom = '*'
filt_all.par.renameto = 'energy'
band_nulls.append(filt_all)

bands = C(mergeCHOP, 'audio_bands', 1460, 1300)
for i, b in enumerate(band_nulls):
    W(b, bands, i)
null_audio = C(nullCHOP, 'null_audio', 1620, 1300)
W(bands, null_audio)

# ---------------------------------------------------------------------------
# MASTER CLOCK — one free-running timerCHOP, never seeked.
# ---------------------------------------------------------------------------
timer = C(timerCHOP, 'clock', 0, 1000, lengthunits='seconds', length=CLOCKLEN,
          cycle=True, cyclelimit=False, play=True,
          outfraction=True, outcycle=True, outcycleplusfraction=True)

# ---------------------------------------------------------------------------
# TEMPO + DROP — verbatim from monsoon.
# ---------------------------------------------------------------------------
TEMPO_BODY = '''# Beat detector, tempo estimator and drop detector.
import numpy as np
#
# A BEAT is a transient: positive flux (the RISE of a dedicated kick band) against an
# EMA of that flux. A DROP is SUSTAIN: the wide bass band sitting well above its own
# recent median for several frames running.

_state = {'prev': 0.0, 'fluxavg': 0.0, 'last_t': 0.0, 'last_beat': -99.0,
          'factor': 1.0, 'seen': False, 'period': 0.5, 'rate': 60.0,
          'beatstr': 0.0, 'fluxpeak': 1e-4,
          'flux_hist': [], 'acc': 0,
          'bhist': [], 'hot': 0, 'last_drop': -99.0}


def onCook(scriptOp):
    src = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    clk = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    aud = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    par = scriptOp.parent().par
    st = _state

    level = 0.0
    try:
        level = max(abs(v) for v in src.chan(0).vals)
    except Exception:
        pass
    try:
        now = float(clk['cycles_plus_fraction'][0]) * CLOCKLEN
    except Exception:
        now = st['last_t']

    dt = max(0.0, now - st['last_t'])
    st['last_t'] = now

    flux = max(0.0, level - st['prev'])
    st['prev'] = level
    a = min(1.0, dt / 0.6) if dt > 0 else 0.0
    st['fluxavg'] += (flux - st['fluxavg']) * a

    beat = 0.0
    beatstr = st['beatstr']
    if flux > max(st['fluxavg'] * 1.9, 0.004):
        if now - st['last_beat'] > REFRACTORY:
            st['last_beat'] = now
            st['seen'] = True
            beat = 1.0
            st['fluxpeak'] = max(flux, st['fluxpeak'] * FLUXPEAKDECAY, 1e-4)
            beatstr = min(1.0, flux / st['fluxpeak'])
            st['beatstr'] = beatstr

    # TEMPO: autocorrelation of the onset envelope, with a harmonic sum so the
    # fundamental wins over half-tempo.
    st['rate'] += (1.0 / max(dt, 1e-3) - st['rate']) * 0.02 if dt > 0 else 0.0
    st['flux_hist'].append(flux)
    del st['flux_hist'][:-TEMPOHIST]
    st['acc'] += 1
    if st['acc'] >= 15 and len(st['flux_hist']) >= TEMPOHIST * 0.6:
        st['acc'] = 0
        x = np.array(st['flux_hist'], dtype=np.float64)
        x -= x.mean()
        if float(x.std()) > 1e-7:
            ac = np.correlate(x, x, 'full')[len(x) - 1:]
            rate = max(20.0, min(200.0, st['rate']))
            lo = max(2, int(round(60.0 / 200.0 * rate)))
            hi = min(len(ac) - 1, int(round(60.0 / 55.0 * rate)))
            if hi > lo + 2:
                best, bestscore = -1, -1e18
                for lag in range(lo, hi + 1):
                    sc = float(ac[lag])
                    if lag * 2 < len(ac):
                        sc += 0.6 * float(ac[lag * 2])
                    if lag * 3 < len(ac):
                        sc += 0.3 * float(ac[lag * 3])
                    if sc > bestscore:
                        bestscore, best = sc, lag
                if best > 0:
                    st['period'] = best / rate
    period = st['period']
    bpm = min(200.0, max(50.0, 60.0 / max(period, 1e-3)))

    ref = max(1.0, float(par.Refbpm.eval()))
    for _ in range(3):
        if bpm > ref * 1.45:
            bpm *= 0.5
        elif bpm < ref * 0.72:
            bpm *= 2.0
        else:
            break

    quiet = st['seen'] and now - st['last_beat'] > SILENCE
    if not st['seen']:
        target = 1.0
    else:
        target = REF_FLOOR if quiet else bpm / max(1.0, float(par.Refbpm.eval()))
    target = min(REF_CEIL, max(REF_FLOOR, target))
    st['factor'] += (target - st['factor']) * min(1.0, dt * 0.6)

    drive = float(par.Beatdrive.eval())
    factor = 1.0 + (st['factor'] - 1.0) * drive

    bass = 0.0
    try:
        bass = float(aud['bass'][0])
    except Exception:
        pass
    st['bhist'].append(bass)
    del st['bhist'][:-DROPHIST]
    hist = sorted(st['bhist'])
    med = hist[len(hist) // 2] if hist else 0.0
    drop = 0.0
    if bass > max(med * DROPRATIO, DROPFLOOR):
        st['hot'] += 1
        if st['hot'] >= DROPFRAMES and now - st['last_drop'] > DROPHOLD:
            st['last_drop'] = now
            drop = 1.0
    else:
        st['hot'] = 0

    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish, ~0.6 MB a minute even on a few 1-sample
    # channels. Build the channels once; after that only write values.
    # (numChans cannot be read from inside a cook, so whether they exist is
    # tracked here; if a write ever fails they are rebuilt and the write retried.)
    names = ('factor', 'bpm', 'beat', 'beatstr', 'drop', 'bassmed')
    vals = (factor, bpm if (st['seen'] and not quiet) else 0.0, beat, beatstr,
            drop, med)
    for attempt in (0, 1):
        try:
            if not st.get('built'):
                scriptOp.clear()
                for n in names:
                    scriptOp.appendChan(n)
                scriptOp.numSamples = 1
                st['built'] = True
            for i, v in enumerate(vals):
                scriptOp[i][0] = v
            break
        except Exception:
            st['built'] = False
    try:
        par.Bpm.val = bpm if (st['seen'] and not quiet) else 0.0
    except Exception:
        pass
    return
'''

tempo_src = C(textDAT, 'tempo_src', 1780, 1240)
tempo_src.text = hdr(
    CLOCKLEN=CLOCKLEN, REF_FLOOR=0.25, REF_CEIL=2.50, REFRACTORY=0.30, SILENCE=2.5,
    DROPHIST=240, DROPRATIO=1.55, DROPFLOOR=0.045, DROPFRAMES=3, DROPHOLD=6.0,
    TEMPOHIST=420, FLUXPEAKDECAY=0.9990,
) + TEMPO_BODY

tempo = C(scriptCHOP, 'tempo', 1940, 1240)
tempo.par.callbacks = tempo_src.name
af_kick = C(audiofilterCHOP, 'af_kick', 660, 1020, filter='lowpass')
soft(af_kick, cutofflog=math.log10(140.0), cutofffrequency=140.0)
W(gain, af_kick)
env_kick = C(envelopeCHOP, 'env_kick', 820, 1020, width=0.025)
W(af_kick, env_kick)
rs_kick = C(resampleCHOP, 'rs_kick', 980, 1020, method='rate', rate=120,
            timeslice=True)
W(env_kick, rs_kick)
W(rs_kick, tempo, 0)
W(timer, tempo, 1)
W(null_audio, tempo, 2)
# ---- END HOMESTEAD ----

# ---------------------------------------------------------------------------
# TENSION — the build-up detector from `fault` (see patterns.md, "Detecting a
# build-up"), with its publish fixed to build its channels once: the original
# clear()s and re-appends every cook, which is the known native leak.
# ---------------------------------------------------------------------------
TENSION_BODY = '''# A build-up is three things at once: RISE (short energy over long energy), LOWCUT
# (the bass below its own median while the track is loud: the filter sweep), and
# DENSITY (high-band onset rate). Fast attack, slow release; IMMINENCE is tension
# that has been held for seconds; everything is suppressed just after a drop.
_st = {'lastt': None, 'fast': 0.0, 'slow': 0.0, 'risepk': 1e-3,
       'onsets': [], 'prevhigh': 0.0, 'denspk': 1e-3,
       'tension': 0.0, 'hot': 0.0, 'lastdrop': -99.0, 'built': False}


def onCook(scriptOp):
    clk = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    aud = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    mus = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    st = _st

    def ch(inp, n, dv=0.0):
        if inp is None:
            return dv
        try:
            return float(inp[n][0])
        except Exception:
            return dv

    now = ch(clk, 'cycles_plus_fraction', 0.0) * CLOCKLEN
    if st['lastt'] is None:
        st['lastt'] = now
    dt = max(0.0, min(0.2, now - st['lastt']))
    st['lastt'] = now
    energy, bass, high = ch(aud, 'energy'), ch(aud, 'bass'), ch(aud, 'high')
    bassmed, drop = ch(mus, 'bassmed'), ch(mus, 'drop')
    if drop > 0.5:
        st['lastdrop'] = now
    if dt > 0.0:
        st['fast'] += (energy - st['fast']) * min(1.0, dt / FASTT)
        st['slow'] += (energy - st['slow']) * min(1.0, dt / SLOWT)
    raw = max(0.0, st['fast'] - st['slow'])
    st['risepk'] = max(raw, st['risepk'] * PEAKDECAY, 1e-3)
    rise = min(1.0, raw / st['risepk'])
    deficit = max(0.0, 1.0 - bass / bassmed) if bassmed > 1e-4 else 0.0
    lowcut = min(1.0, deficit * 1.35) * min(1.0, st['fast'] / max(LOUD, 1e-4))
    if high > st['prevhigh'] * 1.06 + 0.004:
        st['onsets'].append(now)
    st['prevhigh'] = high
    while st['onsets'] and now - st['onsets'][0] > DENSWIN:
        st['onsets'].pop(0)
    del st['onsets'][:-400]
    rawd = len(st['onsets']) / DENSWIN
    st['denspk'] = max(rawd, st['denspk'] * PEAKDECAY, 1e-3)
    density = min(1.0, rawd / st['denspk'])
    target = min(1.0, WRISE * rise + WLOW * lowcut + WDENS * density) ** GAMMA
    since = now - st['lastdrop']
    if since < AFTERDROP:
        target *= max(0.0, since) / AFTERDROP
    tau = ATTACK if target > st['tension'] else RELEASE
    if dt > 0.0:
        st['tension'] += (target - st['tension']) * min(1.0, dt / tau)
    tension = min(1.0, max(0.0, st['tension']))
    if dt > 0.0:
        if tension > IMMTHR:
            st['hot'] = min(1.0, st['hot'] + dt / IMMRISE)
        else:
            st['hot'] = max(0.0, st['hot'] - dt / IMMFALL)
    imminence = st['hot'] * tension

    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME (the native leak): build once.
    vals = (tension, rise, lowcut, density, imminence)
    for attempt in (0, 1):
        try:
            if not st['built']:
                scriptOp.clear()
                for n in ('tension', 'rise', 'lowcut', 'density', 'imminence'):
                    scriptOp.appendChan(n)
                scriptOp.numSamples = 1
                st['built'] = True
            for i, v in enumerate(vals):
                scriptOp[i][0] = v
            break
        except Exception:
            st['built'] = False
    return
'''
tension_src = C(textDAT, 'tension_src', 1780, 1360)
tension_src.text = hdr(
    CLOCKLEN=CLOCKLEN, FASTT=1.0, SLOWT=10.0, PEAKDECAY=0.9990, LOUD=0.28, DENSWIN=2.0,
    WRISE=0.42, WLOW=0.34, WDENS=0.30, GAMMA=0.70, ATTACK=0.85, RELEASE=3.0,
    AFTERDROP=5.0, IMMTHR=0.40, IMMRISE=4.0, IMMFALL=1.4,
) + TENSION_BODY
tension = C(scriptCHOP, 'tension', 1940, 1360)
tension.par.callbacks = tension_src.name
W(timer, tension, 0)
W(null_audio, tension, 1)
W(tempo, tension, 2)

# ---------------------------------------------------------------------------
# DIRECTOR — verbatim from homestead: musical time, the seekable playhead (the day
# of the year), envelopes and event counters.
# ---------------------------------------------------------------------------
# ---- BEGIN HOMESTEAD (verbatim) ----
DIRECTOR_BODY = '''# Musical time is monotonic and never seeks; the playhead is a subtraction from it
# (show = musical - Timeoffset), so a chapter jump is one parameter write.
#
# The playhead is CLAMPED at the end, not wrapped: the finished house stays on the
# bank until someone seeks back. And because `musical` is module state that resets
# on every reload while Timeoffset is a parameter that survives, the offset is
# re-derived from Showt on the first cook after a reload (see bayou) — otherwise the
# story freezes at the first frame for however long the stale offset is.
#
# Discrete events are MONOTONIC COUNTERS, never one-frame flags.
import math

_clock = {'last_raw': None, 'musical': 0.0, 'primed': False}
_st = {'peak': {'bass': PEAKFLOOR, 'high': PEAKFLOOR, 'energy': PEAKFLOOR},
       'kickenv': 0.0, 'dropenv': 0.0,
       'gust': 0, 'fish': 0, 'reseed': 0,
       'kicks': 0, 'accents': 0, 'drops': 0}


def _norm(st, key, v):
    pk = max(v, st['peak'][key] * PEAKDECAY, PEAKFLOOR)
    st['peak'][key] = pk
    return min(1.0, v / pk)


def chan(inp, name, default=0.0):
    if inp is None:
        return default
    try:
        return float(inp[name][0])
    except Exception:
        return default


def onCook(scriptOp):
    tmr = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    aud = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    mus = scriptOp.inputs[2] if len(scriptOp.inputs) > 2 else None
    comp = scriptOp.parent()
    par = comp.par
    st = _st

    raw = chan(tmr, 'cycles_plus_fraction', 0.0) * CLOCKLEN
    factor = chan(mus, 'factor', 1.0)
    if _clock['last_raw'] is None:
        _clock['last_raw'] = raw
    dt = max(0.0, raw - _clock['last_raw'])
    _clock['last_raw'] = raw
    _clock['musical'] += dt * factor
    musical = _clock['musical']

    bass = _norm(st, 'bass', chan(aud, 'bass', 0.0))
    high = _norm(st, 'high', chan(aud, 'high', 0.0))
    energy = _norm(st, 'energy', chan(aud, 'energy', 0.0))
    kick = chan(mus, 'beat', 0.0)
    beatstr = chan(mus, 'beatstr', 0.0)
    drop = chan(mus, 'drop', 0.0)

    if dt > 0.0:
        st['kickenv'] *= 0.5 ** (dt / 0.14)
        st['dropenv'] *= 0.5 ** (dt / 1.10)

    if kick > 0.5:
        st['kickenv'] = 1.0
        st['kicks'] += 1
        if beatstr >= ACCENT:
            st['accents'] += 1
    if drop > 0.5:
        st['dropenv'] = 1.0
        st['drops'] += 1

    if kick > 0.5 and float(par.Beatdrive.eval()) > 0.01:
        period = 60.0 / max(1.0, float(par.Refbpm.eval()))
        phase = _clock['musical'] % period
        err = phase if phase < period * 0.5 else phase - period
        _clock['musical'] -= err * BEATLOCK * float(par.Beatdrive.eval())
        musical = _clock['musical']

    slen = max(1.0, float(par.Storylen.eval()))
    off = float(par.Timeoffset.eval())
    if not _clock['primed']:
        _clock['primed'] = True
        try:
            was = min(slen, max(0.0, float(par.Showt.eval())))
        except Exception:
            was = 0.0
        off = musical - was
        par.Timeoffset = off
    elif musical - off < -0.5:
        try:
            was = min(slen, max(0.0, float(par.Showt.eval())))
        except Exception:
            was = 0.0
        off = musical - was
        par.Timeoffset = off
    # For an all-night run the story LOOPS: the finished homestead fades through
    # black into the empty riverbank again. With Loop off it clamps and holds.
    if par.Loop.eval():
        show = (musical - off) % slen
    else:
        show = min(slen, max(0.0, musical - off))

    pending = comp.fetch('pending', None)
    if pending:
        comp.store('pending', [])
        for what in pending:
            if what == 'gust':
                st['gust'] += 1
                st['dropenv'] = 1.0
            elif what == 'fish':
                st['fish'] += 1
            elif what == 'reseed':
                st['reseed'] += 1

    out = {
        'rawtime': raw, 'musical': musical, 'show': show, 'tempofactor': factor,
        'bass': bass, 'high': high, 'energy': energy,
        'kick': kick, 'kickenv': st['kickenv'], 'beatstr': beatstr,
        'drop': drop, 'dropenv': st['dropenv'],
        'kickcnt': float(st['kicks']), 'accentcnt': float(st['accents']),
        'dropcnt': float(st['drops']), 'gustcnt': float(st['gust']),
        'fishcnt': float(st['fish']), 'reseedcnt': float(st['reseed']),
        'storylen': slen,
    }

    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME. On 2025.33230 a Script
    # CHOP that does leaks native memory inside TouchDesigner — measured 2-5 MB a
    # minute on a 12k-sample publish, ~0.6 MB a minute even on a few 1-sample
    # channels. Build the channels once; after that only write values.
    # (numChans cannot be read from inside a cook, so whether they exist is
    # tracked here; if a write ever fails they are rebuilt and the write retried.)
    keys = sorted(out.keys())
    for attempt in (0, 1):
        try:
            if not st.get('built'):
                scriptOp.clear()
                for k in keys:
                    scriptOp.appendChan(k)
                scriptOp.numSamples = 1
                st['built'] = True
            for i, k in enumerate(keys):
                scriptOp[i][0] = out[k]
            break
        except Exception:
            st['built'] = False

    try:
        par.Bassm.val = bass
        par.Highm.val = high
        par.Energym.val = energy
        par.Showt.val = show
    except Exception:
        pass
    return
'''

dir_src = C(textDAT, 'director_src', 1780, 1120)
dir_src.text = hdr(CLOCKLEN=CLOCKLEN, PEAKDECAY=0.9988, PEAKFLOOR=0.05,
                   BEATLOCK=0.22, ACCENT=0.32) + DIRECTOR_BODY

director = C(scriptCHOP, 'director', 1940, 1120)
director.par.callbacks = dir_src.name
W(timer, director, 0)
W(null_audio, director, 1)
W(tempo, director, 2)
# ---- END HOMESTEAD ----


def D(ch):
    return "(op('director')['%s'] or 0)" % ch


def E(ch):
    return "(op('engine')['%s'] or 0)" % ch


# ---------------------------------------------------------------------------
# THE ENGINE — the day, the music's meaning, the camera, the readout. It moves no
# particles: the GPU does that. It publishes a handful of control channels.
# ---------------------------------------------------------------------------
ENGINE_BODY = r'''# The day of the year comes from the director's playhead. The music becomes three
# numbers the particle shader understands:
#   coh    how strongly the present is held in its data form (build-ups raise it;
#          a drop drops it, and it comes back over a few seconds)
#   burst  a short outward release (a drop, or the B pad)
#   flow   how hard the flow field pushes the present
# and the camera follows the present around the ring.
import math
import datetime

_S = {'S': None}
TAU = 2.0 * math.pi
OUTCH = ('day', 'coh', 'burst', 'flow', 'dt', 'clk', 'kick', 'tension', 'imm',
         'camx', 'camy', 'camz', 'tgx', 'tgy', 'tgz',
         'T', 'RH', 'P', 'W', 'PM', 'cloud', 'flash', 'seed', 'nowang')


def _chan(inp, name, default=0.0):
    try:
        return float(inp[name][0])
    except Exception:
        return default


def _delta(S, inp, name):
    try:
        v = float(inp[name][0])
    except Exception:
        return 0
    prev = S['last'].get(name)
    S['last'][name] = v
    if prev is None or v < prev:
        return 0
    return int(round(v - prev))


def _lerpday(day, k):
    n = len(NORM)
    i0 = int(math.floor(day)) % n
    i1 = (i0 + 1) % n
    f = day - math.floor(day)
    return NORM[i0][k] * (1.0 - f) + NORM[i1][k] * f


def _new():
    return {'last': {}, 'lastraw': None, 'clk': 0.0, 'release': 0.0, 'burst': 0.0,
            'flash': 0.0, 'coh': 0.5, 'camang': None, 'cam': None, 'seed': 0.0,
            'chap': -1, 'labt': -99.0, 'labtxt': '', 'datt': -99.0, 'built': False,
            'census': ''}


def onCook(scriptOp):
    d = scriptOp.inputs[0] if len(scriptOp.inputs) > 0 else None
    tn = scriptOp.inputs[1] if len(scriptOp.inputs) > 1 else None
    comp = scriptOp.parent()
    par = comp.par
    S = _S['S']
    if S is None:
        S = _S['S'] = _new()

    raw = _chan(d, 'rawtime')
    if S['lastraw'] is None:
        S['lastraw'] = raw
    dt = min(0.1, max(0.0, raw - S['lastraw']))
    S['lastraw'] = raw
    S['clk'] = (S['clk'] + dt) % 1000.0
    t = S['clk']
    show = _chan(d, 'show')
    slen = max(1.0, _chan(d, 'storylen', STORYDEF))
    day = (show / slen * NDAYS) % NDAYS
    energy, bass = _chan(d, 'energy'), _chan(d, 'bass')
    kickenv = _chan(d, 'kickenv')
    drops = _delta(S, d, 'dropcnt')
    tension = _chan(tn, 'tension')
    imm = _chan(tn, 'imminence')

    q = comp.fetch('qverbs', None)
    burst_now = bool(drops)
    if q:
        comp.store('qverbs', [])
        for v in q[:16]:
            if v == 'burst':
                burst_now = True
            elif v == 'reseed':
                S['seed'] = (S['seed'] + 17.31) % 997.0
    if burst_now:
        S['release'] = 1.0
        S['burst'] = 1.0
        S['flash'] = 1.0
    S['release'] *= 0.5 ** (dt / 2.2)
    S['burst'] *= 0.5 ** (dt / 0.18)
    S['flash'] *= 0.5 ** (dt / 0.45)

    gather = 1.0 if par.Gather.eval() else 0.0
    coh_t = min(1.0, 0.38 + 0.52 * tension + 0.2 * imm + gather) * (1.0 - 0.80 * S['release'])
    S['coh'] += (coh_t - S['coh']) * min(1.0, dt / 0.6)
    flow = float(par.Flow.eval()) * (0.45 + 0.9 * energy + 0.9 * S['release'])

    # the present day's weather, for the camera, the grade and the readout
    T, RH, P, Wd = (_lerpday(day, k) for k in (0, 1, 2, 3))
    cloud, PM = _lerpday(day, 6), _lerpday(day, 7)

    # the camera pans with the present: it sits a little ahead of it and looks back
    # across the ring, drifting up and down; a build-up draws it in, a drop pulls back
    ang = day / NDAYS * TAU
    if S['camang'] is None:
        S['camang'] = ang
    da = (ang - S['camang'] + math.pi) % TAU - math.pi
    S['camang'] += da * min(1.0, dt / 1.5)
    ca = S['camang'] + 0.55 + 0.18 * math.sin(t * 0.05)
    rad = 5.0 + 0.5 * math.sin(t * 0.071) - 0.9 * tension + 0.5 * S['release']
    cam = (math.cos(ca) * rad, 1.55 + 0.6 * math.sin(t * 0.043) + 0.25 * T, math.sin(ca) * rad)
    na = S['camang']
    tg = (math.cos(na) * RING * 0.30, -0.10 + 0.15 * (T - 0.5), math.sin(na) * RING * 0.30)
    if S['cam'] is None:
        S['cam'] = list(cam + tg)
    for i, v in enumerate(cam + tg):
        S['cam'][i] += (v - S['cam'][i]) * min(1.0, dt / 0.8)

    vals = {'day': day, 'coh': S['coh'], 'burst': S['burst'], 'flow': flow,
            'dt': dt if dt > 0 else 1.0 / 60.0, 'clk': t, 'kick': kickenv,
            'tension': tension, 'imm': imm,
            'camx': S['cam'][0], 'camy': S['cam'][1], 'camz': S['cam'][2],
            'tgx': S['cam'][3], 'tgy': S['cam'][4], 'tgz': S['cam'][5],
            'T': T, 'RH': RH, 'P': P, 'W': Wd, 'PM': PM, 'cloud': cloud,
            'flash': S['flash'], 'seed': S['seed'], 'nowang': -math.degrees(S['camang'])}
    # NEVER clear() AND RE-APPEND CHANNELS EVERY FRAME (the native leak): build once.
    for attempt in (0, 1):
        try:
            if not S['built']:
                scriptOp.clear()
                for n in OUTCH:
                    scriptOp.appendChan(n)
                scriptOp.numSamples = 1
                S['built'] = True
            for i, n in enumerate(OUTCH):
                scriptOp[i][0] = vals[n]
            break
        except Exception:
            S['built'] = False

    # the readout: the chapter on change, the day's data always (at most 4 Hz)
    di = int(day) % NDAYS
    chap = 0
    for i, c in enumerate(CHAPTERS):
        if di >= c[2] - 4:
            chap = i
    if chap != S['chap']:
        S['chap'] = chap
        S['labt'] = raw
        try:
            par.Scaletxt.val = CHAPTERS[chap][1]
        except Exception:
            pass
    if abs(raw - S['datt']) > 0.25:
        S['datt'] = raw
        dd = datetime.date(2024, 1, 1) + datetime.timedelta(days=di)
        r = DELHI_2024[di]
        txt = ('NEW DELHI   28.61 N  77.21 E\n%02d %s %d     %.1f C   %d%% RH   %s   PM2.5 %d'
               % (dd.day, MONTHS[dd.month - 1], dd.year, r[2], r[4],
                  ('%.1f mm' % r[3]) if r[3] > 0 else 'dry', int(round(r[8]))))
        if txt != S['labtxt']:
            S['labtxt'] = txt
            try:
                par.Datatxt.val = txt
            except Exception:
                pass
    try:
        par.Day.val = day
        par.Chapter.val = float(chap)
        par.Coh.val = S['coh']
        par.Tension.val = tension
        par.Labelfade.val = math.exp(-max(0.0, raw - S['labt']) / 5.0) if raw >= S['labt'] else 1.0
    except Exception:
        pass
    S['census'] = ('day %.1f %s | coh %.2f | tension %.2f | T %.2f P %.2f PM %.2f'
                   % (day, CHAPTERS[chap][0], S['coh'], tension, T, P, PM))
    return
'''

eng_src = C(textDAT, 'engine_src', 1780, 980)
eng_src.text = hdr(STORYDEF=STORYDEF, NDAYS=NDAYS, RING=RING, MONTHS=MONTHS,
                   CHAPTERS=CHAPTERS, NORM=NORM, DELHI_2024=DELHI_2024) + ENGINE_BODY
engine = C(scriptCHOP, 'engine', 1940, 980)
engine.par.callbacks = eng_src.name
W(director, engine, 0)
W(tension, engine, 1)

# ---------------------------------------------------------------------------
# THE DATA TEXTURE — 366 x 2, 32-bit float. Row 0: T, RH, P, W. Row 1: sin and cos
# of the wind direction, cloud, PM. Static: it cooks once.
# ---------------------------------------------------------------------------
DATA_BODY = '''# The year, as a texture the particle shader can read with texelFetch.
import numpy as np


def onCook(scriptOp):
    a = np.zeros((2, len(NORM), 4), dtype=np.float32)
    for i, n in enumerate(NORM):
        a[0, i] = n[0:4]
        a[1, i] = n[4:8]
    scriptOp.copyNumpyArray(a)
    return
'''
data_src = C(textDAT, 'data_src', 1300, 560)
data_src.text = hdr(NORM=NORM) + DATA_BODY
data_tex = C(scriptTOP, 'data_tex', 1440, 560)
data_tex.par.callbacks = data_src.name
menu_pick(data_tex.par.format, 'rgba32float')

# ---------------------------------------------------------------------------
# THE SIMULATION — a GLSL TOP, NP x NP particles, two float buffers fed back
# ---------------------------------------------------------------------------
SIM_GLSL = '''// Every pixel is a particle: buffer 0 is position (xyz) and life (w), buffer 1 is
// velocity (xyz) and how much of the present it is (w). Each particle belongs to one
// day (its index mod 366); its HOME is that day's place in the ring, shaped by that
// day's data. The present melts and is driven by its day's weather; the rest of the
// year holds its shape.
uniform vec4 uA;   // x dt, y clock, z day, w coherence
uniform vec4 uB;   // x kick, y burst, z tension, w flow
uniform vec4 uC;   // x focus width (days), y seed, z ring radius, w N
layout(location = 0) out vec4 oPos;
layout(location = 1) out vec4 oVel;

#define NDAYS 366.0
#define TAU 6.2831853

float hash11(float n) { return fract(sin(n * 127.1) * 43758.5453); }
vec3 hash31(float n) { return fract(sin(vec3(n * 127.1, n * 311.7, n * 74.7)) * 43758.5453); }

// simplex noise (Ashima Arts / Stefan Gustavson, MIT)
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v) {
    const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(i.z + vec4(0.0, i1.z, i2.z, 1.0))
             + i.y + vec4(0.0, i1.y, i2.y, 1.0)) + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}

// curl of three offset noise potentials: divergence-free, the smoke drift
vec3 curl(vec3 p) {
    const float e = 0.08;
    vec3 dx = vec3(e, 0.0, 0.0), dy = vec3(0.0, e, 0.0), dz = vec3(0.0, 0.0, e);
    vec3 o1 = vec3(31.4, 7.7, 19.1), o2 = vec3(-11.3, 43.2, 5.9);
    float a_y = snoise(p + dy) - snoise(p - dy);
    float a_z = snoise(p + dz) - snoise(p - dz);
    float b_x = snoise(p + o1 + dx) - snoise(p + o1 - dx);
    float b_z = snoise(p + o1 + dz) - snoise(p + o1 - dz);
    float c_x = snoise(p + o2 + dx) - snoise(p + o2 - dx);
    float c_y = snoise(p + o2 + dy) - snoise(p + o2 - dy);
    return vec3(c_y - b_z, a_z - c_x, b_x - a_y) / (2.0 * e);
}

vec4 dataRow(float day, int row) {
    return texelFetch(sTD2DInputs[2], ivec2(int(mod(day, NDAYS)), row), 0);
}

vec3 dayCentre(float day, vec4 d0) {
    float th = day / NDAYS * TAU;
    float r = uC.z + 0.55 * (d0.x - 0.5);          // hot days bulge outward
    float y = 0.60 * (d0.y - 0.5);                  // wet days rise
    return vec3(cos(th) * r, y, sin(th) * r);
}

vec3 homeOf(float id, float day, vec4 d0, vec4 d1) {
    vec3 c = dayCentre(day, d0);
    float th = day / NDAYS * TAU;
    vec3 radial = vec3(cos(th), 0.0, sin(th));
    vec3 tang = vec3(-sin(th), 0.0, cos(th));
    vec3 h = hash31(id * 1.37 + uC.y);
    float rt = 0.07 + 0.15 * d0.y + 0.32 * d0.z;    // the tube: humidity and rain
    float a = h.x * TAU;
    float rr = sqrt(h.y) * rt;
    vec3 p = c + radial * cos(a) * rr + vec3(0.0, 1.0, 0.0) * sin(a) * rr
             + tang * (h.z - 0.5) * (TAU * uC.z / NDAYS) * 1.3;
    // smog: a share of the day's particles hang in a wide diffuse haze
    if (hash11(id * 2.91 + uC.y) < 0.35 * d1.w) {
        p += (hash31(id * 3.3 + 1.0) - 0.5) * vec3(0.8, 0.55, 0.8) * (0.4 + d1.w);
    }
    return p;
}

void main() {
    ivec2 px = ivec2(gl_FragCoord.xy);
    float id = float(px.x) + float(px.y) * uC.w;
    vec4 pos = texelFetch(sTD2DInputs[0], px, 0);
    vec4 vel = texelFetch(sTD2DInputs[1], px, 0);
    float dt = clamp(uA.x, 0.0, 0.05);
    float t = uA.y;
    float day = mod(id, NDAYS);
    vec4 d0 = dataRow(day, 0);                      // T, RH, P, W
    vec4 d1 = dataRow(day, 1);                      // sin wind, cos wind, cloud, PM
    float T = d0.x, RH = d0.y, P = d0.z, Wd = d0.w, PM = d1.w;
    vec3 home = homeOf(id, day, d0, d1);

    // how much of the present this particle is: distance in days, round the year
    float dd = abs(mod(day - uA.z + NDAYS * 0.5, NDAYS) - NDAYS * 0.5);
    float f = exp(-(dd * dd) / (uC.x * uC.x));
    float f2 = exp(-(dd * dd) / (4.0 * uC.x * uC.x));
    vec3 cNow = dayCentre(uA.z, dataRow(uA.z, 0));

    vec3 p = pos.xyz;
    vec3 v = vel.xyz;
    float life = pos.w;
    if (life <= 0.0 || length(p) > 9.0) {
        p = home + (hash31(id + t) - 0.5) * 0.04;
        v = vec3(0.0);
        life = 0.6 + 0.4 * hash11(id * 7.1 + floor(t));
    }

    // held in the data form: the far year firmly, the present as the music allows
    float coh = mix(1.0, uA.w, f);
    v += (home - p) * mix(0.25, 4.5, coh) * dt;

    // the flow: windy and hot days are turbulent
    vec3 cn = curl(p * 0.48 + vec3(0.0, t * 0.05, t * 0.035) + uC.y);
    v += cn * uB.w * (0.35 + 1.3 * Wd + 0.7 * T) * (f + 0.12) * dt * 1.25;
    // the whole year drifts a little along itself, so the sculpture is never still
    v += normalize(vec3(-home.z, 0.0, home.x) + 1e-5) * 0.05 * dt * (1.0 + uB.w);
    // heat rises, cold sinks; the kick is a heat pulse
    v.y += (T - 0.45) * 1.8 * f * dt * (1.0 + 2.5 * uB.x);
    // rain falls, and the kick is thunder under it
    v.y -= P * 4.0 * f * dt * (1.0 + 1.2 * uB.x);
    // the wind blows from where it came
    v.xz += -vec2(d1.x, d1.y) * Wd * 1.8 * f * dt;
    // the cold shivers on the kick
    v += curl(p * 3.0 + t * 0.7) * (1.0 - T) * uB.x * f * 0.9 * dt;
    // the kick pushes out from the present
    vec3 away = p - cNow;
    float al = length(away);
    vec3 dir = al > 1e-4 ? away / al : vec3(0.0, 1.0, 0.0);
    v += dir * uB.x * f * dt * (0.3 + 0.8 * T);
    // a build-up swirls the present around itself
    v += cross(vec3(0.0, 1.0, 0.0), away) * uB.z * f * dt * 2.2;
    // a drop: the release
    v += (dir * 2.2 + cn * 1.2) * uB.y * f2 * dt * 4.0;
    // a soft leash: nothing drifts more than a couple of units from home
    vec3 off_ = p - home;
    float far_ = length(off_.xz);
    v.xz -= off_.xz * smoothstep(1.0, 2.2, far_) * 3.0 * dt;
    v.y -= off_.y * smoothstep(1.4, 2.6, abs(off_.y)) * 2.0 * dt * (1.0 - step(0.05, P));
    // viscosity: the cold is thick, the rest of the year settles
    v *= exp(-dt * (1.5 + 2.4 * (1.0 - T) * f + 1.2 * (1.0 - f) + 0.8 * PM * f));

    p += v * dt;
    life -= dt * (0.035 + 0.05 * hash11(id * 3.7));
    // rain circulates: what has fallen well below its cloud is reborn inside it
    if (P > 0.05 && p.y < home.y - 0.9 - 0.8 * P) {
        p = home + vec3(0.0, 0.15 * P, 0.0) + (hash31(id + t * 3.0) - 0.5) * 0.06;
        v = vec3(0.0, -0.2, 0.0);
    }

    oPos = vec4(p, life);
    oVel = vec4(v, f);
}
'''
sim_init = C(constantTOP, 'sim_init', 1300, 800)
res(sim_init, NP, NP, 'rgba32float')
soft(sim_init, colorr=0.0, colorg=0.0, colorb=0.0, alpha=0.0)
pos_fb = C(feedbackTOP, 'pos_fb', 1440, 860)
res(pos_fb, NP, NP, 'rgba32float')
W(sim_init, pos_fb)
vel_fb = C(feedbackTOP, 'vel_fb', 1440, 760)
res(vel_fb, NP, NP, 'rgba32float')
W(sim_init, vel_fb)
sim_pix = C(textDAT, 'sim_pixel', 1600, 900)
sim_pix.text = SIM_GLSL
sim = C(glslTOP, 'sim', 1600, 800)
res(sim, NP, NP, 'rgba32float')
sim.par.pixeldat = sim_pix.name
sim.par.numcolorbufs = 2
soft(sim, inputfiltertype='nearest')
W(pos_fb, sim, 0)
W(vel_fb, sim, 1)
W(data_tex, sim, 2)
sim.par.vec = 3
sim.par.vec0name = 'uA'
sim.par.vec0valuex.expr = E('dt')
sim.par.vec0valuey.expr = E('clk')
sim.par.vec0valuez.expr = E('day')
sim.par.vec0valuew.expr = E('coh')
sim.par.vec1name = 'uB'
sim.par.vec1valuex.expr = E('kick')
sim.par.vec1valuey.expr = E('burst')
sim.par.vec1valuez.expr = E('tension')
sim.par.vec1valuew.expr = E('flow')
sim.par.vec2name = 'uC'
sim.par.vec2valuex.expr = 'parent().par.Focus'
sim.par.vec2valuey.expr = E('seed')
sim.par.vec2valuez = RING
sim.par.vec2valuew = NP
pos_out = C(renderselectTOP, 'pos_out', 1760, 860)
pos_out.par.top = sim.name
pos_out.par.bufferindex = 0
vel_out = C(renderselectTOP, 'vel_out', 1760, 760)
vel_out.par.top = sim.name
vel_out.par.bufferindex = 1
pos_fb.par.top = pos_out.name
vel_fb.par.top = vel_out.name

# ---------------------------------------------------------------------------
# THE RENDER — soft billboards, instanced straight from the position texture
# ---------------------------------------------------------------------------
PVERT = '''// One quad per particle, instanced from the position texture (translate = rgb). The
// quad faces the camera and stretches along the particle's velocity, so fast
// particles streak like wet pigment. Size, colour and brightness come from the
// particle's own day of data, and from how much of the present it is.
uniform vec4 uS;   // x size, y brightness, z N, w exposure unused
uniform sampler2D sVel;
uniform sampler2D sPos;
uniform sampler2D sData;
out vec2 vQuad;
out vec4 vCol;

vec3 tempRamp(float t) {
    vec3 c0 = vec3(0.10, 0.16, 0.70);
    vec3 c1 = vec3(0.08, 0.58, 0.86);
    vec3 c2 = vec3(1.00, 0.74, 0.30);
    vec3 c3 = vec3(1.00, 0.38, 0.10);
    vec3 c4 = vec3(0.86, 0.08, 0.28);
    if (t < 0.30) return mix(c0, c1, t / 0.30);
    if (t < 0.55) return mix(c1, c2, (t - 0.30) / 0.25);
    if (t < 0.78) return mix(c2, c3, (t - 0.55) / 0.23);
    return mix(c3, c4, (t - 0.78) / 0.22);
}

void main() {
    int id = TDInstanceID();
    int N = int(uS.z);
    ivec2 c = ivec2(id % N, id / N);
    vec4 vel = texelFetch(sVel, c, 0);
    vec4 pos = texelFetch(sPos, c, 0);
    int day = id % 366;
    vec4 d0 = texelFetch(sData, ivec2(day, 0), 0);
    vec4 d1 = texelFetch(sData, ivec2(day, 1), 0);
    float T = d0.x, RH = d0.y, Pr = d0.z, PM = d1.w;   // not P: that is the vertex
    float f = vel.w;
    float life = clamp(pos.w, 0.0, 1.0);
    float lshape = sqrt(max(0.0, sin(3.14159 * life)));

    float size = uS.x * (0.55 + 0.8 * RH + 0.9 * PM) * (0.75 + 0.7 * f) * lshape;
    vec4 wc = TDDeform(vec3(0.0));
    mat4 camM = uTDMats[TDCameraIndex()].cam;
    vec4 cc = camM * wc;
    vec2 vd = (camM * vec4(vel.xyz, 0.0)).xy;
    float sp = length(vd);
    vec2 ax = sp > 1e-4 ? vd / sp : vec2(1.0, 0.0);
    vec2 ay = vec2(-ax.y, ax.x);
    cc.xy += ax * P.x * size * (1.0 + min(sp, 3.0) * 0.22) + ay * P.y * size;
    gl_Position = uTDMats[TDCameraIndex()].proj * cc;
    vQuad = P.xy * 2.0;

    vec3 col = tempRamp(T);
    vec3 rainCol = mix(vec3(0.10, 0.82, 0.58), vec3(0.28, 0.46, 1.00), Pr);
    // the monsoon is humid AND warm: January is humid too, but cold, and stays blue
    col = mix(col, rainCol, clamp(Pr * 1.3 + (RH - 0.58) * 1.6 * smoothstep(0.45, 0.62, T), 0.0, 0.85));
    col = mix(col, vec3(0.62, 0.52, 0.42), PM * 0.55);
    float b = uS.y * (0.62 + 0.95 * f + 0.25 * min(sp, 2.0)) * (0.8 + 0.4 * RH);
    vCol = vec4(col * b, 0.14 * lshape);
}
'''
PFRAG = '''in vec2 vQuad;
in vec4 vCol;
out vec4 fragColor;

void main() {
    float r2 = dot(vQuad, vQuad);
    if (r2 > 1.0) discard;
    float a = exp(-r2 * 3.2) * (1.0 - r2) * vCol.a;
    fragColor = TDOutputSwizzle(vec4(vCol.rgb * a, a));
}
'''
quad = C(rectangleSOP, 'quad', 1600, 420)
soft(quad, sizex=1.0, sizey=1.0)
pvert = C(textDAT, 'particle_vert', 1760, 500)
pvert.text = PVERT
pfrag = C(textDAT, 'particle_frag', 1760, 440)
pfrag.text = PFRAG
pmat = C(glslMAT, 'particle_mat', 1760, 380)
pmat.par.vdat = pvert.name
pmat.par.pdat = pfrag.name
pmat.par.vec0name = 'uS'
pmat.par.vec0valuex.expr = 'parent().par.Psize'
pmat.par.vec0valuey.expr = 'parent().par.Pbright'
pmat.par.vec0valuez = NP
pmat.par.vec0valuew = 1.0
pmat.par.sampler = 3
for _i, (_n, _t) in enumerate((('sVel', vel_out), ('sPos', pos_out), ('sData', data_tex))):
    setattr(pmat.par, 'sampler%dname' % _i, _n)
    setattr(pmat.par, 'sampler%dtop' % _i, _t.name)
    menu_pick(getattr(pmat.par, 'sampler%dfilter' % _i), 'nearest')
pmat.par.blending = True
menu_pick(pmat.par.srcblend, 'one')
menu_pick(pmat.par.destblend, 'one')
pmat.par.depthwriting = False
soft(pmat, depthtest=False)

g_parts = C(geometryCOMP, 'geo_particles', 1920, 420)
for _stale in list(g_parts.children):
    _stale.destroy()
_sel = g_parts.create(selectSOP, 'shape')
_sel.par.sop = '../' + quad.name
_sel.render = True
_sel.display = True
g_parts.par.material = pmat.name
g_parts.par.instancing = True
g_parts.par.instanceop = pos_out.name
soft(g_parts, instancetx='r', instancety='g', instancetz='b')

# --- the sculpture's scale: month ticks round the year, and a marker for today ---
TICKS_BODY = '''# Twelve month ticks under the ring and a faint circle: the data sculpture's scale.
# Static: it cooks once.
import math


def onCook(scriptOp):
    scriptOp.clear()
    d0 = 0
    for m, ln in enumerate(MLEN):
        th = d0 / NDAYS * 2.0 * math.pi
        for r0, r1 in ((RING - 0.55, RING - 0.40), (RING + 0.40, RING + 0.62)):
            a = scriptOp.appendPoint(); a.x, a.y, a.z = math.cos(th) * r0, -0.55, math.sin(th) * r0
            b = scriptOp.appendPoint(); b.x, b.y, b.z = math.cos(th) * r1, -0.55, math.sin(th) * r1
            pl = scriptOp.appendPoly(2, closed=False, addPoints=False)
            pl[0].point, pl[1].point = a, b
        d0 += ln
    n = 180
    pts = []
    for k in range(n):
        th = k / n * 2.0 * math.pi
        p = scriptOp.appendPoint(); p.x, p.y, p.z = math.cos(th) * RING, -0.55, math.sin(th) * RING
        pts.append(p)
    for k in range(0, n, 2):
        pl = scriptOp.appendPoly(2, closed=False, addPoints=False)
        pl[0].point, pl[1].point = pts[k], pts[(k + 1) % n]
    return
'''
ticks_src = C(textDAT, 'ticks_src', 1600, 300)
ticks_src.text = hdr(MLEN=MLEN, NDAYS=NDAYS, RING=RING) + TICKS_BODY
ticks = C(scriptSOP, 'ticks', 1760, 300)
ticks.par.callbacks = ticks_src.name
now_line = C(lineSOP, 'now_line', 1760, 240)
soft(now_line, pax=RING - 0.62, pay=-0.55, paz=0.0, pbx=RING + 0.62, pby=-0.55, pbz=0.0)
mat_scale = C(constantMAT, 'mat_scale', 1920, 240)
soft(mat_scale, colorr=0.55, colorg=0.62, colorb=0.72, alpha=0.30, blending=True,
     depthtest=False, depthwriting=False)
g_ticks = C(geometryCOMP, 'geo_scale', 1920, 300)
for _stale in list(g_ticks.children):
    _stale.destroy()
_s2 = g_ticks.create(selectSOP, 'shape')
_s2.par.sop = '../' + ticks.name
_s2.render = True
_s2.display = True
g_ticks.par.material = mat_scale.name
g_now = C(geometryCOMP, 'geo_now', 1920, 180)
for _stale in list(g_now.children):
    _stale.destroy()
_s3 = g_now.create(selectSOP, 'shape')
_s3.par.sop = '../' + now_line.name
_s3.render = True
_s3.display = True
g_now.par.material = mat_scale.name
g_now.par.ry.expr = E('nowang')

look = C(nullCOMP, 'cam_target', 1760, 100)
look.par.tx.expr = E('tgx')
look.par.ty.expr = E('tgy')
look.par.tz.expr = E('tgz')
cam = C(cameraCOMP, 'cam', 1920, 100)
cam.par.tx.expr = E('camx')
cam.par.ty.expr = E('camy')
cam.par.tz.expr = E('camz')
soft(cam, fov=42.0, near=0.05, far=50.0)
cam.par.lookat = look.name

render = C(renderTOP, 'render_particles', 2100, 420)
res(render)
render.par.camera = cam.name
render.par.geometry = '%s %s %s' % (g_parts.name, g_ticks.name, g_now.name)
render.par.bgcolora = 0.0
menu_pick(render.par.antialias, 'aa1', 'aa2')

# --- silk: the mass leaves fading trails -------------------------------------------
trail_fb = C(feedbackTOP, 'trail_fb', 2100, 540)
res(trail_fb)
W(render, trail_fb)
trail = C(glslTOP, 'trail', 2260, 420)
res(trail)
trail_pix = C(textDAT, 'trail_pixel', 2260, 500)
trail_pix.text = '''// Silk. The previous frame decays under the new one (max, so it can never wash out).
uniform vec4 uT;   // x decay
out vec4 fragColor;
void main() {
    vec4 cur = texture(sTD2DInputs[0], vUV.st);
    vec4 fb = texture(sTD2DInputs[1], vUV.st);
    fragColor = TDOutputSwizzle(max(cur, fb * uT.x));
}
'''
trail.par.pixeldat = trail_pix.name
W(render, trail, 0)
W(trail_fb, trail, 1)
trail.par.vec = 1
trail.par.vec0name = 'uT'
trail.par.vec0valuex.expr = ("min(0.90, parent().par.Trails * (0.58 + 0.15 * %s + 0.12 * %s))"
                             % (E('RH'), E('tension')))
trail_fb.par.top = trail.name

# --- the grade: the weather's air, filmic tonemap, smog veil, heat shimmer ---------
grade = C(glslTOP, 'grade', 2420, 420)
res(grade)
grade_pix = C(textDAT, 'grade_pixel', 2420, 500)
grade_pix.text = '''// The air the sculpture sits in, and the finish. The background is a dark sky of the
// present day's weather (winter blue-grey, summer dusk, monsoon teal, smog brown).
// The heat shimmers the image; the smog veils it (lifted blacks, lower contrast, a
// warm grey); a filmic curve rolls the particle mass's highlights off softly.
uniform vec4 uW;   // x T, y RH, z P, w PM
uniform vec4 uX;   // x exposure, y haze, z vignette, w clock
uniform vec4 uY;   // x flash, y kick, z cloud, w tension
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
vec3 aces(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

void main() {
    vec2 uv = vUV.st;
    float T = uW.x, RH = uW.y, P = uW.z, PM = uW.w;
    // heat shimmer: a small rising ripple, only when it is hot
    float sh = smoothstep(0.62, 0.95, T) * 0.0022;
    uv += vec2(sin(uv.y * 90.0 + uX.w * 6.0) * sh, sin(uv.x * 70.0 - uX.w * 4.0) * sh * 0.5);
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    // the sky
    vec3 cold = vec3(0.020, 0.030, 0.055), warm = vec3(0.060, 0.028, 0.020);
    vec3 wet = vec3(0.012, 0.045, 0.050), smog = vec3(0.060, 0.050, 0.040);
    vec3 sky = mix(cold, warm, smoothstep(0.35, 0.9, T));
    sky = mix(sky, wet, clamp(P * 1.3 + (RH - 0.65), 0.0, 0.8));
    sky = mix(sky, smog, PM * 0.7);
    sky *= (1.0 - 0.45 * uv.y) * (0.8 + 0.4 * (1.0 - uY.z));
    vec3 col = sky + c * uX.x * (1.0 + 0.25 * uY.x);
    col = aces(col * 1.15);
    // the veil: smog (and winter fog) lift the blacks and flatten the image
    float veil = uX.y * (0.16 * PM + 0.10 * RH * (1.0 - T));
    col = mix(col, vec3(0.34, 0.31, 0.28) * (0.7 + 0.3 * PM), veil);
    vec2 d = (vUV.st - 0.5) * vec2(1.7778, 1.0);
    col *= 1.0 - uX.z * 0.55 * dot(d, d);
    col += (hash(vUV.st * vec2(1920.0, 1080.0) + fract(uX.w)) - 0.5) * 0.008;
    fragColor = TDOutputSwizzle(vec4(max(col, vec3(0.0)), 1.0));
}
'''
grade.par.pixeldat = grade_pix.name
W(trail, grade)
grade.par.vec = 3
grade.par.vec0name = 'uW'
grade.par.vec0valuex.expr = E('T')
grade.par.vec0valuey.expr = E('RH')
grade.par.vec0valuez.expr = E('P')
grade.par.vec0valuew.expr = E('PM')
grade.par.vec1name = 'uX'
grade.par.vec1valuex.expr = 'parent().par.Exposure'
grade.par.vec1valuey.expr = 'parent().par.Haze'
grade.par.vec1valuez.expr = 'parent().par.Vignette'
grade.par.vec1valuew.expr = E('clk')
grade.par.vec2name = 'uY'
grade.par.vec2valuex.expr = E('flash')
grade.par.vec2valuey.expr = E('kick')
grade.par.vec2valuez.expr = E('cloud')
grade.par.vec2valuew.expr = E('tension')

glow_cut = C(levelTOP, 'glow_cut', 2420, 580)
soft(glow_cut, blacklevel=0.30, gamma1=1.3)
W(grade, glow_cut)
glow_blur = C(blurTOP, 'glow_blur', 2580, 580, size=16.0)
res(glow_blur, OUTW // 2, OUTH // 2)
W(glow_cut, glow_blur)
glow_lvl = C(levelTOP, 'glow_lvl', 2740, 580)
glow_lvl.par.opacity.expr = ("0.55 * parent().par.Glow * (0.6 + 0.4 * %s + 0.5 * %s)"
                             % (E('flash'), E('tension')))
W(glow_blur, glow_lvl)
comp_glow = C(compositeTOP, 'comp_glow', 2580, 420, operand='screen')
res(comp_glow)
W(grade, comp_glow, 0)
W(glow_lvl, comp_glow, 1)

# --- the readout: the day's data, always; the chapter, when it turns -----------------
data_lbl = C(textTOP, 'data_label', 2420, 700)
res(data_lbl, OUTW, OUTH, 'rgba8fixed')
soft(data_lbl, alignx='left', aligny='bottom', fontsizex=15, font='Courier New',
     bgalpha=0.0, fontcolorr=0.78, fontcolorg=0.80, fontcolorb=0.82, fontcolora=1.0,
     wordwrap=False, trackingx=0.25, positionx=0.035, positiony=0.05,
     positionunit='fraction')
data_lbl.par.text.expr = 'parent().par.Datatxt.eval()'
data_lvl = C(levelTOP, 'data_lvl', 2580, 700)
data_lvl.par.opacity.expr = 'parent().par.Label * 0.55'
W(data_lbl, data_lvl)
chap_lbl = C(textTOP, 'chapter_label', 2420, 780)
res(chap_lbl, OUTW, OUTH, 'rgba8fixed')
soft(chap_lbl, alignx='right', aligny='top', fontsizex=18, font='Courier New',
     bgalpha=0.0, fontcolorr=0.9, fontcolorg=0.9, fontcolorb=0.92, fontcolora=1.0,
     wordwrap=False, trackingx=0.35, positionx=-0.035, positiony=-0.06,
     positionunit='fraction')
chap_lbl.par.text.expr = 'parent().par.Scaletxt.eval()'
chap_lvl = C(levelTOP, 'chapter_lvl', 2580, 780)
chap_lvl.par.opacity.expr = 'parent().par.Label * (0.15 + 0.85 * parent().par.Labelfade)'
W(chap_lbl, chap_lvl)
comp_lbl = C(compositeTOP, 'comp_labels', 2740, 740, operand='over')
res(comp_lbl, OUTW, OUTH, 'rgba8fixed')
W(data_lvl, comp_lbl, 0)
W(chap_lvl, comp_lbl, 1)
comp_final = C(compositeTOP, 'comp_final', 2900, 420, operand='over')
res(comp_final)
W(comp_lbl, comp_final, 0)
W(comp_glow, comp_final, 1)

final_out = C(nullTOP, 'final_out', 3060, 420)
W(comp_final, final_out)
out1 = C(outTOP, 'out1', 3220, 420)
W(final_out, out1)

pout = proj.create(outTOP, SCENE + '_out')
pout.nodeX, pout.nodeY = 400, -6200
s.outputConnectors[0].connect(pout.inputConnectors[0])


# ---------------------------------------------------------------------------
# PADS AND KEYS
# ---------------------------------------------------------------------------
PEXEC_BODY = '''# A chapter is a SEEK to a day (see bayou): show = musical clock - Timeoffset, so a
# jump is one parameter write and the year plays on from there.


def _seek(comp, seconds):
    d = comp.op('director')
    mus = float(d['musical'][0]) if d is not None and d.numChans else 0.0
    comp.par.Timeoffset = mus - max(0.02, seconds)


def _push(comp, what):
    q = comp.fetch('qverbs', None)
    if not isinstance(q, list):
        q = []
    q.append(what)
    del q[:-16]
    comp.store('qverbs', q)


def onPulse(par):
    comp = par.owner
    n = par.name
    slen = max(1.0, float(comp.par.Storylen.eval()))
    names = [c[0] for c in CHAPTERS]
    if n == 'Burst':
        _push(comp, 'burst')
    elif n == 'Reseed':
        _push(comp, 'reseed')
    elif n == 'Restart':
        _seek(comp, 0.0)
    elif n.startswith('Go'):
        want = n[2:].lower()
        if want in names:
            _seek(comp, CHAPTERS[names.index(want)][2] / float(NDAYS) * slen)
    return
'''
pexec = C(parameterexecuteDAT, 'pad_exec', 2100, 1000)
pexec.text = hdr(CHAPTERS=CHAPTERS, NDAYS=NDAYS) + PEXEC_BODY
pexec.par.op = '..'
soft(pexec, pars='Burst Reseed Restart ' + ' '.join('Go' + c[0] for c in CHAPTERS),
     valuechange=False, onpulse=True)

KEY_BODY = '''# 1-6 jump to a chapter of the year; 0 to 1 January.
#   b  BURST   a release, now
#   g  GATHER  hold the year in its data form (toggle)
#   n  RESEED  a new flow field


def onKey(dat, keyInfo):
    if not keyInfo.state:
        return
    comp = dat.parent()
    k = keyInfo.key
    if k in '123456':
        i = int(k) - 1
        if i < len(CHAPTERS):
            getattr(comp.par, 'Go' + CHAPTERS[i][0]).pulse()
    elif k == '0':
        comp.par.Restart.pulse()
    elif k == 'b':
        comp.par.Burst.pulse()
    elif k == 'g':
        comp.par.Gather = not comp.par.Gather.eval()
    elif k == 'n':
        comp.par.Reseed.pulse()
    return


def onShortcut(dat, shortcutName, time):
    return
'''
keyin = C(keyboardinDAT, 'key_pad', 1780, 700)
keyin.par.keys = '1 2 3 4 5 6 0 b g n'
kcb = keyin.par.callbacks.eval()
if kcb is None:
    kcb = C(textDAT, 'key_pad_callbacks', 1780, 620)
    keyin.par.callbacks = kcb.name
kcb.nodeX, kcb.nodeY = 1780, 620
kcb.text = hdr(CHAPTERS=CHAPTERS) + KEY_BODY

# NO executeDAT KEEP-ALIVE (see bayou): pull-based.
s.par.display = True
s.par.opviewer = final_out.name
s.par.top = final_out.name
s.store('pending', [])
s.store('qverbs', [])

timer.par.initialize.pulse()
timer.par.start.pulse()
director.cook(force=True)
engine.cook(force=True)
pos_fb.par.resetpulse.pulse()
vel_fb.par.resetpulse.pulse()

for _got, _want, _what in (
        (g_parts.par.instanceop.eval(), pos_out, 'instance source'),
        (sim.par.numcolorbufs.eval(), 2, 'sim colour buffers'),
        (comp_glow.par.operand.eval(), 'screen', 'glow composite operand')):
    if _got != _want:
        print('  [CHECK FAILED] %s is %r, expected %r' % (_what, _got, _want))

print('built %s' % s.path)
print('  %s' % eng_src.module._S['S']['census'])
