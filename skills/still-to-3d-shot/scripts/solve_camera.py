#!/usr/bin/env python3
"""Solve the camera of a still image from its vanishing points, so a 3D scene can be built to line up with it.

Mark straight edges in the picture that are parallel in the real room (pixel coordinates, origin top-left):
  --x-lines   edges running left-right in the room   (e.g. counter fronts, the top of a window)
  --z-lines   edges running into the room, at right angles to the x edges (floor boards, the side wall)
  --y-lines   optional vertical edges (door frames, cabinet sides); improves tilt and roll
  --ref       optional "ax,ay,bx,by,metres": a vertical thing of known height, its foot (on the floor)
              and its top. Gives the camera's eye height.

  python3 solve_camera.py --size 1920x1080 \
      --x-lines "210,640,900,598;180,930,960,842" \
      --z-lines "1180,612,1810,705;1150,850,1860,1010" \
      --ref "1020,880,1016,655,0.9"

Each line is "x1,y1,x2,y2"; separate lines with ";". Two lines per group is the minimum, three or
four spread across the frame is better. Prints JSON: focal length (for a 36 mm wide sensor), field of
view, tilt, roll, heading and eye height. Assumes square pixels and the optical centre in the middle
of the frame (true for a generated or uncropped image; a cropped photo breaks it).

  python3 solve_camera.py --selftest     # checks the maths against a known camera (21 mm, 1.34 m)
"""
import argparse
import json
import math
import sys

import numpy as np


def parse_lines(s):
    out = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        v = [float(x) for x in part.split(",")]
        if len(v) != 4:
            sys.exit(f"a line needs four numbers x1,y1,x2,y2, got: {part}")
        out.append(v)
    return out


def vanishing_point(lines):
    """Least-squares meeting point of several image lines, as a homogeneous 3-vector."""
    if len(lines) < 2:
        sys.exit("each group needs at least two lines")
    rows = []
    for x1, y1, x2, y2 in lines:
        l = np.cross([x1, y1, 1.0], [x2, y2, 1.0])
        rows.append(l / np.linalg.norm(l[:2]))
    return np.linalg.svd(np.array(rows))[2][-1]


def solve(size, x_lines, z_lines, y_lines=None, ref=None, sensor_mm=36.0):
    W, H = size
    c = np.array([W / 2.0, H / 2.0])
    vx, vz = vanishing_point(x_lines), vanishing_point(z_lines)

    def finite(v):
        return abs(v[2]) > 1e-9 * np.linalg.norm(v[:2])

    if not (finite(vx) and finite(vz)):
        sys.exit("one group of lines is parallel in the picture (one-point perspective): the focal length "
                 "cannot be solved from it. Pick edges that converge, or set the lens by eye.")
    px, pz = vx[:2] / vx[2] - c, vz[:2] / vz[2] - c
    f2 = -float(px @ pz)
    if f2 <= 0:
        sys.exit("the two vanishing points are on the same side of the centre, so the groups are not at "
                 "right angles in the room (or the image was cropped). Re-mark the lines.")
    f = math.sqrt(f2)
    dx = np.array([px[0], px[1], f]); dx /= np.linalg.norm(dx)
    dz = np.array([pz[0], pz[1], f]); dz /= np.linalg.norm(dz)
    up = np.cross(dx, dz); up /= np.linalg.norm(up)
    if y_lines:
        vy = vanishing_point(y_lines)
        dy = np.array([vy[0] - c[0] * vy[2], vy[1] - c[1] * vy[2], f * vy[2]]); dy /= np.linalg.norm(dy)
        if dy @ up < 0:
            dy = -dy
        up = up + dy; up /= np.linalg.norm(up)                 # average the two estimates of "up"
    if up[1] > 0:                                               # image y points down: up must have y < 0
        up = -up
    fwd = np.array([0.0, 0.0, 1.0])
    tilt = math.degrees(math.asin(max(-1.0, min(1.0, float(fwd @ up)))))     # + looks up, - looks down
    roll = math.degrees(math.atan2(up[0], -up[1]))                           # + horizon drops to the right
    flat = fwd - (fwd @ up) * up
    heading = math.degrees(math.atan2(float(flat @ dx), float(flat @ dz)))   # 0 = looking straight along z
    out = {
        "image": [W, H],
        "focal_px": round(f, 2),
        "focal_mm": round(f * sensor_mm / W, 2),
        "sensor_mm": [sensor_mm, round(sensor_mm * H / W, 3)],
        "hfov_deg": round(2 * math.degrees(math.atan(W / (2 * f))), 2),
        "vfov_deg": round(2 * math.degrees(math.atan(H / (2 * f))), 2),
        "tilt_deg": round(tilt, 2),
        "roll_deg": round(roll, 2),
        "heading_deg": round(heading, 2),
        "horizon_y_at_centre": round(H / 2 + f * math.tan(math.radians(tilt)) / max(1e-9, math.cos(math.radians(roll))), 1),
        "vanishing_points": {"x": [round(float(v), 1) for v in (px + c)], "z": [round(float(v), 1) for v in (pz + c)]},
    }
    if ref:
        ax, ay, bx, by, metres = ref
        ra, rb = np.array([ax - c[0], ay - c[1], f]), np.array([bx - c[0], by - c[1], f])
        if abs(up @ ra) < 1e-9:
            sys.exit("the foot of the reference is on the horizon; pick something that stands on the floor")
        # foot A = -h * ra / (up.ra) lies on the floor; top B = A + metres * up lies on ray rb
        A = np.stack([-ra / (up @ ra), -rb], axis=1)
        (h, s), res = np.linalg.lstsq(A, -metres * up, rcond=None)[:2]
        if h <= 0 or s <= 0:
            sys.exit("the reference gives a camera below the floor: check that the first point is the foot")
        out["eye_height_m"] = round(float(h), 3)
        out["reference_fit_error_m"] = round(float(np.linalg.norm(A @ [h, s] + metres * up)), 4)
    return out


