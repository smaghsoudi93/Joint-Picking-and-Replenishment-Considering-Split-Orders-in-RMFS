# -*- coding: utf-8 -*-
"""instance_generator.py -- generate random RMFS instances matching the
calibration of the paper's benchmark set.

Calibration rules derived from the 15 original instances:
  * station capacity  : statC   = ceil(1.12 * total_demand / nps)      (~12% slack)
  * bulk order       : size    = ceil(1.08 * statC)   -> forces exactly one split
  * replenishment cap : replC   = ceil(1.355 * total_demand / (nrs * waves))
  * pod capacity      : podC    = taken from the size table (as in the originals)
  * remaining orders  : drawn around the original mean order size for that size

Usage:
    python instance_generator.py --size 30 --seed 7 --out Data_o30_s7.xlsx
    python instance_generator.py --all --seeds 10 --outdir instances/
"""
import argparse, math, os
import numpy as np
import openpyxl

# (orders): items, shelves, nps, nrs, waves, pod_cap, mean_small_order
SPEC = {
 10:  (5,  2, 3, 2, 4,  42, 17.0),
 20:  (7,  2, 4, 3, 5,  85, 23.9),
 30:  (8,  3, 4, 3, 5, 106, 29.2),
 40:  (8,  3, 5, 3, 6, 104, 27.9),
 50:  (10, 3, 5, 4, 6, 156, 33.3),
 60:  (10, 3, 6, 4, 6, 183, 34.2),
 70:  (10, 3, 6, 4, 6, 215, 34.4),
 80:  (11, 4, 7, 4, 6, 192, 37.0),
 90:  (11, 4, 7, 5, 6, 215, 36.7),
 100: (12, 4, 8, 5, 6, 258, 40.7),
 110: (12, 4, 8, 5, 6, 283, 40.6),
 120: (12, 4, 9, 5, 6, 305, 40.9),
 130: (12, 4, 9, 5, 6, 322, 39.8),
 140: (12, 4, 10, 5, 6, 340, 39.6),
 150: (12, 4, 10, 5, 6, 379, 41.2),
}
MAX_ITER = {10:50, 20:50, 30:100, 40:50, 50:50, 60:50, 70:50, 80:50, 90:50,
            100:50, 110:50, 120:50, 130:50, 140:50, 150:50}

def is_structurally_feasible(inst):
    """Two necessary conditions for any feasible solution:
    (1) every order line fits into one picking station (lines are not split), and
    (2) the pods over all waves can hold the total demand."""
    D = inst['D']
    return (int(D.max()) <= inst['station_cap'] and
            inst['waves'] * inst['shelves'] * inst['pod_cap'] >= int(D.sum()))

def generate(n_orders, seed):
    """Draw instance `seed`; if it violates a necessary feasibility condition it is
    discarded and redrawn with a derived seed."""
    for attempt in range(100):
        inst = _draw(n_orders, seed if attempt == 0 else seed + 100000 * attempt)
        if is_structurally_feasible(inst):
            inst['redraws'] = attempt
            return inst
    raise RuntimeError(f'no feasible instance for o{n_orders} seed {seed}')

