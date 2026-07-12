# Idempotent builder for /project1/audio_feedback.
# Run via the MCP `run` tool (or paste into a TD Text DAT and execute).
# Destroys and recreates its own container + the project-level Out TOP it wires to;
# touches nothing else in the project. Re-running always yields the same network.

p = op('/project1')
old = p.op('audio_feedback')
if old: old.destroy()

scene = p.create(containerCOMP, 'audio_feedback')
scene.nodeX, scene.nodeY = 300, 400


def C(parent, type_, name, x, y, **params):
    o = parent.op(name)
    if o: o.destroy()
    o = parent.create(type_, name)
    o.nodeX = x
    o.nodeY = y
    for k, v in params.items():
        setattr(o.par, k, v)
    return o


def W(src, dst, idx=0):
    src.outputConnectors[0].connect(dst.inputConnectors[idx])


s = scene

# --- Audio source ---
afile = C(s, audiofileinCHOP, 'audio_in', 100, 700)

# bass chain (canonical two-band chain, see .claude/skills/touchdesigner-building/patterns.md)
af_lo = C(s, audiofilterCHOP, 'af_lo', 300, 750, filter='lowpass', units='frequency', cutofffrequency=700)
W(afile, af_lo)
env_lo = C(s, envelopeCHOP, 'env_lo', 500, 750, width=.15)
W(af_lo, env_lo)
rs_lo = C(s, resampleCHOP, 'rs_lo', 700, 750, rate=60)
W(env_lo, rs_lo)
math_lo = C(s, mathCHOP, 'math_lo', 900, 750)
math_lo.par.torange2 = 0.7
W(rs_lo, math_lo)
filt_lo = C(s, filterCHOP, 'filt_lo', 1100, 750, width=0.1)
W(math_lo, filt_lo)
null_bass = C(s, nullCHOP, 'null_bass', 1300, 750)
W(filt_lo, null_bass)

# highs chain
af_hi = C(s, audiofilterCHOP, 'af_hi', 300, 650, filter='highpass', units='frequency', cutofffrequency=3000)
W(afile, af_hi)
env_hi = C(s, envelopeCHOP, 'env_hi', 500, 650, width=.15)
W(af_hi, env_hi)
rs_hi = C(s, resampleCHOP, 'rs_hi', 700, 650, rate=60)
W(env_hi, rs_hi)
math_hi = C(s, mathCHOP, 'math_hi', 900, 650)
math_hi.par.fromrange2 = 0.5
math_hi.par.torange1 = 0.2
math_hi.par.torange2 = 1.0
W(rs_hi, math_hi)
filt_hi = C(s, filterCHOP, 'filt_hi', 1100, 650, width=0.5)
W(math_hi, filt_hi)
null_highs = C(s, nullCHOP, 'null_highs', 1300, 650)
W(filt_hi, null_highs)

# spectrum stamp: fresh content added into the feedback loop each frame
spec = C(s, audiospectrumCHOP, 'spectrum1', 300, 550)
W(afile, spec)
spec_top = C(s, choptoTOP, 'spectrum_top', 500, 550, chop=spec.path, layout='square',
             dataformat='r',
             outputresolution='custom', resolutionw=640, resolutionh=360, resmult=False)
spec_blur = C(s, blurTOP, 'spectrum_blur', 700, 550, size=4)
W(spec_top, spec_blur)
spec_stamp = C(s, levelTOP, 'spectrum_stamp', 900, 550, brightness1=4)
# raw spectrum magnitudes are tiny (~1e-3); brightness1 boosts to visible range.
# Keep this modest -- in an ADD-composited loop, too much gain per stamp blows the
# whole loop to white in well under a second (verified: brightness1=30 saturated it).
spec_stamp.par.opacity.expr = "0.15 + 0.35*op('%s')['chan1']" % null_bass.path
W(spec_blur, spec_stamp)

# --- Visual feedback chain ---
noise_seed = C(s, noiseTOP, 'noise_seed', 100, 200, type='simplex3d', mono=True, amp=0.3, offset=0.05,
               outputresolution='custom', resolutionw=640, resolutionh=360, resmult=False,
               format='rgba16float')

fb = C(s, feedbackTOP, 'fb_loop', 300, 200,
       outputresolution='custom', resolutionw=640, resolutionh=360, resmult=False,
       format='rgba16float')