def selftest():
    """Project a room from a known camera (21 mm on 36 mm, 1.34 m high, tilted and rolled) and solve it back."""
    W, H, f_mm, eye, tilt, roll, head = 1920, 1080, 21.0, 1.34, -6.0, 1.5, 28.0
    f = f_mm * W / 36.0
    t, r, y = (math.radians(a) for a in (tilt, roll, head))
    # world: x right, y up, z into the room. Camera: x right, y down, z forward.
    Ry = np.array([[math.cos(y), 0, -math.sin(y)], [0, 1, 0], [math.sin(y), 0, math.cos(y)]])     # heading
    Rx = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])     # tilt
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])     # roll
    flip = np.diag([1.0, -1.0, 1.0])
    R = Rz @ flip @ Rx @ Ry

    def proj(p):
        q = R @ (np.array(p, float) - np.array([0, eye, 0]))
        return [f * q[0] / q[2] + W / 2, f * q[1] / q[2] + H / 2]

    def line(a, b):
        return proj(a) + proj(b)

    xs = [line((-1, 0, 4), (1, 0, 4)), line((-1, 0.9, 5), (1.5, 0.9, 5)), line((-0.5, 2.2, 6), (2, 2.2, 6))]
    zs = [line((1, 0, 3), (1, 0, 6)), line((-1, 0.9, 3), (-1, 0.9, 7)), line((2, 2.2, 4), (2, 2.2, 8))]
    ys = [line((1, 0, 4), (1, 2, 4)), line((-1, 0, 5), (-1, 2, 5))]
    foot, top = proj((0.5, 0, 4.5)), proj((0.5, 0.9, 4.5))
    got = solve((W, H), xs, zs, ys, foot + top + [0.9])
    want = {"focal_mm": f_mm, "eye_height_m": eye, "tilt_deg": tilt, "roll_deg": roll, "heading_deg": head}
    ok = True
    for k, v in want.items():
        d = abs(got[k] - v)
        ok &= d < 0.05
        print(f"  {k:<14} want {v:>7}  got {got[k]:>8}  {'ok' if d < 0.05 else 'WRONG'}")
    print("selftest passed" if ok else "selftest FAILED")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", help="image size, e.g. 1920x1080")
    ap.add_argument("--x-lines"); ap.add_argument("--z-lines"); ap.add_argument("--y-lines")
    ap.add_argument("--ref", help="ax,ay,bx,by,metres: foot and top of a vertical thing of known height")
    ap.add_argument("--sensor", type=float, default=36.0, help="sensor width in mm (default 36)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if not (a.size and a.x_lines and a.z_lines):
        ap.error("--size, --x-lines and --z-lines are required")
    W, H = (int(v) for v in a.size.lower().split("x"))
    ref = [float(v) for v in a.ref.split(",")] if a.ref else None
    if ref and len(ref) != 5:
        ap.error("--ref needs five numbers: ax,ay,bx,by,metres")
    print(json.dumps(solve((W, H), parse_lines(a.x_lines), parse_lines(a.z_lines),
                           parse_lines(a.y_lines) if a.y_lines else None, ref, a.sensor), indent=2))


if __name__ == "__main__":
    main()
