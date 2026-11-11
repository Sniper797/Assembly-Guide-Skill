"""Every part of a small electronics box, drawn in code, as quantised meshes for the 3D assembly
guide. No CAD needed: run it, then  python ../build_html.py . example-box  and open standalone.html.

Frame (mm): Z up, Z = 0 under the box floor; +Y = the front, where the USB-C slot is.
Box 80 x 60 x 30, walls and floor 2. A 50 x 40 board on four 5 mm standoffs, its USB-C port at the
slot. A lid with a locating lip, four M3 x 8 screws into heat-set inserts in the corner bosses.

In a real guide the printed parts come from CAD (fusion_export_meshes.py -> meshes/) and only the
bought hardware is drawn here. Writes parts.json: {id: {"p": b64 int16 xyz (0.01 mm), "i": b64 uint16/32, "w": 2|4}}."""
import base64, json, os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
cat = trimesh.util.concatenate


def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]); return b


def cyl(p0, p1, r, n=24):
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=n)


def ring(p0, p1, r_in, r_out, n=24):
    return trimesh.creation.annulus(r_min=r_in, r_max=r_out, segment=[p0, p1], sections=n)


def tube(points, r, n=14):
    pts = [np.asarray(p, float) for p in points]
    parts = [cyl(a, b, r, n) for a, b in zip(pts, pts[1:])]
    for p in pts[1:-1]:
        s = trimesh.creation.icosphere(subdivisions=1, radius=r); s.apply_translation(p); parts.append(s)
    return cat(parts)


X, Y, H, W = 40.0, 30.0, 30.0, 2.0            # half width, half depth, height, wall
SLOT = (-6.0, 6.0, 7.5, 13.0)                 # USB-C slot in the front wall: x0, x1, z0, z1
BOSS = [(sx * 34.0, sy * 24.0) for sx in (-1, 1) for sy in (-1, 1)]       # lid bosses, touching two walls
STAND = [(sx * 21.0, y) for sx in (-1, 1) for y in (-10.0, 22.0)]        # board standoffs
ZB = W + 5.0                                  # board underside (standoffs 5 mm)
TB = 1.6                                      # board thickness

parts = {}
# ---- printed ----
x0, x1, z0, z1 = SLOT
parts["box"] = cat([
    box(-X, X, -Y, Y, 0, W),                                   # floor
    box(-X, X, -Y, -Y + W, W, H),                              # back wall
    box(-X, -X + W, -Y + W, Y - W, W, H), box(X - W, X, -Y + W, Y - W, W, H),   # side walls
    box(-X, x0, Y - W, Y, W, H), box(x1, X, Y - W, Y, W, H),   # front wall, either side of the slot
    box(x0, x1, Y - W, Y, W, z0), box(x0, x1, Y - W, Y, z1, H),
    *[ring((x, y, W), (x, y, H), 2.0, 4.0) for x, y in BOSS],           # 4 mm holes for the inserts
    *[ring((x, y, W), (x, y, ZB), 1.1, 2.5, 18) for x, y in STAND],
])
LIP_T, LIP_GAP = 1.5, 0.2                     # lip inside the walls; stops short of the corner bosses
li = X - W - LIP_GAP; lj = Y - W - LIP_GAP
parts["lid"] = cat([
    box(-X, X, -Y, Y, H, H + 2),
    box(-28, 28, lj - LIP_T, lj, H - 3, H), box(-28, 28, -lj, -lj + LIP_T, H - 3, H),
    box(li - LIP_T, li, -18, 18, H - 3, H), box(-li, -li + LIP_T, -18, 18, H - 3, H),
])

# ---- bought ----
parts["inserts"] = cat([ring((x, y, H - 5.7), (x, y, H), 1.5, 2.1, 16) for x, y in BOSS])       # M3 x 5.7, OD 4.2
parts["board"] = cat([box(-25, 25, -14, 26, ZB, ZB + TB), box(-8, 8, 0, 12, ZB + TB, ZB + TB + 1.2)])
parts["usb"] = box(-4.5, 4.5, 21, 27.5, ZB + TB, ZB + TB + 3.2)          # overhangs the board edge by 1.5
parts["boardscrews"] = cat([cat([cyl((x, y, ZB + TB), (x, y, ZB + TB + 1.8), 2.25, 16),
                                 cyl((x, y, ZB + TB - 6), (x, y, ZB + TB), 1.25, 12)]) for x, y in STAND])
parts["lidscrews"] = cat([cat([cyl((x, y, H + 2), (x, y, H + 4), 2.75, 18),
                               cyl((x, y, H + 2 - 8), (x, y, H + 2), 1.5, 14)]) for x, y in BOSS])   # M3 x 8 pan head
parts["feet"] = cat([cyl((sx * 32, sy * 22, -2), (sx * 32, sy * 22, 0), 5.0, 28) for sx in (-1, 1) for sy in (-1, 1)])
zc = ZB + TB + 1.6                                                        # port centre
parts["cable"] = cat([box(-3.5, 3.5, 22, Y + 0.5, zc - 0.9, zc + 0.9),   # plug tongue, through the slot
                      box(-6, 6, Y + 0.5, Y + 18, zc - 2.3, zc + 2.3),   # overmould, outside the wall
                      tube([(0, Y + 18, zc), (0, Y + 40, zc), (0, Y + 60, 4), (0, Y + 90, 0)], 2.0)])

# ---- clearances the steps quote (checked here so the text can't drift from the model) ----
usb = parts["usb"].bounds; tongue = (-3.5, 3.5, zc - 0.9, zc + 0.9)
print("usb to front wall inner face: %.1f mm" % ((Y - W) - usb[1][1]))
print("tongue in slot: %.1f mm each side, %.1f below, %.1f above" % (tongue[0] - x0, tongue[2] - z0, z1 - tongue[3]))
print("lid screw tip below the insert: %.1f mm" % ((H - 5.7) - (H + 2 - 8)))

out, total = {}, 0
for kname, m in parts.items():
    m = m.copy(); m.merge_vertices()
    q = np.round(np.asarray(m.vertices) * 100).astype(np.int64)
    assert np.abs(q).max() < 32767, kname
    q = q.astype(np.int16)
    f = np.asarray(m.faces)
    ix = f.astype(np.uint16 if len(q) < 65536 else np.uint32)
    out[kname] = {"p": base64.b64encode(q.tobytes()).decode(), "i": base64.b64encode(ix.tobytes()).decode(),
                  "w": 2 if ix.dtype == np.uint16 else 4}
    total += len(f)
    print(f"{kname:12s} tris {len(f):6d}  bounds {np.round(m.bounds, 2).tolist()}")
with open(os.path.join(HERE, "parts.json"), "w") as fh:
    json.dump(out, fh, separators=(",", ":"))
print("triangles", total, "json bytes", os.path.getsize(os.path.join(HERE, "parts.json")))
