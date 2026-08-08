#!/usr/bin/env python3
"""Generate pgfplots figures (paper/figures_auto.tex) from sim/results CSVs.

Stdlib-only. Produces vector TikZ/pgfplots figures that compile with the
paper's existing LaTeX toolchain (no matplotlib). Re-run after new sim
results to refresh the figures.

    python3 figs/make_figures.py
"""
from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "sim", "results")
OUT = os.path.join(ROOT, "paper", "figures_auto.tex")


def load(name):
    with open(os.path.join(RESULTS, name)) as f:
        return list(csv.DictReader(f))


def coords(rows, x, y, ci=None):
    out = []
    for r in rows:
        s = f"({float(r[x])},{float(r[y])})"
        if ci:
            s += f" +- (0,{float(r[ci])})"
        out.append(s)
    return " ".join(out)


def fig_e2():
    rows = load("e2_aoi_paoi.csv")
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.66\columnwidth,
  xlabel={{duty cycle $\delta$}},ylabel={{age (normalized, $P{{=}}1$)}},
  legend style={{at={{(0.5,-0.26)}},anchor=north,legend columns=2}},
  error bars/y dir=both,error bars/y explicit]
\addplot[cA,only marks,mark=*,mark size=1.5pt] coordinates {{{coords(rows,'delta','paoi','paoi_ci')}}};
\addlegendentry{{OPAoI (sim)}}
\addplot[cA,no marks,thick,dashed] coordinates {{{coords(rows,'delta','paoi_cf')}}};
\addlegendentry{{OPAoI $=T_s+P(1-\delta)$}}
\addplot[cB,only marks,mark=square*,mark size=1.5pt] coordinates {{{coords(rows,'delta','aoi','aoi_ci')}}};
\addlegendentry{{mean AoI (sim)}}
\addplot[cB,no marks,thick,densely dotted] coordinates {{{coords(rows,'delta','aoi_cf')}}};
\addlegendentry{{mean AoI $=T_s+\tfrac{{P}}{{2}}(1-\delta)^2$}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Result~1 (E1/E2): simulated mean AoI and OPAoI vs.\ duty cycle
match the closed forms; the peak grows linearly and the mean
quadratically in $(1-\delta)$ (provisioning divergence). Markers are
Monte-Carlo means with 95\% CIs (smaller than markers).}}
\label{{fig:r1}}
\end{{figure}}
"""


def fig_e4():
    rows = load("e4_k2_gain.csv")
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{duty cycle $\delta$}},ylabel={{$\mathbb{{E}}[R_{{\min}}]/\mathbb{{E}}[R]$}},
  legend pos=north east,grid=both,legend cell align=left]
\addplot[cA,only marks,mark=*,mark size=1.6pt] coordinates {{{coords(rows,'delta','ratio')}}};
\addlegendentry{{sim}}
\addplot[cB,no marks,thick,dashed] coordinates {{{coords(rows,'delta','ratio_cf')}}};
\addlegendentry{{$\tfrac{{2}}{{3}}(1-\delta)$}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Result~2 (E4): the two-copy gain. Simulated
$\mathbb{{E}}[R_{{\min}}]/\mathbb{{E}}[R]$ matches the two-copy
ratio $\tfrac{{2}}{{3}}(1-\delta)$; replication saves most at sparse
contacts ($\delta\to0$).}}
\label{{fig:r2gain}}
\end{{figure}}
"""


def fig_e7():
    rows = load("e7_threshold.csv")
    series = {}
    for r in rows:
        series.setdefault(r["eta"], []).append((float(r["k"]), float(r["mean_paoi"])))
    plots = []
    styles = ["cA,mark=*", "cB,mark=square*", "cC,mark=triangle*", "cD,mark=diamond*"]
    for i, (eta, pts) in enumerate(sorted(series.items(), key=lambda kv: float(kv[0]))):
        pts.sort()
        c = " ".join(f"({k},{y})" for k, y in pts)
        st = styles[i % len(styles)]
        plots.append(rf"\addplot[thick,{st},mark size=1.3pt] coordinates {{{c}}};")
        plots.append(rf"\addlegendentry{{$\eta={float(eta):.0f}$ ($k^\ast={int(round(float(eta)))}$)}}")
    body = "\n".join(plots)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.66\columnwidth,
  xlabel={{replication degree $k$}},ylabel={{mean $\PAoIper$ (normalized)}},
  legend pos=north west,grid=both,legend cell align=left,xtick=data]
{body}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Result~3 (E7): the integrated energy+replication+AoI objective
is unimodal in $k$ with minimum at one of the two integers bracketing
$\eta$; pushing
$k$ past the energy budget starves future contacts and raises the peak.}}
\label{{fig:r3unimodal}}
\end{{figure}}
"""


def fig_e8():
    rows = load("e8_monotonicity.csv")
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{energy-adequacy ratio $\eta=\lambda_e P/e$}},ylabel={{optimal degree $k^\ast$}},
  legend pos=south east,grid=both,legend cell align=left,ymin=0]
\addplot[cB,no marks,thick,dashed,const plot] coordinates {{{coords(rows,'eta','k_star_cf')}}};
\addlegendentry{{$\min(K_{{\max}},\lfloor\eta\rfloor)$}}
\addplot[cA,only marks,mark=*,mark size=1.7pt] coordinates {{{coords(rows,'eta','k_star')}}};
\addlegendentry{{sim}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Result~3 (E8): $k^\ast(\eta)$ is non-decreasing in the
harvest-to-contact ratio and saturates at $K_{{\max}}{{=}}8$ once energy
ceases to bind.}}
\label{{fig:r3kstar}}
\end{{figure}}
"""


