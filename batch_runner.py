# -*- coding: utf-8 -*-
"""batch_runner.py -- run the AO heuristic on many random instances.

For each (size, seed): generate the instance -> save it to generated_instances/
-> run Joint-Picking-and-Replenishment-Considering-Split-Orders.py on it (via the RMFS_DATA environment variable; your own
'Data2 - new.xlsx' is never touched) -> parse the result -> append one row to the
CSV immediately (a crash never loses finished runs; use --resume to continue).

Each row also stores an ANALYTIC LOWER BOUND, valid for every instance:
    LB = 2*ceil(D / C_pod)                      pod visits (pick + replenish, pods start empty)
       + alpha * sum_o max(0, ceil(d_o / C_st) - 1)   splits forced by oversized orders
       + Wu * (|S| * C_st - D)                   unused capacity (a constant)

USAGE (Windows, in the folder that contains Joint-Picking-and-Replenishment-Considering-Split-Orders.py):
    python batch_runner.py --sizes 10 20 30 40 50 60 --seeds 10 --alpha 10 --out set1.csv
    python batch_runner.py --sizes 70 80 90 100 110 120 130 140 150 --seeds 10 --alpha 10 --out set2.csv
    ...add --resume to continue after an interruption.
"""
import argparse, csv, math, os, re, subprocess, sys, time
from instance_generator import generate, write_xlsx

SOLVER = 'Joint-Picking-and-Replenishment-Considering-Split-Orders.py'
UNUSED_WEIGHT = 10
PAT_OBJ   = re.compile(r'\[AO FINAL\] converged objective\s*=\s*([0-9.eE+-]+)')
INFEASIBLE = 1e6   # the solver reports 10000000 (printed 1e+07) when no feasible solution exists
PAT_SPLIT = re.compile(r'extra splits\s*=\s*(\d+)')
PAT_SX    = re.compile(r'\(\u03a3x\)\s*=\s*(\d+)')
PAT_SV    = re.compile(r'\(\u03a3v\)\s*=\s*(\d+)')

def analytic_lb(inst, alpha):
    D = inst['D']; tot = int(D.sum()); st = inst['station_cap']
    forced = sum(max(0, math.ceil(int(s) / st) - 1) for s in D.sum(axis=1))
    unused = inst['nps'] * st - tot
    return 2 * math.ceil(tot / inst['pod_cap']) + alpha * forced + UNUSED_WEIGHT * unused, unused

def run_one(size, seed, alpha, ao_rounds, inst_dir):
    inst = generate(size, seed)
    os.makedirs(inst_dir, exist_ok=True)
    path = os.path.abspath(os.path.join(inst_dir, f'Data_o{size}_s{seed}.xlsx'))
    write_xlsx(inst, path)
    env = dict(os.environ, RMFS_DATA=path, RMFS_ALPHA=str(alpha), RMFS_AO_ROUNDS=str(ao_rounds),
               PYTHONIOENCODING='utf-8')
    t0 = time.time()
    p = subprocess.run([sys.executable, SOLVER], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    wall = time.time() - t0
    out = p.stdout
    os.makedirs('logs', exist_ok=True)
    with open(os.path.join('logs', f'o{size}_s{seed}.log'), 'w', encoding='utf-8') as f:
        f.write(out); f.write('\n--- STDERR ---\n'); f.write(p.stderr)
    obj = PAT_OBJ.findall(out); sp = PAT_SPLIT.findall(out)
    sx = PAT_SX.findall(out); sv = PAT_SV.findall(out)
    lb, unused = analytic_lb(inst, alpha)
    objv = float(obj[-1]) if obj else None
    good = objv is not None and objv < INFEASIBLE
    return {'size': size, 'seed': seed, 'alpha': alpha,
            'objective': objv if good else '', 'wall_s': round(wall, 1),
            'splits': int(sp[-1]) if sp else '', 'Sx': int(sx[-1]) if sx else '',
            'Sv': int(sv[-1]) if sv else '', 'lb_analytic': lb, 'unused_const': unused,
            'total_demand': int(inst['D'].sum()), 'ok': good}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sizes', type=int, nargs='+')
    ap.add_argument('--pairs', nargs='+', help='run only these size:seed pairs, e.g. 10:4 20:6')
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--alpha', type=int, required=True)
    ap.add_argument('--ao-rounds', type=int, default=5)
    ap.add_argument('--out', default='results.csv')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--inst-dir', default='generated_instances')
    a = ap.parse_args()
    done = set()
    if a.resume and os.path.exists(a.out):
        with open(a.out, newline='', encoding='utf-8') as f:
            done = {(int(r['size']), int(r['seed'])) for r in csv.DictReader(f) if r['ok'] == 'True'}
        print(f'resuming: {len(done)} runs already done')
    fields = ['size','seed','alpha','objective','wall_s','splits','Sx','Sv',
              'lb_analytic','unused_const','total_demand','ok']
    new = not os.path.exists(a.out)
    with open(a.out, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new: w.writeheader()
        jobs = ([tuple(int(x) for x in p.split(':')) for p in a.pairs] if a.pairs
                else [(sz, sd) for sz in a.sizes for sd in range(a.seeds)])
        for size, seed in jobs:
                if (size, seed) in done: continue
                print(f'--- o{size} seed {seed} ---', flush=True)
                row = run_one(size, seed, a.alpha, a.ao_rounds, a.inst_dir)
                w.writerow(row); f.flush()
                print(f"    obj={row['objective']} LB={row['lb_analytic']} splits={row['splits']} "
                      f"t={row['wall_s']}s ok={row['ok']}", flush=True)
                if not row['ok']:
                    print(f'    !! no result -- see logs/o{size}_s{seed}.log', flush=True)
    print('done ->', a.out)

if __name__ == '__main__':
    main()
