# -*- coding: utf-8 -*-
"""summarize_batch.py -- build the Set 1 / Set 2 tables from batch_runner CSVs.

    python summarize_batch.py set1.csv set2.csv
    python summarize_batch.py set1.csv set2.csv --cplex cplex_set1.csv

Per size: runs, mean/std/min/max objective, mean time, mean splits, mean gap to
the analytic lower bound on the TOTAL objective and on the DECISION part
(objective minus the constant unused-capacity term, i.e. pod visits + coordination).
Optional cplex csv columns: size,seed,objective,bound,time  -> adds CPLEX columns.
"""
import argparse, csv, statistics as st
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csvs', nargs='+'); ap.add_argument('--cplex')
    a = ap.parse_args()
    rows = []
    for p in a.csvs:
        with open(p, newline='', encoding='utf-8') as f:
            rows += [r for r in csv.DictReader(f) if r['ok'] == 'True']
    cp = {}
    if a.cplex:
        with open(a.cplex, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                cp[(int(r['size']), int(r['seed']))] = r
    by = defaultdict(list)
    for r in rows: by[int(r['size'])].append(r)
    hdr = (f"{'n':>4} {'runs':>4} {'mean obj':>9} {'std':>7} {'min':>7} {'max':>7} {'t(s)':>7} "
           f"{'splits':>6} {'gapLB%':>7} {'gapDec%':>7}")
    if cp: hdr += f" {'CPLEX obj':>9} {'CPLEX t':>7} {'CPLEX gap%':>10}"
    print(hdr); print('-' * len(hdr))
    for n in sorted(by):
        g = by[n]; obj = [float(r['objective']) for r in g]
        lb = [float(r['lb_analytic']) for r in g]; zz = [10 * float(r['unused_const']) for r in g]
        gap = [(o - l) / l * 100 for o, l in zip(obj, lb)]
        dec = [(o - l) / (l - z) * 100 for o, l, z in zip(obj, lb, zz) if l - z > 0]
        line = (f"{n:>4} {len(g):>4} {st.mean(obj):>9.1f} {(st.stdev(obj) if len(obj) > 1 else 0):>7.1f} "
                f"{min(obj):>7.0f} {max(obj):>7.0f} {st.mean(float(r['wall_s']) for r in g):>7.0f} "
                f"{st.mean(float(r['splits'] or 0) for r in g):>6.2f} {st.mean(gap):>6.2f}% {st.mean(dec):>6.2f}%")
        if cp:
            c = [cp[(n, int(r['seed']))] for r in g if (n, int(r['seed'])) in cp]
            if c:
                line += (f" {st.mean(float(x['objective']) for x in c):>9.1f} "
                         f"{st.mean(float(x['time']) for x in c):>7.0f} "
                         f"{st.mean((float(x['objective']) - float(x['bound'])) / float(x['objective']) * 100 for x in c):>9.2f}%")
        print(line)

if __name__ == '__main__':
    main()
