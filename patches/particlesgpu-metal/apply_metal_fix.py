"""
Make the particlesGPU tox render under Metal / macOS (TD 2025.x, Apple Silicon).

Two independent breakages, both fixed here. Idempotent: safe to re-run, and it
only touches operators inside the target particlesGpu COMP.

1. "Geometry Shaders not supported on this GPU or OS."
   phong1GLSL expanded each particle point into a camera-facing quad in
   phong1GLSLGeometry. Metal has no geometry shader stage, so the MAT errored
   and nothing rendered. Fix: do the expansion in the vertex shader instead --
   renderParticles/grid1 becomes a 2x2 quad (P.xy spans [-0.5, 0.5]) copied
   once per particle, and every vertex offsets itself in camera space. The
   quad/rotation math in phong1GLSLVertexMAC.glsl is a 1:1 port of the old
   geometry shader; the pixel shader is unchanged.

2. "Sampler type of uniform sTexture does not match up with that of the
   referenced TOP." (was masked by #1, and renders fully black on its own --
   sTexture reads 0, alpha 0, every fragment hits the uDiscardAlpha discard)
   select8/select9 used `depth == 0` / `depth > 0` to ask "is the incoming
   particle map already a 2D texture array?". On build 2025.33230 every TOP
   reports depth 1 -- including tex3d2, which IS an array -- so both guards are
   stuck true: tex3d2 was fed the blank `white` TOP and the sampler2DArray was
   fed a plain 2D TOP. Fix: always build the array through tex3d2.

Usage, from the MCP `run` tool or a TD Text DAT:
    exec(open('<repo>/patches/particlesgpu-metal/apply_metal_fix.py').read())
    apply_metal_fix(op('/project1/particlesGpu'))
    # revert_metal_fix(op('/project1/particlesGpu'))
"""

import os

VERTEX_DAT = 'phong1GLSLVertexMAC'
SHADER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'phong1GLSLVertexMAC.glsl')


def apply_metal_fix(comp, shader_path=SHADER_FILE):
    rp = comp.op('renderParticles')
    mat = comp.op('phong1GLSL')

    # --- 1a. the Metal vertex shader ---------------------------------------
    with open(shader_path) as f:
        src = f.read()
    dat = comp.op(VERTEX_DAT)
    if dat is None:
        dat = comp.create(textDAT, VERTEX_DAT)
        ref = comp.op('phong1GLSLVertex')
        dat.nodeX, dat.nodeY = ref.nodeX, ref.nodeY - 160
    dat.text = src

    # --- 1b. one quad per particle instead of one point --------------------
    rp.op('grid1').par.rows = 2
    rp.op('grid1').par.cols = 2
    rp.op('convert1').par.totype = 'poly'      # was 'part' (point primitives)
    # objIndex must count quads, not vertices, now that a particle is 4 points
    rp.op('point1').par.attr0value1.expr = (
        "me.inputPoint.index // max(1, len(op('sourceGeo').points))")

    mat.par.vdat = VERTEX_DAT
    mat.par.gdat = ''                          # no geometry shader under Metal

    # --- 2. always build the sampler2DArray through tex3d2 -----------------
    comp.op('select8').par.top.expr = "'default'"
    comp.op('select9').par.top.expr = "'tex3d2'"

    mat.cook(force=True)
    return {'errors': mat.errors(), 'warnings': mat.warnings()}


def revert_metal_fix(comp):
    """Restore the stock (OpenGL-only) configuration."""
    rp = comp.op('renderParticles')
    mat = comp.op('phong1GLSL')
    rp.op('grid1').par.rows = 1
    rp.op('grid1').par.cols = 1
    rp.op('convert1').par.totype = 'part'
    rp.op('point1').par.attr0value1.expr = 'me.inputPoint.index'
    mat.par.vdat = 'phong1GLSLVertex'
    mat.par.gdat = 'phong1GLSLGeometry'
    comp.op('select8').par.top.expr = (
        "'default' if op('default').depth == 0 else 'white'")
    comp.op('select9').par.top.expr = (
        "'default' if op('default').depth > 0 else 'tex3d2'")
    mat.cook(force=True)