W(noise_seed, fb)
# Periodic self-reseed: a sustained scale>1 zoom feedback loop zooms into an
# ever-shrinking, never-refreshed center point and collapses to a black hole
# there (verified). Reseeding every 14s keeps it a cycling tunnel instead.
fb.par.reset.expr = "absTime.seconds % 14 < 0.1"

fb_zoom = C(s, transformTOP, 'fb_zoom', 500, 200, extend='repeat')
fb_zoom.par.sx.expr = "1.015**op('%s')['chan1']" % null_bass.path
fb_zoom.par.sy.expr = "1.015**op('%s')['chan1']" % null_bass.path
fb_zoom.par.rotate.expr = "absTime.seconds*0.015"
W(fb, fb_zoom)

fb_disp_noise = C(s, noiseTOP, 'fb_displace_noise', 500, 80, type='simplex3d', mono=True,
                   outputresolution='custom', resolutionw=640, resolutionh=360, resmult=False)
fb_disp_noise.par.tz.expr = "(absTime.seconds*0.05) - 0.15*(100**op('%s')['chan1'])" % null_highs.path

fb_disp = C(s, displaceTOP, 'fb_displace', 700, 200, displaceweightx=0.0003, displaceweighty=0.0003)
W(fb_zoom, fb_disp, 0)
W(fb_disp_noise, fb_disp, 1)

fb_blur = C(s, blurTOP, 'fb_blur', 900, 200, size=6, extend='repeat')
W(fb_disp, fb_blur)

fb_faded = C(s, levelTOP, 'fb_faded', 1100, 200, brightness2=0.95)
# Decay must land on RGB (brightness2), not alpha (opacity) -- the loop is
# ADD-composited downstream, which ignores alpha entirely. An opacity-only
# decay left RGB at full strength forever and washed the loop to white.
W(fb_blur, fb_faded)

comp_loop = C(s, compositeTOP, 'composite_loop', 1300, 200, operand='add')
# ADD, not OVER: OVER blends the spectrum stamp's *uniform* alpha over the
# whole frame every frame (verified), erasing existing feedback detail even
# where the stamp itself is black. ADD only contributes where the stamp is
# actually bright.
W(spec_stamp, comp_loop, 0)
W(fb_faded, comp_loop, 1)

loop_null = C(s, nullTOP, 'loop_null', 1500, 200)
W(comp_loop, loop_null)

fb.par.top = loop_null.path  # closes the loop -- fb's wired input is only the reset image

# --- Finishing: colorize + glow ---
palette_dat = s.op('palette_dat')
if palette_dat: palette_dat.destroy()
palette_dat = s.create(tableDAT, 'palette_dat')
palette_dat.nodeX, palette_dat.nodeY = 1500, 50
palette_dat.clear()
palette_dat.appendRow(['pos', 'r', 'g', 'b', 'a'])
palette_dat.appendRow(['0', '0.0', '0.0', '0.0', '1'])
palette_dat.appendRow(['0.5', '0.05', '0.05', '0.35', '1'])
palette_dat.appendRow(['1', '0.65', '0.55', '0.75', '1'])

palette_ramp = C(s, rampTOP, 'palette_ramp', 1700, 50, type='horizontal',
                  outputresolution='custom', resolutionw=256, resolutionh=4, resmult=False)
palette_ramp.par.dat = palette_dat

lookup1 = C(s, lookupTOP, 'lookup1', 1700, 200, channel='luminance')
W(loop_null, lookup1, 0)
W(palette_ramp, lookup1, 1)

glow_blur = C(s, lumablurTOP, 'glow_blur', 1900, 200, blackvalue=0.02, whitewidth=20)
W(lookup1, glow_blur, 0)
W(lookup1, glow_blur, 1)  # lumablurTOP requires 2 sources; reads its own luminance for width

level_final = C(s, levelTOP, 'level_final', 2100, 200, contrast=1.1)
W(glow_blur, level_final)

final_out = C(s, nullTOP, 'final_out', 2300, 200)
W(level_final, final_out)

out1 = C(s, outTOP, 'out1', 2500, 200)
W(final_out, out1)

fb.par.resetpulse.pulse()

# --- Project-level output rig ---
proj_out = p.op('audio_feedback_out')
if proj_out: proj_out.destroy()
proj_out = p.create(outTOP, 'audio_feedback_out')
proj_out.nodeX, proj_out.nodeY = 1500, 400
scene.outputConnectors[0].connect(proj_out.inputConnectors[0])

print('audio_feedback build complete')