def fig_e11():
    rows = load("e11_finite_battery.csv")
    series = {}
    for r in rows:
        series.setdefault(r["eta"], []).append((float(r["B"]), float(r["k_star"])))
    plots = []
    styles = ["mark=*", "mark=square*"]
    for i, (eta, pts) in enumerate(sorted(series.items(), key=lambda kv: float(kv[0]))):
        pts.sort()
        c = " ".join(f"({b},{k})" for b, k in pts)
        plots.append(rf"\addplot[thick,{styles[i%2]},mark size=1.4pt] coordinates {{{c}}};")
        plots.append(rf"\addlegendentry{{$\eta={float(eta):.0f}$}}")
    body = "\n".join(plots)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{battery capacity $B$ (copies)}},ylabel={{optimal degree $k^\ast$}},
  legend pos=south east,grid=both,legend cell align=left,xmode=log,log basis x=2,ymin=0]
{body}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Hardening (E11): finite battery lowers $p_e$ (overflow loss),
pressing the optimal degree downward as $B$ shrinks---a quantified
downward pressure, not a hard $\lfloor\eta\rfloor$ ceiling.}}
\label{{fig:r3finiteB}}
\end{{figure}}
"""


def fig_e12():
    rows = load("e12_inversion.csv")
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{gap coefficient of variation $\mathrm{{CV}}(V)$}},
  ylabel={{age (normalized)}},legend pos=north west,grid=both,
  legend cell align=left]
\addplot[cB,only marks,mark=square*,mark size=1.7pt] coordinates {{{coords(rows,'cv','mean_aoi')}}};
\addlegendentry{{mean AoI}}
\addplot[cA,only marks,mark=*,mark size=1.7pt] coordinates {{{coords(rows,'cv','mean_paoi')}}};
\addlegendentry{{mean OPAoI}}
\draw[gray,dashed] (axis cs:1.106,\pgfkeysvalueof{{/pgfplots/ymin}}) -- (axis cs:1.106,\pgfkeysvalueof{{/pgfplots/ymax}});
\end{{axis}}
\end{{tikzpicture}}
\caption{{The AoI/OPAoI inversion (E12). Mean OPAoI ($=T_s+
\mathbb{{E}}[V]$) is flat in the gap variability, while mean AoI grows
with it; they cross at the exact threshold
$\mathrm{{CV}}^2(V)=1+2\mathbb{{E}}[U]/\mathbb{{E}}[V]$ (dashed:
$\mathrm{{CV}}\approx1.11$ for the plotted $\mathbb{{E}}[U]/\mathbb{{E}}[V]=1/9$),
so for high-variance
terrestrial contacts the outage peak sits {{\itshape below}}
average AoI.}}
\label{{fig:inversion}}
\end{{figure}}
"""


def load_tier2(name):
    with open(os.path.join(ROOT, "sim", "tier2", "results", name)) as f:
        return list(csv.DictReader(f))


def fig_r3_tier2():
    rows = load_tier2("r3_sweep.csv")
    P = 5736.0  # relay period; normalize PAoI to periods
    def coords(col, cicol):
        return " ".join(f"({float(r['eta'])},{float(r[col])/P:.3f}) +- (0,{float(r[cicol])/P:.3f})"
                        for r in rows)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{energy-adequacy ratio $\eta$ (harvest per update $/\,e$)}},
  ylabel={{mean OPAoI (periods $P$)}},
  legend style={{at={{(0.97,0.52)}},anchor=east}},
  error bars/y dir=both,error bars/y explicit]
