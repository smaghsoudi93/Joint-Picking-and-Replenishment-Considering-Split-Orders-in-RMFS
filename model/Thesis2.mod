/*********************************************
 * OPL 22.1.0.0 Model
 * Joint optimization of picking and replenishment
 * considering split orders in RMFS
 * Author: Samaneh Maghsoudi
 *
 * Constraint labels refer to the equation numbers of the paper.
 *********************************************/

 int I  = ...;   // number of SKUs
 int o  = ...;   // number of orders
 int g  = ...;   // not used by the model (kept for compatibility with the data files)
 int p  = ...;   // number of pods
 int np = ...;   // number of picking stations
 int nr = ...;   // number of replenishment stations
 int C  = ...;   // capacity of a pod
 int Cp = ...;   // capacity of a picking station
 int Cr = ...;   // capacity of a replenishment station
 int w  = ...;   // number of replenishment waves
 int se = ...;   // not used by the model (kept for compatibility with the data files)

 int Wu    = 10;   // weight of unused picking-station capacity
 int alpha = 10;   // unit coordination cost

 // Big-M values derived from the instance parameters (Section 3):
 int Muv = minl(C, Cr);   // quantity replenished into a pod in a wave
 int Mqx = C;             // quantity picked from a pod in a wave

 range items                  = 1..I;
 range orders                 = 1..o;
 range shelves                = 1..p;
 range picking_stations       = 1..np;
 range replenishment_stations = 1..nr;
 range waves                  = 1..w;

 float demand[orders][items] = ...;   // quantity of SKU i requested in order o
 float t[waves] = ...;                // not used by the model (kept for compatibility with the data files)
 float d[waves] = ...;                // not used by the model (kept for compatibility with the data files)

 dvar boolean x[shelves][waves][picking_stations];                 // pod p visits picking station s in wave w
 dvar boolean y[items][orders][picking_stations];                  // SKU i of order o is picked at station s
 dvar boolean yy[orders][picking_stations];                        // order o is (partly) served at station s
 dvar int+    z[picking_stations];                                 // unused capacity of station s
 dvar boolean v[shelves][waves][replenishment_stations];           // pod p visits replenishment station r in wave w
 dvar int+    q[items][orders][shelves][waves][picking_stations];  // quantity of SKU i for order o picked from pod p (wave w) at station s
 dvar int+    u[items][shelves][waves][replenishment_stations];    // quantity of SKU i replenished into pod p in wave w by station r
 dvar int+    ff[items][waves][replenishment_stations];            // quantity of SKU i arriving in wave w at station r

 execute CPX_PARAM {
   cplex.tilim = 7200;
   cplex.epgap = 0;
   cplex.workmem = 4096;
   cplex.nodefileind = 3;
 }

 // (3.1)
 minimize
     sum(p in shelves, w in waves, s in picking_stations) x[p][w][s]
   + sum(p in shelves, w in waves, r in replenishment_stations) v[p][w][r]
   + sum(s in picking_stations) Wu * z[s]
   + alpha * (sum(o in orders, s in picking_stations) yy[o][s] - o);

subject to {

 // every order is counted at least once in the coordination term
 forall (o in orders)
  ctOrder:
  sum(s in picking_stations) yy[o][s] >= 1;

 // (3.2)
 forall (i in items, o in orders, s in picking_stations)
  ct3_2:
  yy[o][s] >= y[i][o][s];

 // (3.3)
 forall (o in orders, s in picking_stations)
  ct3_3:
  sum(i in items) y[i][o][s] >= yy[o][s];

 // (3.4)
 forall (o in orders, i in items : demand[o][i] > 0)
  ct3_4:
  sum(s in picking_stations) y[i][o][s] == 1;

 // (3.5)
 forall (s in picking_stations)
  ct3_5:
  sum(i in items, o in orders) demand[o][i] * y[i][o][s] + z[s] == Cp;

 // (3.6)
 forall (i in items, o in orders, s in picking_stations)
  ct3_6:
  sum(p in shelves, w in waves) x[p][w][s] >= y[i][o][s];

 // (3.7)
 forall (w in waves, r in replenishment_stations)
  ct3_7:
  sum(i in items, p in shelves) u[i][p][w][r] <= Cr;

 // (3.8)
 forall (p in shelves, w in waves)
  ct3_8:
  sum(r in replenishment_stations, i in items) u[i][p][w][r] <= C;

 // (3.9)
 forall (o in orders, i in items, s in picking_stations)
  ct3_9:
  demand[o][i] * y[i][o][s] == sum(w in waves, p in shelves) q[i][o][p][w][s];

 // (3.10)
 forall (w in waves, i in items, p in shelves)
  ct3_10:
  sum(r in replenishment_stations) u[i][p][w][r] == sum(o in orders, s in picking_stations) q[i][o][p][w][s];

 // (3.11)
 forall (i in items, r in replenishment_stations, w in waves)
  ct3_11:
  ff[i][w][r] == sum(p in shelves) u[i][p][w][r];

 // (3.12)
 forall (p in shelves, w in waves, r in replenishment_stations)
  ct3_12:
  sum(i in items) u[i][p][w][r] >= v[p][w][r];

 // (3.13)
 forall (p in shelves, w in waves, r in replenishment_stations)
  ct3_13:
  sum(i in items) u[i][p][w][r] <= Muv * v[p][w][r];

 // (3.14)
 forall (p in shelves, w in waves, s in picking_stations)
  ct3_14:
  sum(i in items, o in orders) q[i][o][p][w][s] <= Mqx * x[p][w][s];
}
