# FusionAgent job (read-only): every body under one occurrence, meshed in THAT occurrence's frame,
# for a 3D assembly guide. Also writes the round holes of each body (screw/insert positions) and the
# user parameters. Run:
#   python run_job.py fusion_export_meshes.py --doc "<doc>" --read-only --light-receipt \
#       --args "{\"root\": \"<component name>\", \"dir\": \"<out folder>\"}"
# Writes <dir>/<comp>__<n>.json = {comp, body, v: [x,y,z,...] mm, f: [i,j,k,...]} and <dir>/index.json.
import os, json

ROOT = args['root']
OUT = args['dir']
os.makedirs(OUT, exist_ok=True)
d = design()
roots = [o for o in d.rootComponent.allOccurrences if o.component.name == ROOT]
if not roots:
    raise RuntimeError('no occurrence of component %r' % ROOT)
root = roots[0]
inv = root.transform2.copy()
inv.invert()
HQ = adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh   # never setSurfaceTolerance(0.01): hung Fusion > 20 min
prefix = root.fullPathName + '+'
occs = [(root, None)] + [(o, o) for o in d.rootComponent.allOccurrences if o.fullPathName.startswith(prefix)]
rec, holes = {}, {}
for o, child in occs:
    comp = o.component
    if child is None:
        T = adsk.core.Matrix3D.create()                       # the root's own bodies are already in its frame
    else:
        T = child.transform2.copy()                           # component -> world (assembly-context proxy)
        T.transformBy(inv)                                    # world -> root frame
    for i, b in enumerate(comp.bRepBodies):                   # native bodies: component space
        mc = b.meshManager.createMeshCalculator()
        mc.setQuality(HQ)
        m = mc.calculate()
        c = m.nodeCoordinatesAsDouble
        v = []
        for k in range(0, len(c), 3):
            p = adsk.core.Point3D.create(c[k], c[k + 1], c[k + 2])
            p.transformBy(T)
            v += [round(p.x * 10, 3), round(p.y * 10, 3), round(p.z * 10, 3)]
        fn = '%s__%02d.json' % (comp.name.replace(' ', '_').replace('/', '_'), i)
        json.dump(dict(comp=comp.name, body=b.name, v=v, f=list(m.nodeIndices)), open(os.path.join(OUT, fn), 'w'), separators=(',', ':'))
        xs, ys, zs = v[0::3], v[1::3], v[2::3]
        key = o.fullPathName + ' / ' + b.name + ('' if i == 0 else ' #%d' % i)
        rec[key] = dict(file=fn, comp=comp.name, body=b.name, tris=len(m.nodeIndices) // 3, visible=b.isVisible,
                        volume_mm3=round(b.volume * 1000, 1),
                        bbox=[min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)])
        hs = []
        for f in b.faces:
            g = f.geometry
            if g.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType or g.radius * 10 > 8:
                continue
            org, ax = g.origin.copy(), g.axis.copy()
            org.transformBy(T); ax.transformBy(T)
            hs.append(dict(d=round(g.radius * 20, 2), o=[round(org.x * 10, 2), round(org.y * 10, 2), round(org.z * 10, 2)],
                           a=[round(ax.x, 3), round(ax.y, 3), round(ax.z, 3)]))
        holes[key] = hs
params = {}
for p in d.userParameters:
    params[p.name] = round(p.value * 10, 4) if p.unit == 'mm' else p.value
json.dump(dict(root=ROOT, bodies=rec, holes=holes, params=params), open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), indent=1)
out['bodies'] = {k: [r['tris'], r['bbox']] for k, r in rec.items()}