\addplot[cB,thick,mark=square*,mark size=1.6pt] coordinates {{{coords('k1_paoi','k1_paoi_ci')}}};
\addlegendentry{{single-copy CGR}}
\addplot[cA,thick,mark=*,mark size=1.6pt] coordinates {{{coords('k2_paoi','k2_paoi_ci')}}};
\addlegendentry{{CGR $k{{=}}2$ (this work)}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Replication benefit in a real CGR stack with our CGR-native
$k$-copy router (dtnsim, random relay faults, source energy gate; 10
seeds, 95\% CIs). Sending two copies over the two best distinct CGR
routes cuts mean OPAoI by roughly $6\times$ versus single-copy across the
whole energy range---the order statistic hedges relay faults. Because the
per-transmission energy gate defers the second copy when the battery is
low (rather than dropping the update), the benefit degrades gracefully as
$\eta$ falls instead of inverting. This experiment isolates the
fault-hedging \emph{{mechanism}}; it is not a test of the atomic
all-or-nothing policy of \eqref{{eq:kstar}}, whose over-replication
penalty appears in Fig.~\ref{{fig:r3atomic}}.}}
\label{{fig:r3tier2}}
\end{{figure}}
"""


def fig_r3_atomic():
    rows = load_tier2("r3_atomic.csv")
    P = 5736.0
    series = {}
    for r in rows:
        series.setdefault(float(r["eta"]), []).append((int(float(r["k"])), float(r["paoi_mean"]) / P))
    plots = []
    styles = ["cA,mark=*", "cB,mark=square*", "cC,mark=triangle*", "cD,mark=diamond*",
              "cE,mark=pentagon*", "cA,mark=o"]
    for i, (eta, pts) in enumerate(sorted(series.items())):
        if eta not in (0.6, 1.0, 2.0, 3.0):
            continue
        pts.sort()
        c = " ".join(f"({k},{v:.3f})" for k, v in pts)
        plots.append(rf"\addplot[thick,{styles[i%6]},mark size=1.6pt] coordinates {{{c}}};")
        plots.append(rf"\addlegendentry{{$\eta={eta:g}$}}")
    body = "\n".join(plots)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.62\columnwidth,
  xlabel={{replication degree $k$ (atomic all-or-nothing admission)}},
  ylabel={{mean OPAoI (periods $P$)}},legend pos=north west,grid=both,
  legend cell align=left,xtick={{1,2,3}}]
{body}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Tier-2 atomic threshold test (real CGR, fault-free
3-relay staggered diamond, update-atomic admission: launch $k$ copies
iff the battery holds $k$ units, else skip the whole update; 5 seeds).
The over-replication penalty is now visible in the DTN stack:
at $\eta{{=}}1$, $k{{=}}3$ admits $35\%$ of updates (theory
$\min(1,\eta G_{{\mathrm{{gen}}}}/kP)$, matched to $<0.5\%$) and its
peak age is $2.7\times$ single-copy's. At $\eta\ge3$ the degrees tie
exactly: with a fault-free deterministic plan, oracle CGR's single copy
already rides the earliest route, so extra copies deliver stale
duplicates---the strict replication benefit requires route-outcome
uncertainty (Fig.~\ref{{fig:r3tier2}}).}}
\label{{fig:r3atomic}}
\end{{figure}}
"""


def fig_robust():
    rows = load("robust_kstar.csv")
    full = " ".join(f"({float(r['alpha'])},{float(r['paoi_full'])})" for r in rows)
    res = " ".join(f"({float(r['alpha'])},{float(r['paoi_reserve'])})" for r in rows)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{contact-prediction reliability $\alpha$}},
  ylabel={{mean $\PAoIper$ (normalized)}},legend pos=north east,grid=both,
  legend cell align=left,x dir=reverse]
