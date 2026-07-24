# Joint Optimization of Order Picking and Replenishment in Robotic Mobile Fulfillment Systems

This repository contains the model, algorithms, benchmark instances, and analysis
scripts accompanying the paper *"Joint Optimization of Order Picking and
Replenishment in Robotic Mobile Fulfillment Systems under a Split-Order Policy."*

The work studies a robotic mobile fulfillment system (RMFS) in which customer
orders may be split across several picking stations. Order splitting is priced
through an explicit **coordination cost**, and picking and replenishment are
optimized jointly. Because the resulting mixed-integer program is NP-hard and
does not scale, a four-phase heuristic (order-aware clustering → cluster-to-station
assignment → wave planning → Variable Neighborhood Search) is proposed and
evaluated against CPLEX and two baselines.

## Repository structure

| File | Description |
|------|-------------|
| `Joint-Picking-and-Replenishment-Considering-Split-Orders.py` | Main four-phase heuristic (Phases 1–3 + VNS). Reads an instance from `Data_o10.xlsx` to Data_o150.xlsx` and reports the objective, splits, pod visits, and run time. |
| `sequential_baselinee.py` | Sequential (hierarchical) planning baseline: capacity-only first-fit assignment, then the same downstream evaluation. |
| `random_baseline.py` | Random-assignment baseline (10 replications) used to quantify the value of the co-occurrence-based clustering. |
| `alpha_sensitivity.py` | Sensitivity sweep over the coordination weight α; writes `alpha_sensitivity_results.csv` and the Fig. 3 plots. |
| `Data/` | The fifteen benchmark instances (`.xlsx`), for 10 to 150 orders. |
| `requirements.txt` | Python dependencies. |

## Requirements

- **Python 3.7**
- **IBM ILOG CPLEX Optimization Studio 22.1**, with the matching `docplex` Python
  package. CPLEX is commercial software; a free
  [academic license](https://www.ibm.com/academic/) is available. The Python
  packages alone are not sufficient — a working CPLEX installation is required
  to solve the models.
- Remaining Python dependencies are listed in `requirements.txt`.

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

## Reproducing the results

Each script expects the target instance to be named `Data_o10.xlsx` in the
working directory. To run a given instance, copy the desired file from
`instances/` to `Data_o10.xlsx` and then run the script, e.g.:

```bash
cp "instances/Data_o10.xlsx" "Data_o10.xlsx"
python Joint-Picking-and-Replenishment-Considering-Split-Orders.py
```

- **Table 3** (proposed algorithm vs. CPLEX): run `Joint-Picking-and-Replenishment-Considering-Split-Orders` on
  each instance; run the exact model with OPL for the CPLEX column.
- **Table 4** (vs. sequential baseline): run `sequential_baselinee.py` on each
  instance.
- **Table 5** (vs. random baseline): run `random_baseline.py` on each instance.
- **Fig. 3** (α sensitivity): run `alpha_sensitivity.py`.

The exact model is solved with a two-hour time limit; the heuristic solves each
instance in seconds to minutes.

## Notes

- All objective coefficients are integer-valued. During the VNS search, candidate
  subproblems are solved with an objective cutoff at the incumbent cost; the
  initial and final reported solutions are evaluated exactly.
- Benchmark instances are generated with a fixed random seed for full
  reproducibility.

## Citation

If you use this code or data, please cite the paper. (Full bibliographic details
will be added upon publication.)
