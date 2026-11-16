"""
make_electrode.py
=================

Parametric CAD model of a dry sEMG electrode: a 316L stainless-steel domed button
with an M2 threaded stud on the back, meant to be CNC-turned on a lathe.

What this script produces (all written next to this file):
    electrode_316L_dome.step   -> 3D model to upload to Xometry / Hubs / any machine shop
    electrode_316L_dome.stl    -> mesh, handy for 3D-printing a fit-check dummy
    electrode_316L_dome_drawing.pdf / .png -> 2D drawing with dimensions and notes

How to run (tested; `uv` fetches cadquery + matplotlib into a temporary environment):
    uv run --python 3.11 --with cadquery --with matplotlib python make_electrode.py

To change the design, edit the numbers in the PARAMETERS section and run it again.
All lengths are in millimetres.
"""

import math                      # square roots for the dome height
from pathlib import Path         # building file paths next to this script

import cadquery as cq            # the CAD library that builds the solid and writes STEP
import matplotlib                # plotting library used to draw the 2D drawing
matplotlib.use("Agg")            # draw to files only (no window needed)
import matplotlib.pyplot as plt  # the plotting interface
from matplotlib.patches import Circle, Arc  # shapes for the top view

# ---------------------------------------------------------------------------
# PARAMETERS  (edit these)
# ---------------------------------------------------------------------------
HEAD_DIAMETER = 6.0     # outer diameter of the skin-contact button
HEAD_HEIGHT = 4.0       # total height of the button, from its flat back to the top of the dome
DOME_RADIUS = 9.0       # radius of the spherical top; bigger = flatter dome
EDGE_FILLET = 0.5       # rounding where the dome meets the side wall (comfort, no sharp edge)
BACK_CHAMFER = 0.2      # small chamfer on the back outer edge (deburr)
STUD_DIAMETER = 2.0     # M2 stud major diameter
STUD_LENGTH = 4.0       # stud length below the head (PCB 1.6 + washer + M2 nut ~1.6 + spare)
STUD_TIP_CHAMFER = 0.2  # chamfer on the stud end so the nut starts easily
PART_NAME = "electrode_316L_dome"   # base name for every output file

OUT_DIR = Path(__file__).resolve().parent   # write outputs next to this script


def dome_sag(radius: float, diameter: float) -> float:
    """
    How far the centre of a spherical cap sticks up above its rim.

    A sphere of radius R cut by a circle of radius r rises by
    sag = R - sqrt(R^2 - r^2) at its centre.
    """
    r = diameter / 2.0                         # rim radius of the dome
    return radius - math.sqrt(radius**2 - r**2)  # height of the cap above the rim


def build_electrode() -> cq.Workplane:
    """
    Build the electrode as one solid and return it.

    Steps: plain cylinder for the head -> cut the top into a sphere ->
    round and chamfer the edges -> add the threaded stud underneath.
    The flat back of the head sits at z = 0; the dome points up (+z), the stud down (-z).
    """
    # Head blank: a plain cylinder from z = 0 up to the full head height.
    head = cq.Workplane("XY").circle(HEAD_DIAMETER / 2).extrude(HEAD_HEIGHT)

    # A big sphere whose top touches z = HEAD_HEIGHT; intersecting keeps only the domed part.
    sphere = cq.Workplane("XY").sphere(DOME_RADIUS).translate((0, 0, HEAD_HEIGHT - DOME_RADIUS))
    head = head.intersect(sphere)  # the cylinder now has a spherical top

    # Round the sharp circular edge where the dome meets the side wall.
    sag = dome_sag(DOME_RADIUS, HEAD_DIAMETER)          # dome height above the rim
    rim_z = HEAD_HEIGHT - sag                            # z height of that rim edge
    head = head.edges(cq.selectors.BoxSelector(          # pick only the edge near the rim height
        (-10, -10, rim_z - 0.05), (10, 10, rim_z + 0.05))).fillet(EDGE_FILLET)

    # Small deburr chamfer on the outer edge of the flat back (z = 0).
    head = head.faces("<Z").edges().chamfer(BACK_CHAMFER)

    # Threaded stud: a plain cylinder; the thread is a drawing callout (standard practice for STEP).
    stud = (cq.Workplane("XY")
            .circle(STUD_DIAMETER / 2)                  # stud cross-section
            .extrude(-STUD_LENGTH)                      # extend downward from the back face
            .faces("<Z").edges().chamfer(STUD_TIP_CHAMFER))  # lead-in chamfer at the tip

    return head.union(stud)  # head and stud as one single machined part