\addplot[thick,mark=*,mark size=1.4pt] coordinates {{{full}}};
\addlegendentry{{keep $k{{=}}\lfloor\eta\rfloor$ (our rule)}}
\addplot[thick,dashed,mark=square*,mark size=1.4pt] coordinates {{{res}}};
\addlegendentry{{reserve $k{{=}}\lfloor\alpha\eta\rfloor$}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Robustness to contact-prediction error ($\eta{{=}}6$; $x$ axis
reversed so error grows rightward). The PAoI-optimal degree stays at the
energy ceiling $\lfloor\eta\rfloor$ for all $\alpha$: extra copies hedge
missed contacts via the order statistic, so our rule degrades gracefully
($+19\%$ PAoI as $\alpha$ falls to $0.4$). The intuitive reserve heuristic
$\lfloor\alpha\eta\rfloor$ \emph{{under-replicates}} and is counterproductive
($+50\%$ PAoI at $\alpha{{=}}0.4$)---replication is the right response to
prediction uncertainty, not a smaller copy budget.}}
\label{{fig:robust}}
\end{{figure}}
"""


def fig_hetero():
    rows = load_tier2("hetero_battery.csv")
    P = 5736.0
    c = " ".join(f"({float(r['B'])},{float(r['paoi'])/P:.3f})" for r in rows)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{relay battery capacity $B$ (copies)}},
  ylabel={{end-to-end mean OPAoI (periods $P$)}},grid=both,
  xmode=log,log basis x=2,legend pos=north east,legend cell align=left]
\addplot[cA,thick,mark=*,mark size=1.5pt] coordinates {{{c}}};
\addlegendentry{{heterogeneous chain}}
\addplot[cC,thick,dashed,no marks] coordinates {{(4,1.802) (64,1.802)}};
\addlegendentry{{energy-unconstrained}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Energy coupling in the full heterogeneous chain (sensor $\to$ UAV
mule $\to$ LEO $\to$ gateway in real CGR). A finite battery at the UAV/LEO
relays must cover the per-contact forwarding burst; below that, end-to-end
mean OPAoI degrades by $\sim\!11\times$ (and delivery collapses from $96\%$
to $31\%$). With sufficient battery it matches the energy-unconstrained
chain, whose mean delay confirms the additive composition
$\E[Y]{{=}}\E[R_1]{{+}}\E[R_2]{{+}}\E[R_3]$ to $1.1\%$.}}
\label{{fig:hetero}}
\end{{figure}}
"""


def fig_rucop():
    rows = load("rucop_frontier.csv")
    front = " ".join(f"({float(r['energy'])},{float(r['delivery'])})" for r in rows)
    by_k = {int(float(r['k'])): float(r['delivery']) for r in rows}
    kmax = max(by_k)
    pts = {1: "single-copy CGR", 2: "AoI-Energy policy ($\\eta{=}2$)", kmax: "RUCoP (delivery-opt.)"}
    marks = []
    styles = {1: "mark=triangle*", 2: "mark=*", kmax: "mark=square*"}
    for k, lab in pts.items():
        marks.append(rf"\addplot[only marks,{styles[k]},mark size=2.6pt] coordinates {{({k},{by_k[k]})}};")
        marks.append(rf"\addlegendentry{{{lab}}}")
    body = "\n".join(marks)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{energy (copies / update)}},ylabel={{delivery probability}},
  legend pos=south east,grid=both,legend cell align=left,
  xtick=data,ymin=0.75,ymax=1.01]
\addplot[thick,gray,no marks] coordinates {{{front}}};
\addlegendentry{{RUCoP frontier $\mathrm{{deliv}}(k)$}}
{body}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Comparison with CGR-UCoP. The RUCoP MDP (validated against
$1-(1-q)^k$ on a symmetric plan) gives the concave delivery--vs--copies
frontier on a heterogeneous uncertain diamond. RUCoP is delivery-optimal
but energy-blind (it operates at $k{{=}}K_{{\max}}$); single-copy is cheap
but low-delivery. Our energy-aware policy stops at $k^\ast(\eta)$: at
$k^\ast{{=}}2$ it attains $94.7\%$ of RUCoP's delivery for $40\%$ of the
energy, since the extra copies RUCoP spends lie on the flat tail of the
frontier.}}
\label{{fig:rucop}}
\end{{figure}}
"""


def fig_ccdf():
    rows = load("paoi_ccdf.csv")
    def c(col):
        return " ".join(f"({float(r['deadline'])},{max(float(r[col]),1e-4):.5f})"
                        for r in rows)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{semilogyaxis}}[paperfig,width=\columnwidth,height=0.6\columnwidth,
  xlabel={{deadline $\Delta$ (periods $P$)}},
  ylabel={{$\Pr(\PAoIper>\Delta)$}},legend pos=south west,grid=both,
  legend cell align=left,ymin=0.0008,ymax=1.2]
\addplot[cC,thick,densely dotted,mark=triangle*,mark size=1.5pt] coordinates {{{c('ccdf_k1')}}};
\addlegendentry{{$k{{=}}1$}}
\addplot[cE,thick,dashed,mark=square*,mark size=1.5pt] coordinates {{{c('ccdf_k2')}}};
\addlegendentry{{$k{{=}}2$}}
\addplot[cA,thick,mark=*,mark size=1.5pt] coordinates {{{c('ccdf_k4')}}};
\addlegendentry{{$k{{=}}4$}}
\end{{semilogyaxis}}
\end{{tikzpicture}}
\caption{{PAoI tail (deadline-violation probability) at energy-abundant
$\eta$: replication pulls in the tail via the order statistic. The
probability of exceeding a $1.5P$ freshness deadline falls from $0.40$
($k{{=}}1$) to $0.16$ ($k{{=}}2$) to $0.027$ ($k{{=}}4$)---a $15\times$
reduction---and the $99$th-percentile PAoI drops from $1.90P$ to $1.59P$.
Mean PAoI alone understates the benefit of replication for
mission-critical traffic.}}
\label{{fig:ccdf}}
\end{{figure}}
"""


