"""Can a tool reach this spot? Casts straight rays from each point against the given meshes and
reports how many directions escape to the outside, plus the free length along +-X/Y/Z.
A screw, insert or clamp whose spot has 0 escaping directions cannot be reached by a straight
tool (screwdriver, soldering iron, hex key) - fix the design or the order before writing the step.

  python reach_check.py meshes/HU_Chassis__00.json other.stl --at 7,-21.3,34 --at 25,0,32

Meshes: the {v, f} JSON from fusion_export_meshes.py, or any STL/OBJ trimesh can load
(all in the same frame, mm). Pure numpy (no rtree needed)."""
import argparse, json
import numpy as np


def load(path):
    if path.endswith(".json"):
        d = json.load(open(path))
        return np.array(d["v"], float).reshape(-1, 3), np.array(d["f"], int).reshape(-1, 3)
    import trimesh
    m = trimesh.load(path, force="mesh")
    return np.asarray(m.vertices, float), np.asarray(m.faces, int)


ap = argparse.ArgumentParser()
ap.add_argument("meshes", nargs="+")
ap.add_argument("--at", action="append", required=True, help="x,y,z in mm (repeatable)")
ap.add_argument("--rays", type=int, default=3000)
a = ap.parse_args()
V, F, off = [], [], 0
for p in a.meshes:
    v, f = load(p); V.append(v); F.append(f + off); off += len(v)
V, F = np.vstack(V), np.vstack(F)
A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
E1, E2 = B - A, C - A


def first_hit(o, d):
    """Distance to the first triangle along d from o (Moller-Trumbore over all triangles), or None."""
    P = np.cross(d, E2); det = (E1 * P).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); T = o - A
    u = (T * P).sum(1) * inv; Q = np.cross(T, E1); v = (d * Q).sum(1) * inv; t = (E2 * Q).sum(1) * inv
    h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
    return float(t[h].min()) if h.any() else None


rng = np.random.default_rng(1)
U = rng.normal(size=(a.rays, 3)); U /= np.linalg.norm(U, axis=1)[:, None]
for s in a.at:
    o = np.array([float(x) for x in s.split(",")])
    esc = [u for u in U if first_hit(o, u) is None]
    print(f"at {s}: {len(esc)} of {len(U)} directions escape")
    for name, d in [("+X", (1, 0, 0)), ("-X", (-1, 0, 0)), ("+Y", (0, 1, 0)), ("-Y", (0, -1, 0)), ("+Z", (0, 0, 1)), ("-Z", (0, 0, -1))]:
        t = first_hit(o, np.array(d, float))
        print(f"   {name}: {'open' if t is None else 'blocked at %.1f mm' % t}")
    if esc:
        print("   escaping e.g.", np.round(np.array(esc[:5]), 2).tolist())
