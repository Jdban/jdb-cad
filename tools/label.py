"""Engrave a part ID onto a build123d solid.

Every printed part carries a short ID (e.g. "I5") so it can be referred to
later and looked up in the project's PARTS.md.

    from label import engrave
    part = engrave(part, "I5", origin=(30, 20, 0), normal=(0, 0, -1), up=(1, 0, 0))

origin: a point on the flat face to engrave (text is centred there)
normal: the face's outward normal (the side you read it from)
up:     which way is "up" for the text, lying in the face
Pick a face that doesn't touch anything (not a fit, sealing or food surface).
"""
from build123d import Plane, Text, FontStyle, Vector, extrude


def engrave(part, text, origin, normal, up, size=4.0, depth=0.5, check=True):
    n = Vector(*normal).normalized()
    u = Vector(*up).normalized()
    right = u.cross(n)                       # text runs left-to-right as seen from outside
    plane = Plane(origin=origin, x_dir=right, z_dir=n)
    letters = extrude(plane * Text(text, font_size=size, font_style=FontStyle.BOLD), depth, dir=-n)
    out = part - letters
    if check:   # the engraving should lie fully inside the part (not hanging off an edge)
        removed = part.volume - out.volume
        if removed < 0.95 * letters.volume:
            raise ValueError(f"label {text!r} only {removed / letters.volume:.0%} inside the part: "
                             "move it or make it smaller")
    return out
