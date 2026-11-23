"""Chaskidoo icon set: stepped C (Inca stonework / chakana steps) + three knots (dev -> stage -> prod)."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = Path("chaskidoo"); OUT.mkdir(exist_ok=True)
U = 32
OX, OY = 34, 64            # x offset centers the C + knots group in the 512 tile
BG1, BG2 = "#1D2E52", "#0E1730"
NAVY = "#14213D"
CREAM, OCHRE, TERRA = "#F4E9D8", "#E8A33D", "#D2603F"

def X(x): return OX + x*U
def Y(y): return OY + y*U

C_POINTS = [(8.0,2.3),(5.0,2.3),(5.0,3.7),(3.6,3.7),(3.6,5.1),(2.2,5.1),(2.2,6.9),(3.6,6.9),(3.6,8.3),(5.0,8.3),(5.0,9.7),(8.0,9.7)]
KNOTS = [(5.7, 0.42, "c"), (7.55, 0.66, "t"), (9.95, 1.05, "o")]

def mark(c_color=CREAM, knot_colors=None, dx=0, dy=0, scale=1.0):
    kc = knot_colors or {"c": CREAM, "t": TERRA, "o": OCHRE}
    d = "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in C_POINTS)
    knots = "\n".join(
        f'    <circle cx="{X(x):.1f}" cy="{Y(6):.1f}" r="{r*U:.1f}" fill="{kc[k]}"/>' for x, r, k in KNOTS
    )
    return (f'  <g transform="translate({dx} {dy}) scale({scale})">\n'
            f'    <path d="{d}" fill="none" stroke="{c_color}" stroke-width="{1.15*U:.1f}" stroke-linejoin="miter"/>\n'
            f'{knots}\n  </g>')

def tile(rx=112):
    return (f'  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>\n'
            f'  <rect width="512" height="512" rx="{rx}" fill="url(#bg)"/>')

def svg(body, w, h, title="Chaskidoo"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">\n'
            f'  <title>{title}</title>\n{body}\n</svg>\n')

# 1. App icon (rounded tile)
(OUT / "chaskidoo-icon.svg").write_text(svg(tile() + "\n" + mark(), 512, 512))
# 2. Favicon: square-ish tile, slightly larger mark for 16-32 px
(OUT / "chaskidoo-favicon.svg").write_text(svg(tile(rx=96) + "\n" + mark(dx=-28, dy=-28, scale=1.11), 512, 512))
# 3. Mark only (transparent), for light and dark backgrounds
(OUT / "chaskidoo-mark-light-bg.svg").write_text(svg(mark(c_color=NAVY, knot_colors={"c": NAVY, "t": TERRA, "o": OCHRE}), 512, 512))
(OUT / "chaskidoo-mark-dark-bg.svg").write_text(svg(mark(), 512, 512))

# 4. Lockup: icon + wordmark, text converted to outlines (Inter SemiBold)
font = TTFont("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
upm = font["head"].unitsPerEm

def word_path(text, size, x0, baseline, tracking=-0.01):
    s = size / upm; x = x0; parts = []
    for ch in text:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        parts.append(pen.getCommands())
        x += hmtx[g][0] * s + tracking * size
    return " ".join(parts), x

def lockup(dark: bool):
    h, icon_size = 160, 128
    pad = (h - icon_size) / 2
    word, end = word_path("chaskidoo", 76, icon_size + pad + 32, 107)
    w = int(end + pad + 16)
    bg = f'  <rect width="{w}" height="{h}" rx="24" fill="{NAVY}"/>\n' if dark else ""
    color = CREAM if dark else NAVY
    icon = (f'  <g transform="translate({pad} {pad}) scale({icon_size/512})">\n'
            + tile().replace("\n", "\n  ") + "\n  " + mark().replace("\n", "\n  ") + "\n  </g>")
    return svg(f'{bg}{icon}\n  <path d="{word}" fill="{color}"/>', w, h)

(OUT / "chaskidoo-lockup-light.svg").write_text(lockup(dark=False))
(OUT / "chaskidoo-lockup-dark.svg").write_text(lockup(dark=True))
print("svgs:", sorted(p.name for p in OUT.glob("*.svg")))
