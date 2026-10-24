# Joint Optimization of Picking and Replenishment Considering Split Orders in Robotic Mobile Fulfillment Systems

This repository contains the model, algorithms, benchmark instances, random test
instances, and analysis scripts accompanying the paper *"Joint Optimization of
Picking and Replenishment Considering Split Orders in Robotic Mobile Fulfillment
Systems."*

The work studies a robotic mobile fulfillment system (RMFS) in which customer
orders may be split across several picking stations. Order splitting is priced
through an explicit **coordination cost**, and picking and replenishment are
optimized jointly. Because the resulting mixed-integer program does not scale,
a heuristic is proposed: order-aware clustering → cluster-to-station assignment
→ wave planning → Variable Neighborhood Search, embedded in an **alternating
optimization (AO)** loop that alternates between the allocation step (VNS with
replenishment fixed) and the location step (replenishment variables optimized
freely by CPLEX for the given assignment).

## Repository structure

| File / folder | Description |
|---------------|-------------|
| `Joint-Picking-and-Replenishment-Considering-Split-Orders.py` | Main algorithm (clustering, assignment, wave planning, VNS, alternating optimization). Reports the objective, splits, pod visits, and run time. |
| `sequential_baseline.py` | Sequential (hierarchical) planning baseline: capacity-only first-fit assignment, then the same downstream evaluation. |
| `random_baseline.py` | Random-assignment baseline (10 replications) used to quantify the value of the co-occurrence-based clustering. |
| `alpha_sensitivity.py` | Sensitivity analysis over the coordination weight α. |
| `instance_generator.py` | Generator of random instances calibrated on the fifteen benchmark instances. |
| `batch_runner.py` | Runs the algorithm on many generated instances and records the objective, run time, splits, and an analytic lower bound. |
| `summarize_batch.py` | Aggregates the batch results per instance size (mean, standard deviation, gap to the lower bound). |
| `model/` | Exact MIP model in IBM ILOG OPL (`Thesis2.mod`) and the fifteen benchmark instances as OPL data files (`Instance_o{orders}.dat`). |
| `Data_o{orders}.xlsx` | The fifteen benchmark instances (10 to 150 orders) as input files for the Python scripts; identical to the `.dat` files. |
| `generated_instances/` | The 150 random instances (15 sizes × 10 seeds), `Data_o{orders}_s{seed}.xlsx`. |
| `results/robustness_results.csv` | Results of the algorithm on the 150 random instances. |
| `requirements.txt` | Python dependencies. |

## Requirements

- **Python 3.7** or later
- **IBM ILOG CPLEX Optimization Studio 22.1**, with the matching `docplex` Python
  package. CPLEX is commercial software; a free
  [academic license](https://www.ibm.com/academic/) is available. The Python
  packages alone are not sufficient — a working CPLEX installation is required
  to solve the models.
- Remaining Python dependencies are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Configuration

`alpha_sensitivity.py` reads `Data2 - new.xlsx` from the working directory (copy
the desired `Data_o{orders}.xlsx` to that name). The other scripts read three
optional environment variables:

| Variable | Meaning | Default |
|----------|---------|---------|
| `RMFS_DATA` | Instance file to solve | `Data2 - new.xlsx` |
| `RMFS_ALPHA` | Coordination weight α | `10` |
| `RMFS_AO_ROUNDS` | Maximum number of AO rounds | `5` |

Example (Linux/macOS):

```bash
RMFS_DATA="Data_o50.xlsx" python Joint-Picking-and-Replenishment-Considering-Split-Orders.py
```

Example (Windows PowerShell):

```powershell
$env:RMFS_DATA = "Data_o50.xlsx"; python Joint-Picking-and-Replenishment-Considering-Split-Orders.py
```

## Reproducing the results

- **Table 3** (proposed algorithm vs. CPLEX): run `Joint-Picking-and-Replenishment-Considering-Split-Orders.py` on each
  benchmark instance `Data_o{orders}.xlsx`; for the CPLEX column, solve
  `model/Thesis2.mod` with the matching `model/Instance_o{orders}.dat` in
  IBM ILOG CPLEX Optimization Studio (two-hour time limit).
- **Table 4** (ten random instances per size):
  ```bash
  python batch_runner.py --sizes 10 20 30 40 50 60 --seeds 10 --alpha 10 --ao-rounds 1 --out set1.csv
  python batch_runner.py --sizes 70 80 90 100 110 120 130 140 150 --seeds 10 --alpha 10 --ao-rounds 1 --out set2.csv
  python summarize_batch.py set1.csv set2.csv
  ```
  The instances are regenerated deterministically from their seeds and are also
  provided in `generated_instances/`; the results are in
  `results/robustness_results.csv`.
- **Table 5** (vs. sequential baseline): run `sequential_baseline.py` on each
  benchmark instance.
- **Table 6** (vs. random baseline): run `random_baseline.py` on each benchmark
  instance.
- **α sensitivity**: run `alpha_sensitivity.py` on the 30-order instance.

## Random instances

`instance_generator.py` reproduces the calibration of the benchmark set: the
picking-station capacity is set to about 1.12 times the average demand per
station, each instance contains one bulk order of 1.08 times the station
capacity, and the replenishment capacity, pod capacity, and dimensions follow
the benchmark instances of the same size. An instance that is structurally
infeasible (a single order line larger than a station, or total pod capacity
below total demand) is redrawn with a derived seed.

```bash
python instance_generator.py --size 30 --seed 7 --out Data_o30_s7.xlsx
python instance_generator.py --all --seeds 10 --outdir generated_instances
```

## Notes

- All objective coefficients are integer-valued. During the VNS search, candidate
  subproblems are solved with an objective cutoff at the incumbent cost; the
  initial and final reported solutions are evaluated exactly.
- A fixed random seed is used in all experiments for full reproducibility.

## Citation

If you use this code or data, please cite the paper. (Full bibliographic details
will be added upon publication.)