def _draw(n_orders, seed):
    """Return a dict with all fields of one random instance."""
    items, shelves, nps, nrs, waves, pod_cap, mean_small = SPEC[n_orders]
    rng = np.random.default_rng(seed)

    # 1) draw the n-1 "normal" orders around the historical mean size
    #    (lognormal-ish spread, clipped to a sensible band)
    lo, hi = max(5, int(mean_small*0.45)), int(mean_small*1.75)
    small = rng.integers(lo, hi+1, size=n_orders-1)
    small_total = int(small.sum())

    # 2) solve for the bulk order so the calibration holds:
    #    statC = ceil(1.12*(small_total+bulk)/nps)  and  bulk = ceil(1.08*statC)
    #    => bulk ≈ 1.08*1.12*(small_total+bulk)/nps  -> closed form
    k = 1.08 * 1.12 / nps
    bulk = int(math.ceil(k * small_total / (1 - k)))
    total = small_total + bulk
    statC = int(math.ceil(1.12 * total / nps))
    # enforce the bulk strictly exceeds one station (forced split)
    bulk = max(bulk, statC + 1)
    total = small_total + bulk
    statC = int(math.ceil(1.12 * total / nps))
    if bulk <= statC:                      # re-tighten if rounding flipped it
        bulk = statC + 1
        total = small_total + bulk

    replC = int(math.ceil(1.355 * total / (nrs * waves)))

    # 3) spread each order's quantity over a random subset of SKUs
    D = np.zeros((n_orders, items), dtype=int)
    def spread(row, qty):
        k = int(rng.integers(max(2, items//2), items+1))
        cols = rng.choice(items, size=k, replace=False)
        cuts = np.sort(rng.choice(np.arange(1, qty), size=k-1, replace=False)) if qty > k else None
        if cuts is None:
            base = qty//k; parts=[base]*k; parts[0]+=qty-base*k
        else:
            parts = np.diff(np.concatenate(([0], cuts, [qty]))).tolist()
        for c, p in zip(cols, parts):
            D[row, c] = int(p)
    spread(0, bulk)                        # order 0 is the bulk one
    for i, q in enumerate(small, start=1):
        spread(i, int(q))

    assert D.sum(axis=1)[0] == bulk
    assert D.sum() == total
    return dict(items=items, orders=n_orders, shelves=shelves, nps=nps, nrs=nrs,
                waves=waves, pod_cap=pod_cap, station_cap=statC, repl_cap=replC,
                max_iter=MAX_ITER[n_orders], sequences=3, D=D)

def write_xlsx(inst, path):
    """Write in the exact layout the solver expects (labels + blocks in col A)."""
    wb = openpyxl.Workbook(); sh = wb.active
    def put_scalar(row, label, value):
        sh.cell(row=row, column=1, value=label)
        sh.cell(row=row+1, column=1, value=int(value))
    put_scalar(1,  'items', inst['items'])
    put_scalar(4,  'orders1', inst['orders'])
    put_scalar(7,  'shelves', inst['shelves'])
    put_scalar(10, 'num_picking_stations', inst['nps'])
    put_scalar(13, 'num_replenishment_stations', inst['nrs'])
    put_scalar(16, 'waves', inst['waves'])
    put_scalar(19, 'Pods_capacity', inst['pod_cap'])
    put_scalar(22, 'group_capacity', inst['station_cap'])
    put_scalar(25, 'Replenishment_station_capacity', inst['repl_cap'])
    put_scalar(28, 'max_iterations', inst['max_iter'])
    put_scalar(31, 'sequences', inst['sequences'])
    D = inst['D']; n, m = D.shape
    # Demand, Demand1, matrix1 are identical copies in the originals
    start = 34
    for label in ('Demand', 'Demand1', 'matrix1'):
        sh.cell(row=start, column=1, value=label)
        for i in range(n):
            for j in range(m):
                sh.cell(row=start+1+i, column=1+j, value=int(D[i, j]))
        start += 1 + n + 1        # label + data + one blank row
    wb.save(path)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--size', type=int)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--outdir', default='instances')
    a = ap.parse_args()
    if a.all:
        os.makedirs(a.outdir, exist_ok=True)
        for n in sorted(SPEC):
            for s in range(a.seeds):
                inst = generate(n, s)
                write_xlsx(inst, os.path.join(a.outdir, f'Data_o{n}_s{s}.xlsx'))
        print(f'wrote {len(SPEC)*a.seeds} instances to {a.outdir}/')
    else:
        inst = generate(a.size, a.seed)
        write_xlsx(inst, a.out or f'Data_o{a.size}_s{a.seed}.xlsx')
        print('wrote', a.out or f'Data_o{a.size}_s{a.seed}.xlsx')