def export_3d(part: cq.Workplane) -> None:
    """Write the STEP (for quoting/machining) and STL (for 3D-printed fit checks)."""
    cq.exporters.export(part, str(OUT_DIR / f"{PART_NAME}.step"))  # exact geometry for the shop
    cq.exporters.export(part, str(OUT_DIR / f"{PART_NAME}.stl"))   # triangle mesh


def dim(ax, x1, y1, x2, y2, text, offset=(0, 0), rotation=0):
    """Draw a double-headed dimension arrow between two points with a label."""
    ax.annotate("", xy=(x1, y1), xytext=(x2, y2),                 # the arrow itself
                arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((x1 + x2) / 2 + offset[0], (y1 + y2) / 2 + offset[1], text,  # label at the midpoint
            ha="center", va="center", fontsize=8, rotation=rotation,
            bbox=dict(fc="white", ec="none", pad=0.5))


def side_profile():
    """
    Return (xs, ys) of the half-profile outline (right side), from stud tip up to the dome top.
    Used for the side view; mirrored to get the left side.
    """
    r = HEAD_DIAMETER / 2                                 # head radius
    rs = STUD_DIAMETER / 2                                # stud radius
    sag = dome_sag(DOME_RADIUS, HEAD_DIAMETER)            # dome height
    rim = HEAD_HEIGHT - sag                               # rim height
    pts = [(0, -STUD_LENGTH), (rs - STUD_TIP_CHAMFER, -STUD_LENGTH),   # stud tip with chamfer
           (rs, -STUD_LENGTH + STUD_TIP_CHAMFER), (rs, 0),            # up the stud to the back face
           (r - BACK_CHAMFER, 0), (r, BACK_CHAMFER)]                 # back face and its chamfer
    # Fillet geometry: a circle of radius f that touches both the side wall (x = r)
    # and the inside of the dome sphere (centre (0, cz), radius R).
    f = EDGE_FILLET                                       # fillet radius
    R = DOME_RADIUS                                       # dome sphere radius
    cz = HEAD_HEIGHT - R                                  # sphere centre height
    fx = r - f                                            # fillet centre x (f in from the wall)
    fz = cz + math.sqrt((R - f) ** 2 - fx ** 2)           # fillet centre z (R - f from sphere centre)
    pts.append((r, fz))                                   # side wall ends where the fillet starts
    a_wall = 0.0                                          # angle of the wall tangent point (pointing +x)
    a_dome = math.atan2(fz - cz, fx)                      # angle of the dome tangent point
    for i in range(1, 21):                                # 20 points around the fillet arc
        a = a_wall + (a_dome - a_wall) * i / 20
        pts.append((fx + f * math.cos(a), fz + f * math.sin(a)))
    x_start = pts[-1][0]                                  # dome starts where the fillet ends
    for i in range(1, 41):                                # 40 points along the dome to the centre
        x = x_start * (1 - i / 40)
        pts.append((x, cz + math.sqrt(R ** 2 - x ** 2)))
    return [p[0] for p in pts], [p[1] for p in pts]


def make_drawing() -> None:
    """Draw a simple 2D drawing (side view + top view + notes) and save it as PDF and PNG."""
    sag = dome_sag(DOME_RADIUS, HEAD_DIAMETER)            # dome height, shown on the drawing
    fig = plt.figure(figsize=(11.69, 8.27))               # A4 landscape, in inches
    ax = fig.add_axes([0.04, 0.30, 0.42, 0.62])           # side view area
    ax2 = fig.add_axes([0.50, 0.40, 0.22, 0.42])          # top view area

    # ---- Side view -------------------------------------------------------
    xs, ys = side_profile()                               # right half of the outline
    ax.plot(xs, ys, "k", lw=1.2)                          # right side
    ax.plot([-x for x in xs], ys, "k", lw=1.2)            # mirrored left side
    ax.plot([-HEAD_DIAMETER / 2, HEAD_DIAMETER / 2], [0, 0], "k", lw=0.6)  # back-face line
    ax.plot([0, 0], [-STUD_LENGTH - 0.6, HEAD_HEIGHT + 0.6], "k-.", lw=0.5)  # centre line
    for y in (-STUD_LENGTH + 0.3, -STUD_LENGTH + 0.9, -STUD_LENGTH + 1.5,   # thread hatch marks
              -STUD_LENGTH + 2.1, -STUD_LENGTH + 2.7, -STUD_LENGTH + 3.3):
        ax.plot([-STUD_DIAMETER / 2 * 0.8, STUD_DIAMETER / 2 * 0.8], [y, y], "k", lw=0.4)
    r = HEAD_DIAMETER / 2
    dim(ax, -r, HEAD_HEIGHT + 1.2, r, HEAD_HEIGHT + 1.2, f"Ø{HEAD_DIAMETER:.1f}")
    dim(ax, r + 1.3, 0, r + 1.3, HEAD_HEIGHT, f"{HEAD_HEIGHT:.1f}", offset=(0.6, 0))
    dim(ax, r + 0.6, HEAD_HEIGHT - sag, r + 0.6, HEAD_HEIGHT, f"{sag:.2f} ref", offset=(0.9, 0.35))
    dim(ax, -r + 0.6, -STUD_LENGTH, -r + 0.6, 0, f"{STUD_LENGTH:.1f}", offset=(-0.6, 0))
    ax.text(-r - 3.6, -STUD_LENGTH / 2 - 0.4, "M2×0.4-6g\nsee note 4", fontsize=8, ha="left")
    ax.text(0.4, HEAD_HEIGHT + 0.25, f"SR{DOME_RADIUS:.0f}", fontsize=8)          # dome radius
    ax.text(r - 0.1, HEAD_HEIGHT - sag - 0.65, f"R{EDGE_FILLET}", fontsize=7, ha="right")
    ax.text(r - 0.9, 0.3, f"{BACK_CHAMFER}×45°", fontsize=7)
    ax.set_title("SIDE VIEW (scale ~8:1)", fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-7.5, 7.5); ax.set_ylim(-STUD_LENGTH - 1.5, HEAD_HEIGHT + 2.2)

    # ---- Top view --------------------------------------------------------
    ax2.add_patch(Circle((0, 0), HEAD_DIAMETER / 2, fill=False, lw=1.2))             # head outline
    ax2.add_patch(Circle((0, 0), HEAD_DIAMETER / 2 - EDGE_FILLET, fill=False, lw=0.5, ls="--"))
    ax2.plot([-4, 4], [0, 0], "k-.", lw=0.5); ax2.plot([0, 0], [-4, 4], "k-.", lw=0.5)
    ax2.text(0, -4.6, "Skin-contact face: no visible tool marks,\nno burrs, Ra ≤ 0.8 µm",
             ha="center", fontsize=7)
    ax2.set_title("TOP VIEW (skin side)", fontsize=10)
    ax2.set_aspect("equal"); ax2.axis("off"); ax2.set_xlim(-5, 5); ax2.set_ylim(-5.5, 5)

    # ---- Notes and title block ------------------------------------------
    notes = (
        "NOTES\n"
        "1. MATERIAL: 316L stainless steel (UNS S31603), mill certificate required with each lot.\n"
        "   DO NOT substitute 303 or any free-machining (high-sulfur) grade. Implant-grade\n"
        "   316L (e.g. ASTM F138) acceptable but optional (quote both if price differs).\n"
        "2. FINISH: passivate (e.g. per ASTM A967) or electropolish. Skin face Ra ≤ 0.8 µm, no burrs.\n"
        "3. GENERAL TOLERANCE: ±0.1 mm unless stated. Break all sharp edges 0.1 mm max.\n"
        "4. THREAD: M2×0.4-6g. Thread runout or relief groove allowed at the head, max 0.8 mm;\n"
        "   min 3.0 mm full thread. Stud concentric to head within 0.1 mm.\n"
        "5. No marking, no coatings, no lubricant residue on the skin face. Clean and bag individually\n"
        "   or in lint-free trays.\n"
        "6. Starting-point design, not yet validated on skin. Dome radius, size and finish to be\n"
        "   confirmed with electrode_testing_protocol.md."
    )
    fig.text(0.04, 0.03, notes, fontsize=8, family="monospace", va="bottom")
    title = (f"PART: {PART_NAME}\nDry sEMG electrode, CNC turned\n"
             f"Units: mm    Qty: see PO\nRev A (draft, 2026-11-16)")
    fig.text(0.76, 0.06, title, fontsize=9, family="monospace", va="bottom",
             bbox=dict(fc="white", ec="black"))
    fig.savefig(OUT_DIR / f"{PART_NAME}_drawing.pdf")      # vector drawing for the shop
    fig.savefig(OUT_DIR / f"{PART_NAME}_drawing.png", dpi=150)  # quick preview image
    plt.close(fig)


if __name__ == "__main__":
    part = build_electrode()     # 1) build the solid
    export_3d(part)              # 2) write STEP + STL
    make_drawing()               # 3) write the 2D drawing
    bb = part.val().BoundingBox()  # report size so the run can be sanity-checked
    print(f"Bounding box: X {bb.xlen:.3f}  Y {bb.ylen:.3f}  Z {bb.zlen:.3f} mm")
    print(f"Volume: {part.val().Volume():.2f} mm^3   dome sag: {dome_sag(DOME_RADIUS, HEAD_DIAMETER):.3f} mm")
