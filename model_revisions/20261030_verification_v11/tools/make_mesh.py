"""Cylinder mesh family for the v11 grid check (Opus B).

Same topology as the v06/v08 generator (archived bootstrap
20261029_cylinder_v06/prepare.py): a centre node column, nr uniform radial
rings, nt uniform sectors starting at theta=pi/2 (so the x=0.025 m material
plane is resolved by radial faces), Gmsh 2.2 wedges (type 6) in the centre
ring and hexahedra (type 5) elsewhere. Vertical levels follow one fixed
geometric mapping y(xi)=H*(1-q40**(40*xi))/(1-q40**40), xi=k/nz, q40=0.9;
this is the mapping of the v08 40-layer levels (inherited from the v05 2-D
grid, rounded there to ~5e-8 m). The medium level therefore reuses the frozen
v08 cylinder.msh byte-for-byte instead of a regenerated file; the regenerated
medium mesh is only used to verify this generator against it.

Usage: python make_mesh.py nr nt nz out.msh out_geometry.json
"""
import json, math, sys, hashlib
import numpy as np

R, H, XC = 0.025, 0.04, 0.025
Q40 = 0.9


def levels(nz):
    k = np.arange(nz + 1)
    q = Q40 ** (40.0 / nz)
    y = H * (1 - q ** k) / (1 - q ** nz)
    y[0], y[-1] = 0.0, H
    return y


def build(nr, nt, nz):
    if nt % 2:
        raise SystemExit('nt must be even so radial faces lie on x=0.025')
    ys = levels(nz)
    nodes, lookup = [], {}
    for k, y in enumerate(ys):
        lookup[k, 0, 0] = len(nodes) + 1
        nodes.append((XC, y, 0))
        for j in range(1, nr + 1):
            for i in range(nt):
                t = math.pi / 2 + 2 * math.pi * i / nt
                lookup[k, j, i] = len(nodes) + 1
                nodes.append((XC + R * j / nr * math.cos(t), y, R * j / nr * math.sin(t)))

    def ix(k, j, i):
        return lookup[k, j, i % nt if j else 0]

    elements = []
    for k in range(nz):
        for i in range(nt):
            elements.append((6, [ix(k, 0, 0), ix(k, 1, i + 1), ix(k, 1, i), ix(k + 1, 0, 0), ix(k + 1, 1, i + 1), ix(k + 1, 1, i)]))
            for j in range(1, nr):
                bottom = [ix(k, j, i), ix(k, j, i + 1), ix(k, j + 1, i + 1), ix(k, j + 1, i)]
                top = [ix(k + 1, j, i), ix(k + 1, j, i + 1), ix(k + 1, j + 1, i + 1), ix(k + 1, j + 1, i)]
                elements.append((5, bottom + top))
    return ys, nodes, elements


def write_msh(path, nodes, elements):
    with open(path, 'w', newline='\n') as o:
        o.write('$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$Nodes\n' + str(len(nodes)) + '\n')
        for i, p in enumerate(nodes):
            o.write(f'{i+1} ' + ' '.join(f'{x:.17g}' for x in p) + '\n')
        o.write('$EndNodes\n$Elements\n' + str(len(elements)) + '\n')
        for i, (t, ns) in enumerate(elements):
            o.write(f'{i+1} {t} 0 ' + ' '.join(map(str, ns)) + '\n')
        o.write('$EndElements\n')


def read_msh(path):
    L = open(path).read().split('\n')
    n = int(L[4])
    nodes = np.array([list(map(float, l.split()[1:4])) for l in L[5:5 + n]])
    m = int(L[5 + n + 2])
    els = [list(map(int, l.split())) for l in L[5 + n + 3:5 + n + 3 + m]]
    return nodes, els


def circumcentre_xz(pts):
    """Circumcentre of the horizontal cross-section (same construction as cylinder_geometry.hh)."""
    a = pts[0]
    best, b, d = 0.0, None, None
    for j in range(1, len(pts)):
        for k in range(j + 1, len(pts)):
            p, q = pts[j] - a, pts[k] - a
            det = p[0] * q[1] - p[1] * q[0]
            if abs(det) > abs(best):
                best, b, d = det, p, q
    rb, rd = (b @ b) / 2, (d @ d) / 2
    return np.array([a[0] + (rb * d[1] - b[1] * rd) / best, a[1] + (b[0] * rd - rb * d[0]) / best])


