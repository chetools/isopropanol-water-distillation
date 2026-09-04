r"""Geometry helpers for asserting that SVG diagrams stay legible.

Estimates a bounding box for every <text> element from its anchor, font size
and rendered character count, then reports pairs that overlap.  Approximate,
but it reliably catches the gross collisions that make a figure look amateur --
and it checks all fifteen diagrams in a second, which eyeballing does not.
"""
import re


TEXT = re.compile(
    r'<text\s+([^>]*?)>(.*?)</text>', re.S)
ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')
TAG = re.compile(r"<[^>]+>")

# Mean glyph width as a fraction of font size, for a humanist sans at these sizes.
WIDTH_RATIO = 0.52


def boxes(svg: str):
    out = []
    for attrs_raw, inner in TEXT.findall(svg):
        attrs = dict(ATTR.findall(attrs_raw))
        if "x" not in attrs or "y" not in attrs:
            continue
        # Rotated labels sit outside the main flow; skip them.
        if "transform" in attrs:
            continue
        try:
            x, y = float(attrs["x"]), float(attrs["y"])
        except ValueError:
            continue
        size = float(attrs.get("font-size", 13))
        plain = TAG.sub("", inner)
        # Resolve entities before measuring: the zero-width space that resets a
        # subscript's dy is eight source characters but zero rendered width, so
        # counting it raw would grossly inflate every label carrying a symbol.
        plain = re.sub(r"&#8203;|&#x200[bB];", "", plain)
        plain = plain.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        plain = re.sub(r"&[a-zA-Z]+;|&#\d+;", "x", plain)
        # Subscript glyphs render at 0.72 em, so they are narrower than the run.
        subscripts = sum(len(t) for t in re.findall(r'<tspan dy="0\.3em"[^>]*>([^<]*)</tspan>', inner))
        width = (len(plain) - subscripts) * size * WIDTH_RATIO
        width += subscripts * size * WIDTH_RATIO * 0.72
        anchor = attrs.get("text-anchor", "start")
        if anchor == "middle":
            x0 = x - width / 2
        elif anchor == "end":
            x0 = x - width
        else:
            x0 = x
        # Baseline sits near the bottom of the glyph box.
        out.append((x0, y - size * 0.78, x0 + width, y + size * 0.24, plain.strip()))
    return out


def overlaps(a, b, pad=1.0):
    ax0, ay0, ax1, ay1, _ = a
    bx0, by0, bx1, by1, _ = b
    return not (ax1 <= bx0 + pad or bx1 <= ax0 + pad
                or ay1 <= by0 + pad or by1 <= ay0 + pad)


def area(box):
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