def fig_policy():
    rows = load("policy_sweep.csv")
    def c(col):
        return " ".join(f"({float(r['eta'])},{float(r[col]):.3f})" for r in rows)
    pol = " ".join(f"({float(r['eta'])},{float(r['paoi_policy']):.3f})" for r in rows)
    return rf"""
\begin{{figure}}[t]\centering
\begin{{tikzpicture}}
\begin{{axis}}[paperfig,width=\columnwidth,height=0.62\columnwidth,
  xlabel={{energy-adequacy ratio $\eta$}},ylabel={{mean PAoI (normalized)}},
  legend pos=north east,grid=both,legend cell align=left,ymax=4.2]
\addplot[cC,semithick,densely dotted,mark=triangle*,mark size=1.5pt] coordinates {{{c('paoi_k1')}}};
\addlegendentry{{fixed $k{{=}}1$}}
\addplot[cE,semithick,dashdotted,mark=square*,mark size=1.5pt] coordinates {{{c('paoi_k2')}}};
\addlegendentry{{fixed $k{{=}}2$}}
\addplot[cD,semithick,densely dashed,mark=diamond*,mark size=1.6pt] coordinates {{{c('paoi_k4')}}};
\addlegendentry{{fixed $k{{=}}4$}}
\addplot[cA,very thick,mark=*,mark size=1.8pt] coordinates {{{pol}}};
\addlegendentry{{AoI-Energy policy}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{The AoI-Energy policy selects the replication degree from the
closed-form rule $k_{{\mathrm{{pol}}}}(\eta)=\arg\min_k\mathcal{{A}}(k)$
(no search); it matched the per-$\eta$ exhaustive optimum in all 11 cases
and is the lower envelope of every fixed-degree curve. A single fixed $k$
is wasteful when energy is scarce (large $k$ starves) or stale when it is
abundant (small $k$ misses the order-statistic gain); the adaptive policy
is best at every energy level.}}
\label{{fig:policy}}
\end{{figure}}
"""


def main():
    header = (
        "% AUTO-GENERATED by figs/make_figures.py from sim/results/*.csv\n"
        "% and sim/tier2/results/*.csv. Re-run the generator to refresh.\n"
        "% Colour palette: Okabe-Ito (colour-blind safe, prints legibly in grey).\n"
        "\\definecolor{cA}{RGB}{0,114,178}\n"      # blue
        "\\definecolor{cB}{RGB}{213,94,0}\n"       # vermillion
        "\\definecolor{cC}{RGB}{0,158,115}\n"      # bluish green
        "\\definecolor{cD}{RGB}{204,121,167}\n"    # reddish purple
        "\\definecolor{cE}{RGB}{230,159,0}\n"      # orange
        "\\pgfplotsset{\n"
        "  paperfig/.style={\n"
        "    grid=both, grid style={black!10},\n"
        "    legend cell align=left,\n"
        "    legend style={font=\\scriptsize, fill=white, fill opacity=0.92,\n"
        "                  text opacity=1, draw=black!45, inner xsep=3pt,\n"
        "                  inner ysep=1.6pt, rounded corners=1pt},\n"
        "    tick label style={font=\\footnotesize},\n"
        "    label style={font=\\footnotesize},\n"
        "  }\n"
        "}\n")
    # fig_rucop() and fig_robust() retired (figure-count pruning): their key
    # numbers are quoted in the text; regenerate by re-adding here if needed.
    # fig_e11() retired (density pruning): its content is the Tier-1
    # traceability-table row + E11 numbers in Sec. VIII prose.
    blocks = [fig_e2(), fig_e4(), fig_e7(), fig_e8(), fig_e12(),
              fig_policy(), fig_ccdf(), fig_r3_tier2(), fig_r3_atomic(),
              fig_hetero()]
    with open(OUT, "w") as f:
        f.write(header + "\n".join(blocks))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