def polygon_area(xz):
    x, z = xz[:, 0], xz[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(z, -1)) - np.dot(z, np.roll(x, -1)))


def audit(path, nr, nt, nz):
    """Independent Python geometry audit of a msh file (prism cells, vertical extrusion)."""
    nodes, els = read_msh(path)
    ys = np.unique(nodes[:, 1])
    vol = coarse = top = contact = 0.0
    min_inside_margin = np.inf
    max_circ_residual = 0.0
    cells = len(els)
    for e in els:
        t, ids = e[1], [v - 1 for v in e[3:]]
        P = nodes[ids]
        half = len(ids) // 2
        base = P[:half][:, [0, 2]]
        h = P[half:, 1].mean() - P[:half, 1].mean()
        if t == 5:
            order = base
        else:
            order = base
        A = polygon_area(order)
        c = circumcentre_xz(base)
        r = np.linalg.norm(base - c, axis=1)
        max_circ_residual = max(max_circ_residual, float((r.max() - r.min()) / r.mean()))
        # circumcentre must lie strictly inside the convex cross-section
        n = len(order)
        cross = [(order[(i + 1) % n][0] - order[i][0]) * (c[1] - order[i][1]) - (order[(i + 1) % n][1] - order[i][1]) * (c[0] - order[i][0]) for i in range(n)]
        cross = np.array(cross)
        sgn = np.sign(np.sum(cross))
        min_inside_margin = min(min_inside_margin, float(np.min(cross * sgn)))
        vol += A * h
        if c[0] < XC:
            coarse += A * h
        if P[half:, 1].max() > H - 1e-12:
            top += A
        # contact faces: two vertices with x==XC on each level and cell on coarse side
        on = np.abs(P[:, 0] - XC) < 1e-12
        if on.sum() == 4 and c[0] < XC:
            q = P[on]
            zs = np.unique(np.round(q[:, 2], 15))
            contact += (zs.max() - zs.min()) * h
    poly = nt / 2 * R * R * math.sin(2 * math.pi / nt)
    d = np.diff(ys)
    res = {
        'file': str(path), 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest(),
        'radial_layers': nr, 'angular_sectors': nt, 'vertical_layers': nz,
        'cells': cells, 'expected_cells': nr * nt * nz,
        'volume_m3': vol, 'coarse_volume_fraction': coarse / vol,
        'top_area_m2': top, 'polygon_area_formula_m2': poly, 'circle_area_m2': math.pi * R * R,
        'water_flux_area_correction': math.pi * R * R / poly,
        'contact_area_m2': contact, 'contact_area_expected_m2': 2 * R * H,
        'max_circumcentre_radius_spread_rel': max_circ_residual,
        'min_circumcentre_inside_margin_m2': min_inside_margin,
        'bottom_layer_mm': d[0] * 1e3, 'top_layer_mm': d[-1] * 1e3, 'vertical_ratio': float(d[1] / d[0]),
        'top_3mm_layers': int(np.sum(ys > H - 0.003 + 1e-12)),
        'layer_boundaries_near_3mm_mm': [float((H - y) * 1e3) for y in ys if abs(H - y - 0.003) < 0.0015],
    }
    ok = (cells == nr * nt * nz and abs(top - poly) < 1e-15 * 1e3 and abs(contact - 2 * R * H) < 1e-12
          and abs(coarse / vol - 0.5) < 1e-10 and min_inside_margin > 0 and max_circ_residual < 1e-9)
    res['status'] = 'passed' if ok else 'failed'
    return res


if __name__ == '__main__':
    nr, nt, nz = map(int, sys.argv[1:4])
    out, js = sys.argv[4], sys.argv[5]
    ys, nodes, elements = build(nr, nt, nz)
    write_msh(out, nodes, elements)
    r = audit(out, nr, nt, nz)
    r['generator_sha256'] = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
    with open(js, 'w') as f:
        json.dump(r, f, indent=2)
    print(json.dumps(r, indent=2))
    if r['status'] != 'passed':
        sys.exit(1)
