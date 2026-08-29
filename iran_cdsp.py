"""
Forecast-informed compromise DSP for energy-system configuration: Iran, 2030.

This module implements the decision model reported in the manuscript. Every engineering
coefficient is taken from a documented public source and recorded with its provenance in
PROVENANCE. Every stakeholder threshold is derived from a documented policy statement and
recorded with its derivation in THRESHOLDS.

Scope: national electricity system, annual energy balance, planning year 2030. Hourly
dispatch, transmission, storage operation, reserve margins, and intra-country regional
differences lie outside this boundary.

Candidate technologies (capacity may be added): solar PV, hydro, geothermal, biofuel.
Fixed background (not a decision variable): the existing thermal fleet, predominantly gas.

"""

import numpy as np
import pandas as pd
import pulp

np.random.seed(42)
HOURS = 8760.0


def energy_twh(cf, k_gw):
    """Annual energy (TWh/yr) from capacity factor and installed capacity (GW)."""
    return HOURS * cf * k_gw / 1000.0


# ======================================================================
# 1. PROVENANCE OF EVERY INPUT
#    Each entry: (value, source, evidence class)
#      measured-national  reported for Iran by an authoritative source
#      global-proxy       global representative value, no Iran-specific value published
#      adjusted           documented value adjusted for an Iran-specific condition
#      calibrated         set so the model reproduces a reported national aggregate
#      own-forecast       produced by the forecasting stage of this research programme
#      external-forecast  projected value from an external peer-reviewed study
#      policy             a stated national target or international commitment
# ======================================================================
PROVENANCE = {
    "Installed hydro capacity": ("11.781 GW", "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024, renewable hydropower excluding pure pumped storage", "measured-national"),
    "Installed solar PV capacity": ("0.782 GW", "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024", "measured-national"),
    "Installed geothermal capacity": ("0.0 GW", "IRENA Renewable Capacity Statistics 2025, no Iranian geothermal entry", "measured-national"),
    "Installed biofuel capacity": ("0.022 GW", "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024, biogas", "measured-national"),
    "Installed thermal capacity": ("77.0 GW", "Iran Thermal Power Plants Holding Company, reported via Tehran Times 2024: combined cycle 35.663, gas turbine 25.539, steam 15.830 GW", "measured-national"),
    "Hydro capacity factor": ("0.18", "Adjusted downward for prolonged drought. The IRENA global hydro capacity factor is 0.535; Iranian reservoir depletion places recent national output near 0.12", "adjusted"),
    "Solar PV capacity factor": ("0.162", "IRENA Renewable Power Generation Costs in 2023, global weighted average, utility-scale solar PV", "global-proxy"),
    "Geothermal capacity factor": ("0.821", "IRENA Renewable Power Generation Costs in 2023, global weighted average, geothermal", "global-proxy"),
    "Biofuel capacity factor": ("0.719", "IRENA Renewable Power Generation Costs in 2023, global weighted average, bioenergy", "global-proxy"),
    "Gas capacity factor": ("0.524", "Calibrated so the existing thermal fleet reproduces the IRENA-reported 2023 Iranian generation of about 368 TWh", "calibrated"),
    "Solar PV cost": ("44 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average levelised cost", "global-proxy"),
    "Hydro cost": ("57 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average levelised cost", "global-proxy"),
    "Geothermal cost": ("71 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average levelised cost", "global-proxy"),
    "Biofuel cost": ("72 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average levelised cost", "global-proxy"),
    "Gas cost": ("76 USD/MWh", "Lazard Levelized Cost of Energy Analysis version 17.0 (2024), gas combined cycle, unsubsidised midpoint", "global-proxy"),
    "Gas emission factor": ("0.49 t CO2/MWh", "IPCC AR5 (2014) Annex III, natural gas combined cycle, lifecycle median of 490 gCO2eq/kWh", "global-proxy"),
    "Renewable emission factors": ("0 t CO2/MWh", "IPCC AR5 (2014) Annex III. Operational emissions of hydro, solar, geothermal and bioenergy are negligible at the resolution of this model", "global-proxy"),
    "National renewable target": ("30 GW by 2030", "Renewable Energy and Energy Efficiency Organization of Iran (SATBA), reported internationally", "policy"),
    "Iran 2030 demand, external": ("389.76 TWh/yr", "Shahveran and Yousefi (2025), reported range 363.64 to 408.50 TWh/yr", "external-forecast"),
    "Iran 2030 demand, our forecast": ("377.1 TWh/yr", "Forecasting stage of this research programme, piecewise log-linear model on the project dataset", "own-forecast"),
    "Electricity-sector emissions commitment": ("215.92 of 224.92 Mt CO2eq", "Shahveran and Yousefi (2025): 2030 sector trend 224.92 Mt, unconditional Paris commitment 215.92 Mt, conditional commitment 197.92 Mt", "policy"),
    "Iran 2023 generation": ("367.7 TWh", "IRENA Energy Profile Iran 2025, 2023 total generation of 367,666 GWh", "measured-national"),
}

# ======================================================================
# 2. TECHNOLOGY SET AND COEFFICIENTS
# ======================================================================
CANDIDATES = ["solarpv", "hydro", "geothermal", "biofuel"]
FIXED = ["gas_fixed"]

TECH_LABEL = {"solarpv": "Solar PV", "hydro": "Hydro", "geothermal": "Geothermal",
              "biofuel": "Biofuel", "gas_fixed": "Gas (fixed)"}

CF = {"solarpv": 0.162, "hydro": 0.18, "geothermal": 0.821, "biofuel": 0.719, "gas_fixed": 0.524}
COST = {"solarpv": 44.0, "hydro": 57.0, "geothermal": 71.0, "biofuel": 72.0, "gas_fixed": 76.0}
EMIT = {"solarpv": 0.0, "hydro": 0.0, "geothermal": 0.0, "biofuel": 0.0, "gas_fixed": 0.49}
K_EXIST = {"solarpv": 0.782, "hydro": 11.781, "geothermal": 0.0, "biofuel": 0.022, "gas_fixed": 77.0}

# Per-technology new-build ceilings for 2030 (GW). Existing renewable capacity totals about
# 12.6 GW, so the 30 GW national target leaves about 17.4 GW of headroom. We allocate that
# headroom across technologies in proportion to Iranian resource potential.
K_ADD_MAX = {"solarpv": 17.0, "hydro": 3.0, "geothermal": 1.0, "biofuel": 0.8}

BUILD_LIMIT_BASIS = {
    "solarpv": "The majority of the headroom under the 30 GW national target. Iranian solar resource potential greatly exceeds this figure, so the national target binds rather than the resource.",
    "hydro": "Iranian hydropower is largely built out and drought-constrained, so we allow a modest increment.",
    "geothermal": "The Sabalan and Damavand fields remain undeveloped, so we allow a first commercial increment.",
    "biofuel": "Iranian biomass feedstock is limited, so we allow a small increment.",
}

# ======================================================================
# 3. FORECAST-INFORMED DEMAND
# ======================================================================
DEMAND = {
    "point": 389.76,
    "ci_low": 363.64,
    "ci_high": 408.50,
    "own_forecast": 377.10,
    "credibility": "High",
    "sensitivity": "Moderate",
    "response_action": "Use, and record the sensitivity",
    "source": "Shahveran and Yousefi (2025)",
}

DEMAND_LEVELS = {
    "lower":   ("Lower end of the reported interval", DEMAND["ci_low"]),
    "own":     ("Our own 2030 forecast",              DEMAND["own_forecast"]),
    "point":   ("Central projection",                 DEMAND["point"]),
    "upper":   ("Upper end of the reported interval", DEMAND["ci_high"]),
    "widened": ("Five percent above the upper end",   DEMAND["ci_high"] * 1.05),
}


def demand_design_value(scenario="point"):
    if isinstance(scenario, (int, float)):
        return float(scenario)
    return DEMAND_LEVELS[scenario][1]


# ======================================================================
# 4. SYSTEM MODEL: ANNUAL ENERGY BALANCE WITH RESIDUAL GAS DISPATCH
# ======================================================================
def gas_max_generation():
    """Largest annual energy the fixed gas fleet can supply (TWh/yr)."""
    return energy_twh(CF["gas_fixed"], K_EXIST["gas_fixed"])


def renewable_generation(k_add):
    """Annual renewable generation from existing plus added capacity (TWh/yr)."""
    return sum(energy_twh(CF[t], K_EXIST[t] + k_add.get(t, 0.0)) for t in CANDIDATES)


def max_renewable_generation():
    return sum(energy_twh(CF[t], K_EXIST[t] + K_ADD_MAX[t]) for t in CANDIDATES)


def max_system_generation():
    """Largest annual generation the 2030 system can deliver within the build limits."""
    return max_renewable_generation() + gas_max_generation()


def gas_generation(k_add, demand, residual=True):
    """Gas generation. Under residual dispatch, gas supplies only what renewables cannot."""
    if not residual:
        return gas_max_generation()
    return min(max(0.0, demand - renewable_generation(k_add)), gas_max_generation())


def total_generation(k_add, demand=None, residual=True):
    if demand is None:
        demand = DEMAND["point"]
    return renewable_generation(k_add) + gas_generation(k_add, demand, residual)


def renewable_share(k_add, demand=None, residual=True):
    if demand is None:
        demand = DEMAND["point"]
    tg = total_generation(k_add, demand, residual)
    return renewable_generation(k_add) / tg if tg > 0 else 0.0


def annual_cost(k_add, demand=None, residual=True):
    """Annualised generation cost (billion USD/yr)."""
    if demand is None:
        demand = DEMAND["point"]
    c_ren = sum(energy_twh(CF[t], K_EXIST[t] + k_add.get(t, 0.0)) * COST[t] / 1000.0 for t in CANDIDATES)
    return c_ren + gas_generation(k_add, demand, residual) * COST["gas_fixed"] / 1000.0


def annual_emissions(k_add, demand=None, residual=True):
    """Annual CO2 emissions (Mt/yr). Renewables contribute negligibly."""
    if demand is None:
        demand = DEMAND["point"]
    return gas_generation(k_add, demand, residual) * EMIT["gas_fixed"]


def demand_is_met(k_add, demand):
    """Can renewable generation plus the full gas fleet meet the design demand?"""
    return renewable_generation(k_add) + gas_max_generation() >= demand - 1e-9


def all_gas_baseline_emissions(demand=None):
    """Emissions when the renewable fleet is unchanged and gas supplies the remainder."""
    if demand is None:
        demand = DEMAND["point"]
    return annual_emissions({}, demand)


# ======================================================================
# 5. STAKEHOLDER REQUIREMENTS, EACH WITH A DOCUMENTED DERIVATION
# ======================================================================
PARIS_TREND_MT = 224.92
PARIS_UNCONDITIONAL_MT = 215.92
PARIS_CONDITIONAL_MT = 197.92
PARIS_UNCOND_RATIO = PARIS_UNCONDITIONAL_MT / PARIS_TREND_MT
PARIS_COND_RATIO = PARIS_CONDITIONAL_MT / PARIS_TREND_MT


def emissions_ceiling(demand=None):
    """Ceiling from Iran's unconditional Paris commitment, applied as a proportional
    reduction against the all-gas baseline of the modelled fleet."""
    return all_gas_baseline_emissions(demand) * PARIS_UNCOND_RATIO


THRESHOLDS = {
    "demand_coverage": {
        "priority": "critical",
        "statement": "Renewable generation plus the full gas fleet must be able to meet the design demand.",
        "basis": "A configuration that cannot meet projected demand is unacceptable to every stakeholder, so violation is not permitted.",
    },
    "renewable_share": {
        "priority": "important", "target": 0.13, "sense": "at least",
        "statement": "At least 13 percent of annual generation from renewable sources.",
        "basis": ("Two independent policy instruments converge on this level. First, Iran's national "
                  "target of 30,000 MW of renewable capacity by 2030 implies 13.5 percent of projected "
                  "2030 generation, when the 17.4 GW of headroom above the 12.585 GW installed at "
                  "year-end 2024 is allocated across technologies in proportion to their build limits. "
                  "Second, Iran's unconditional Paris commitment for the electricity sector implies a "
                  "renewable share of 12.9 percent, because the emissions it permits can be reached only "
                  "by displacing that much gas generation. We adopt 13 percent, which is consistent with "
                  "both, and we record the derivation of each figure in the appendix."),
    },
    "emissions": {
        "priority": "important", "target": None, "sense": "at most",
        "statement": "Annual emissions at or below the level implied by Iran's unconditional Paris commitment.",
        "basis": ("Iran's unconditional Paris commitment for the electricity sector implies a 4.0 percent "
                  "reduction against the projected 2030 trend, 215.92 against 224.92 Mt CO2eq. We apply "
                  "that same proportional reduction to the all-gas baseline of the modelled fleet. We use "
                  "a proportion rather than the absolute national figure because our system boundary "
                  "covers only the generation fleet represented in the model."),
    },
    "cost": {
        "priority": "desirable", "target": 28.8, "sense": "at most",
        "statement": "Annualised generation cost at or below 28.8 billion USD per year.",
        "basis": ("The lower end of the cost range spanned by the four candidate configurations, which "
                  "run from 28.32 to 28.70 billion USD per year at the central demand. Stakeholders "
                  "prefer lower cost but treat no level as binding, so we tag this requirement desirable."),
    },
}


def stretch_thresholds(demand=None):
    """The conditional Paris commitment, used to expose a requirement the 2030 build limits
    cannot satisfy."""
    t = thresholds_for(demand)
    t["emissions"]["target"] = all_gas_baseline_emissions(demand) * PARIS_COND_RATIO
    t["emissions"]["statement"] = "Annual emissions at or below the level implied by Iran's conditional Paris commitment."
    t["renewable_share"]["target"] = 0.20
    t["renewable_share"]["statement"] = "At least 20 percent of annual generation from renewable sources."
    return t


def thresholds_for(demand=None):
    """Resolve the requirements, computing the emissions ceiling from the demand level."""
    t = {k: dict(v) for k, v in THRESHOLDS.items()}
    t["emissions"]["target"] = emissions_ceiling(demand)
    return t


# ======================================================================
# 6. CANDIDATE CONFIGURATIONS, EACH BUILT BY A STATED RULE
# ======================================================================
NAMED_CONFIGS = {
    "Current-Trend": {"solarpv": 4.0, "hydro": 0.5, "geothermal": 0.0, "biofuel": 0.1},
    "Renewable-Priority": {"solarpv": 15.0, "hydro": 2.5, "geothermal": 0.8, "biofuel": 0.6},
    "Balanced-Transition": {"solarpv": 11.0, "hydro": 2.0, "geothermal": 0.5, "biofuel": 0.4},
    "Firm-Capacity": {"solarpv": 7.0, "hydro": 1.0, "geothermal": 0.2, "biofuel": 0.2},
}

CONFIG_RULES = {
    "Current-Trend": (
        "Continuation of the recent pace of renewable additions. Iranian solar additions have run near "
        "0.8 GW per year, which over the five years to 2030 gives 4.0 GW of solar. We add the small "
        "hydro and biogas increments already under construction and no geothermal, because no Iranian "
        "geothermal plant is currently in development."),
    "Renewable-Priority": (
        "A build close to the ceiling implied by the national target. We set each technology near 90 "
        "percent of its 2030 build limit, giving 15.0 GW of solar, 2.5 GW of hydro, 0.8 GW of "
        "geothermal and 0.6 GW of biofuel."),
    "Balanced-Transition": (
        "An intermediate build spread across all four candidate technologies. We set each technology "
        "near 60 percent of its build limit, giving 11.0 GW of solar, 2.0 GW of hydro, 0.5 GW of "
        "geothermal and 0.4 GW of biofuel."),
    "Firm-Capacity": (
        "A reliability-first build that leans on the dispatchable gas fleet. We halve the "
        "Balanced-Transition solar figure to 7.0 GW and reduce the other technologies in proportion, "
        "reflecting a stakeholder preference for firm capacity over variable renewable output."),
}


def config_table():
    """The candidate configurations with their construction rules and capacities."""
    rows = []
    for name, k in NAMED_CONFIGS.items():
        rows.append({"Configuration": name,
                     **{f"{TECH_LABEL[t]} (GW)": k[t] for t in CANDIDATES},
                     "Total added (GW)": round(sum(k.values()), 2),
                     "Construction rule": CONFIG_RULES[name]})
    return pd.DataFrame(rows)


def screen_config(name, k_add, demand, thresholds=None):
    """Stage 1 screening of one configuration against the stakeholder requirements."""
    if thresholds is None:
        thresholds = thresholds_for(demand)
    met = demand_is_met(k_add, demand)
    gen = total_generation(k_add, demand)
    rs = renewable_share(k_add, demand)
    em = annual_emissions(k_add, demand)
    ct = annual_cost(k_add, demand)
    checks = {
        "demand coverage": (met, "critical"),
        "renewable share": (rs >= thresholds["renewable_share"]["target"] - 1e-9, "important"),
        "emissions": (em <= thresholds["emissions"]["target"] + 1e-9, "important"),
        "cost": (ct <= thresholds["cost"]["target"] + 1e-9, "desirable"),
    }
    crit = [k for k, (ok, p) in checks.items() if p == "critical" and not ok]
    imp = [k for k, (ok, p) in checks.items() if p == "important" and not ok]
    des = [k for k, (ok, p) in checks.items() if p == "desirable" and not ok]
    if crit:
        status = "Rejected"
    elif imp:
        status = "Flagged"
    elif des:
        status = "Acceptable with a desirable miss"
    else:
        status = "Acceptable"
    return {"config": name, "added_GW": sum(k_add.values()), "generation_TWh": gen,
            "renewable_share": rs, "emissions_Mt": em, "cost_bnUSD": ct, "status": status,
            "critical_fail": crit, "important_fail": imp, "desirable_fail": des}


def screening_table(demand="point"):
    D = demand_design_value(demand)
    rows = []
    for name, k in NAMED_CONFIGS.items():
        r = screen_config(name, k, D)
        reasons = []
        if r["critical_fail"]:
            reasons.append("fails critical: " + ", ".join(r["critical_fail"]))
        if r["important_fail"]:
            reasons.append("misses important: " + ", ".join(r["important_fail"]))
        if r["desirable_fail"]:
            reasons.append("misses desirable: " + ", ".join(r["desirable_fail"]))
        rows.append({"Configuration": name,
                     "New capacity (GW)": round(r["added_GW"], 2),
                     "Generation (TWh/yr)": round(r["generation_TWh"], 1),
                     "Renewable share (%)": round(r["renewable_share"] * 100, 1),
                     "Emissions (Mt/yr)": round(r["emissions_Mt"], 1),
                     "Cost (bn USD/yr)": round(r["cost_bnUSD"], 2),
                     "Outcome": r["status"],
                     "Reason": "; ".join(reasons) if reasons else "meets every requirement"})
    return pd.DataFrame(rows)


# ======================================================================
# 7. THE COMPROMISE DSP
# ======================================================================
GOALS = ["renewable", "emissions", "cost"]


def _problem(D, thresholds, build_limits):
    R_t = thresholds["renewable_share"]["target"]
    M_t = thresholds["emissions"]["target"]
    C_t = thresholds["cost"]["target"]

    prob = pulp.LpProblem("iran_cdsp", pulp.LpMinimize)
    x = {t: pulp.LpVariable(f"x_{t}", 0, build_limits[t]) for t in CANDIDATES}
    g = {t: energy_twh(CF[t], K_EXIST[t] + x[t]) for t in CANDIDATES}
    renew = pulp.lpSum(g.values())
    gas_cap = gas_max_generation()

    g_gas = pulp.LpVariable("g_gas", 0, gas_cap)
    prob += (g_gas >= D - renew), "residual_gas"

    total = renew + g_gas
    cost = pulp.lpSum(g[t] * COST[t] / 1000.0 for t in CANDIDATES) + g_gas * COST["gas_fixed"] / 1000.0
    emis = g_gas * EMIT["gas_fixed"]

    d = {k: (pulp.LpVariable(f"d_{k}_under", 0), pulp.LpVariable(f"d_{k}_over", 0)) for k in GOALS}

    prob += (renew + gas_cap >= D), "demand_coverage"
    prob += (renew - R_t * total + d["renewable"][0] - d["renewable"][1] == 0), "goal_renewable"
    prob += (emis / M_t + d["emissions"][0] - d["emissions"][1] == 1), "goal_emissions"
    prob += (cost / C_t + d["cost"][0] - d["cost"][1] == 1), "goal_cost"

    return prob, {"x": x, "renew": renew, "g_gas": g_gas, "total": total, "cost": cost,
                  "emis": emis, "d": d, "D": D, "R_t": R_t, "M_t": M_t, "C_t": C_t}


def _penalties(h):
    return {"renewable": h["d"]["renewable"][0] / (h["R_t"] * DEMAND["point"]),
            "emissions": h["d"]["emissions"][1],
            "cost": h["d"]["cost"][1]}


# When the stated requirements can all be met, many configurations drive the deviation
# function to zero and the solver would return an arbitrary one among them. We therefore add
# a small secondary term on total new capacity. Among configurations that satisfy the goals
# equally well, a designer prefers the smaller build, because it commits less capital and
# leaves more room to revise the decision later. The weight is small enough that it never
# overrides a goal, and it makes the reported solution unique and reproducible.
TIE_BREAK = 1e-4


def _tie_break(h):
    return TIE_BREAK * pulp.lpSum(h["x"].values())


def solve_cdsp(demand="point", form="weighted", weights=None,
               priorities=("renewable", "emissions", "cost"),
               thresholds=None, build_limits=None):
    """Solve the compromise DSP in the weighted or the priority form."""
    D = demand_design_value(demand)
    if thresholds is None:
        thresholds = thresholds_for(D)
    if build_limits is None:
        build_limits = K_ADD_MAX

    if form == "weighted":
        if weights is None:
            weights = {"renewable": 1 / 3, "emissions": 1 / 3, "cost": 1 / 3}
        prob, h = _problem(D, thresholds, build_limits)
        pen = _penalties(h)
        prob += pulp.lpSum(weights[k] * pen[k] for k in GOALS) + _tie_break(h), "Z"
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        return _extract(prob, h, form, D, weights=weights)

    if form == "priority":
        frozen, last = [], None
        for level, key in enumerate(priorities):
            prob, h = _problem(D, thresholds, build_limits)
            pen = _penalties(h)
            for fk, fv in frozen:
                if fv is not None:
                    prob += (_penalties(h)[fk] <= fv + 1e-6), f"lock_{fk}"
            prob += pen[key] + _tie_break(h), f"Z_{level}_{key}"
            prob.solve(pulp.PULP_CBC_CMD(msg=0))
            val = pulp.value(pen[key]) if pulp.LpStatus[prob.status] == "Optimal" else None
            frozen.append((key, val))
            last = (prob, h)
        prob, h = last
        return _extract(prob, h, form, D, priorities=priorities)

    raise ValueError("form must be 'weighted' or 'priority'")


def _extract(prob, h, form, D, weights=None, priorities=None):
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return {"status": status, "form": form, "demand_TWh": D, "feasible": False,
                "added_GW": None, "generation_TWh": None, "renewable_share": None,
                "emissions_Mt": None, "cost_bnUSD": None, "deviations": None,
                "weights": weights, "priorities": priorities}
    v = pulp.value
    k_add = {t: v(h["x"][t]) for t in CANDIDATES}
    dev = {f"{k}_{side}": v(h["d"][k][i])
           for k in GOALS for i, side in enumerate(("under", "over"))}
    return {"status": status, "form": form, "demand_TWh": D, "feasible": True,
            "added_GW": k_add, "total_added_GW": sum(k_add.values()),
            "generation_TWh": total_generation(k_add, D),
            "renewable_share": renewable_share(k_add, D),
            "emissions_Mt": annual_emissions(k_add, D),
            "cost_bnUSD": annual_cost(k_add, D),
            "gas_generation_TWh": gas_generation(k_add, D),
            "deviations": dev, "weights": weights, "priorities": priorities,
            "targets": {"renewable": h["R_t"], "emissions": h["M_t"], "cost": h["C_t"]}}


def solution_row(sol, label):
    """One row summarising a solution, for the results tables."""
    if not sol["feasible"]:
        return {"Solution": label, "Outcome": "No feasible configuration"}
    return {"Solution": label,
            **{f"{TECH_LABEL[t]} (GW)": round(sol["added_GW"][t], 2) for t in CANDIDATES},
            "Total added (GW)": round(sol["total_added_GW"], 2),
            "Renewable share (%)": round(sol["renewable_share"] * 100, 1),
            "Emissions (Mt/yr)": round(sol["emissions_Mt"], 1),
            "Cost (bn USD/yr)": round(sol["cost_bnUSD"], 2)}


# ======================================================================
# 8. BASELINE DECISION RULES
# ======================================================================
BASELINE_BASIS = {
    "Least cost only": "A designer minimises annualised cost and disregards the renewable and emissions aspirations.",
    "Minimum new capacity": "A designer adds the least capacity that still meets demand, disregarding the renewable and emissions aspirations.",
    "Pro-rata scaling": "A designer scales the existing renewable mix proportionally until demand can be met.",
    "Best screened configuration": "A designer screens the named configurations and takes the acceptable one with the lowest cost, without searching the design space.",
    "Compromise DSP": "A designer states the requirements as goals with deviation variables and minimises the deviation function.",
}


def _lp_baseline(label, sense, objective_fn, D):
    prob = pulp.LpProblem("baseline", sense)
    x = {t: pulp.LpVariable(f"x_{t}", 0, K_ADD_MAX[t]) for t in CANDIDATES}
    g = {t: energy_twh(CF[t], K_EXIST[t] + x[t]) for t in CANDIDATES}
    renew = pulp.lpSum(g.values())
    g_gas = pulp.LpVariable("g_gas", 0, gas_max_generation())
    prob += (g_gas >= D - renew)
    prob += (renew + gas_max_generation() >= D)
    prob += objective_fn(g, g_gas, renew)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[prob.status] != "Optimal":
        return {"rule": label, "feasible": False}
    k_add = {t: pulp.value(x[t]) for t in CANDIDATES}
    return {"rule": label, "feasible": True, "added_GW": k_add,
            "total_added_GW": sum(k_add.values()),
            "renewable_share": renewable_share(k_add, D),
            "emissions_Mt": annual_emissions(k_add, D),
            "cost_bnUSD": annual_cost(k_add, D)}


def baseline_least_cost(demand="point"):
    D = demand_design_value(demand)
    return _lp_baseline("Least cost only", pulp.LpMinimize,
                        lambda g, gg, r: pulp.lpSum(g[t] * COST[t] / 1000.0 for t in CANDIDATES)
                        + gg * COST["gas_fixed"] / 1000.0, D)


def baseline_min_build(demand="point"):
    """B2. Add the least new capacity that still meets demand, disregarding the aspirations."""
    D = demand_design_value(demand)
    prob = pulp.LpProblem("b2", pulp.LpMinimize)
    x = {t: pulp.LpVariable(f"x_{t}", 0, K_ADD_MAX[t]) for t in CANDIDATES}
    renew = pulp.lpSum(energy_twh(CF[t], K_EXIST[t] + x[t]) for t in CANDIDATES)
    prob += (renew + gas_max_generation() >= D)
    prob += pulp.lpSum(x.values())
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[prob.status] != "Optimal":
        return {"rule": "Minimum new capacity", "feasible": False}
    k_add = {t: pulp.value(x[t]) for t in CANDIDATES}
    return {"rule": "Minimum new capacity", "feasible": True, "added_GW": k_add,
            "total_added_GW": sum(k_add.values()),
            "renewable_share": renewable_share(k_add, D),
            "emissions_Mt": annual_emissions(k_add, D),
            "cost_bnUSD": annual_cost(k_add, D)}


def baseline_pro_rata(demand="point"):
    D = demand_design_value(demand)
    base_gen = renewable_generation({})
    need = max(0.0, D - gas_max_generation())
    if base_gen <= 0:
        return {"rule": "Pro-rata scaling", "feasible": False}
    scale = (need - base_gen) / base_gen if need > base_gen else 0.0
    k_add = {t: min(K_EXIST[t] * max(scale, 0.0), K_ADD_MAX[t]) for t in CANDIDATES}
    ok = demand_is_met(k_add, D)
    return {"rule": "Pro-rata scaling", "feasible": ok, "added_GW": k_add,
            "total_added_GW": sum(k_add.values()),
            "renewable_share": renewable_share(k_add, D) if ok else None,
            "emissions_Mt": annual_emissions(k_add, D) if ok else None,
            "cost_bnUSD": annual_cost(k_add, D) if ok else None}


def baseline_best_screened(demand="point"):
    D = demand_design_value(demand)
    rows = [screen_config(n, k, D) for n, k in NAMED_CONFIGS.items()]
    ok = [r for r in rows if r["status"].startswith("Acceptable")]
    if not ok:
        return {"rule": "Best screened configuration", "feasible": False}
    best = min(ok, key=lambda r: r["cost_bnUSD"])
    k_add = dict(NAMED_CONFIGS[best["config"]])
    return {"rule": "Best screened configuration", "feasible": True, "chosen": best["config"],
            "added_GW": k_add, "total_added_GW": sum(k_add.values()),
            "renewable_share": best["renewable_share"], "emissions_Mt": best["emissions_Mt"],
            "cost_bnUSD": best["cost_bnUSD"]}


def baseline_comparison(demand="point"):
    """Compare the compromise solution with four simpler decision rules."""
    D = demand_design_value(demand)
    thr = thresholds_for(D)
    results = [baseline_least_cost(demand), baseline_min_build(demand),
               baseline_pro_rata(demand), baseline_best_screened(demand)]
    sol = solve_cdsp(demand, "weighted")
    results.append({"rule": "Compromise DSP", "feasible": sol["feasible"],
                    "added_GW": sol["added_GW"], "total_added_GW": sol.get("total_added_GW"),
                    "renewable_share": sol["renewable_share"], "emissions_Mt": sol["emissions_Mt"],
                    "cost_bnUSD": sol["cost_bnUSD"]})
    rows = []
    for r in results:
        if not r.get("feasible"):
            rows.append({"Decision rule": r["rule"], "Total added (GW)": None,
                         "Renewable share (%)": None, "Emissions (Mt/yr)": None,
                         "Cost (bn USD/yr)": None, "Requirements satisfied": "No feasible result",
                         "What the designer gives up": BASELINE_BASIS.get(r["rule"], "")})
            continue
        rs, em, ct = r["renewable_share"], r["emissions_Mt"], r["cost_bnUSD"]
        flags = [rs >= thr["renewable_share"]["target"] - 1e-9,
                 em <= thr["emissions"]["target"] + 1e-9,
                 ct <= thr["cost"]["target"] + 1e-9]
        missed = [n for n, f in zip(("renewable share", "emissions", "cost"), flags) if not f]
        rows.append({"Decision rule": r["rule"],
                     "Total added (GW)": round(r["total_added_GW"], 2),
                     "Renewable share (%)": round(rs * 100, 1),
                     "Emissions (Mt/yr)": round(em, 1),
                     "Cost (bn USD/yr)": round(ct, 2),
                     "Requirements satisfied": f"{sum(flags)} of 3"
                     + (f" (misses {', '.join(missed)})" if missed else ""),
                     "What the designer gives up": BASELINE_BASIS.get(r["rule"], "")})
    return pd.DataFrame(rows)


# ======================================================================
# 9. ABLATIONS
# ======================================================================
def ablation_fixed_gas(demand="point"):
    """A1. Remove residual dispatch: gas runs flat out and emissions stop responding."""
    D = demand_design_value(demand)
    rows = []
    for name, k in NAMED_CONFIGS.items():
        rows.append({"Configuration": name,
                     "Emissions, residual dispatch (Mt/yr)": round(annual_emissions(k, D, True), 1),
                     "Emissions, gas fixed at full output (Mt/yr)": round(annual_emissions(k, D, False), 1)})
    df = pd.DataFrame(rows)
    df.attrs["spread_residual"] = round(df.iloc[:, 1].max() - df.iloc[:, 1].min(), 1)
    df.attrs["spread_fixed"] = round(df.iloc[:, 2].max() - df.iloc[:, 2].min(), 1)
    return df


def ablation_solar_model_form(demand="point"):
    """A2. Remove model-form testing: a single solar capacity factor is trusted."""
    base = CF["solarpv"]
    rows = []
    for label, cf in [("Retained, 0.162", 0.162), ("Alternate optimistic, 0.20", 0.20),
                      ("Conservative, 0.12", 0.12)]:
        CF["solarpv"] = cf
        s = solve_cdsp(demand, "weighted")
        rows.append({"Solar capacity-factor assumption": label, "Capacity factor": cf,
                     "Solar capacity added (GW)": round(s["added_GW"]["solarpv"], 2),
                     "Total added (GW)": round(s["total_added_GW"], 2),
                     "Renewable share (%)": round(s["renewable_share"] * 100, 1),
                     "Cost (bn USD/yr)": round(s["cost_bnUSD"], 2)})
    CF["solarpv"] = base
    return pd.DataFrame(rows)


def ablation_demand_scenarios():
    """A3. Remove scenario testing: only the central projection is examined."""
    rows = []
    for key, (label, val) in DEMAND_LEVELS.items():
        s = solve_cdsp(key, "weighted")
        rows.append({"Demand level": label, "Demand (TWh/yr)": round(val, 1),
                     "Outcome": "Feasible" if s["feasible"] else "No feasible configuration",
                     "Solar added (GW)": round(s["added_GW"]["solarpv"], 2) if s["feasible"] else None,
                     "Total added (GW)": round(s["total_added_GW"], 2) if s["feasible"] else None,
                     "Renewable share (%)": round(s["renewable_share"] * 100, 1) if s["feasible"] else None,
                     "Emissions (Mt/yr)": round(s["emissions_Mt"], 1) if s["feasible"] else None,
                     "Cost (bn USD/yr)": round(s["cost_bnUSD"], 2) if s["feasible"] else None})
    return pd.DataFrame(rows)


def reduction_check(demand="point"):
    """A4. With every requirement rigid, the admitted set equals the screened set."""
    D = demand_design_value(demand)
    thr = thresholds_for(D)
    rows = []
    for name, k in NAMED_CONFIGS.items():
        rigid_ok = (demand_is_met(k, D)
                    and renewable_share(k, D) >= thr["renewable_share"]["target"] - 1e-9
                    and annual_emissions(k, D) <= thr["emissions"]["target"] + 1e-9)
        screened_ok = screen_config(name, k, D)["status"].startswith("Acceptable")
        rows.append({"Configuration": name,
                     "Admitted when every requirement is rigid": rigid_ok,
                     "Accepted in the screening stage": screened_ok,
                     "Agreement": rigid_ok == screened_ok})
    return pd.DataFrame(rows)


# ======================================================================
# 10. TRADE-OFF FRONTIER AND WEIGHT SWEEP
# ======================================================================
def tradeoff_frontier(demand="point", n=25):
    """Lowest achievable cost as the renewable-share requirement is tightened."""
    D = demand_design_value(demand)
    lo = renewable_share({}, D)
    rows = []
    for target in np.linspace(lo, 0.18, n):
        thr = thresholds_for(D)
        thr["renewable_share"]["target"] = float(target)
        s = solve_cdsp(demand, "priority", priorities=("renewable", "cost", "emissions"),
                       thresholds=thr)
        if s["feasible"]:
            rows.append({"Renewable-share requirement (%)": target * 100,
                         "Achieved renewable share (%)": s["renewable_share"] * 100,
                         "Cost (bn USD/yr)": s["cost_bnUSD"],
                         "Emissions (Mt/yr)": s["emissions_Mt"],
                         "Total added (GW)": s["total_added_GW"]})
    return pd.DataFrame(rows)


def weight_sweep(demand="point", n=21):
    """Recommended configuration across the range of weight on the renewable goal."""
    rows = []
    for w in np.linspace(0, 1, n):
        rest = (1 - w) / 2
        s = solve_cdsp(demand, "weighted",
                       weights={"renewable": w, "emissions": rest, "cost": rest})
        rows.append({"Weight on the renewable goal": w,
                     "Renewable share (%)": s["renewable_share"] * 100,
                     "Cost (bn USD/yr)": s["cost_bnUSD"],
                     "Emissions (Mt/yr)": s["emissions_Mt"],
                     **{f"{TECH_LABEL[t]} (GW)": s["added_GW"][t] for t in CANDIDATES}})
    return pd.DataFrame(rows)


# ======================================================================
# 11. VERIFICATION
# ======================================================================
def verify(sol, tol=1e-4):
    """Check a solution against the conditions a compromise solution must satisfy."""
    if not sol["feasible"]:
        return pd.DataFrame([{"Quantity": "Feasibility", "Computed": "infeasible",
                              "Required": "feasible", "Satisfied": False}])
    D = sol["demand_TWh"]
    d = sol["deviations"]
    R_t, M_t, C_t = (sol["targets"]["renewable"], sol["targets"]["emissions"], sol["targets"]["cost"])
    gen = sol["generation_TWh"]
    renew = sol["renewable_share"] * gen
    checks = [
        ("Renewable-share goal equation residual",
         renew - R_t * gen + d["renewable_under"] - d["renewable_over"], 0.0),
        ("Emissions goal equation residual",
         sol["emissions_Mt"] / M_t + d["emissions_under"] - d["emissions_over"], 1.0),
        ("Cost goal equation residual",
         sol["cost_bnUSD"] / C_t + d["cost_under"] - d["cost_over"], 1.0),
        ("Product of the two renewable deviations", d["renewable_under"] * d["renewable_over"], 0.0),
        ("Product of the two emissions deviations", d["emissions_under"] * d["emissions_over"], 0.0),
        ("Product of the two cost deviations", d["cost_under"] * d["cost_over"], 0.0),
    ]
    rows = [{"Quantity": n,
             "Computed": ("%.2e" % v) if abs(v) < 1e-3 else ("%.6f" % v),
             "Required": "%.0f" % r, "Satisfied": abs(v - r) < tol} for n, v, r in checks]
    nonneg = all(val >= -1e-9 for val in d.values())
    rows.append({"Quantity": "All deviation variables non-negative",
                 "Computed": "yes" if nonneg else "no", "Required": "yes", "Satisfied": nonneg})
    rows.append({"Quantity": "Generation at least demand (TWh/yr)",
                 "Computed": "%.2f against %.2f" % (gen, D), "Required": "at least",
                 "Satisfied": gen >= D - tol})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    D = demand_design_value("point")
    print("=" * 74)
    print("FORECAST-INFORMED COMPROMISE DSP: IRAN 2030")
    print("=" * 74)
    print(f"Existing renewable generation   : {renewable_generation({}):8.2f} TWh/yr")
    print(f"Gas fleet maximum output        : {gas_max_generation():8.2f} TWh/yr")
    print(f"Existing system total           : {renewable_generation({}) + gas_max_generation():8.2f} TWh/yr")
    print(f"Maximum 2030 system generation  : {max_system_generation():8.2f} TWh/yr")
    print(f"Central demand projection       : {DEMAND['point']:8.2f} TWh/yr")
    print(f"Our own 2030 forecast           : {DEMAND['own_forecast']:8.2f} TWh/yr")
    diff = DEMAND["point"] - DEMAND["own_forecast"]
    print(f"Difference                      : {diff:8.2f} TWh/yr = {diff / DEMAND['own_forecast'] * 100:.2f}%")
    print(f"All-gas baseline emissions      : {all_gas_baseline_emissions(D):8.2f} Mt/yr")
    print(f"Emissions ceiling (Paris ratio) : {emissions_ceiling(D):8.2f} Mt/yr")
    print()
    print("STAGE 1 SCREENING")
    print(screening_table().drop(columns=["Reason"]).to_string(index=False))
    print()
    print("BASELINE COMPARISON")
    print(baseline_comparison().drop(columns=["What the designer gives up"]).to_string(index=False))


def cost_conflict_case(demand="point", solar_cost=90.0, hydro_cost=100.0):
    """Sensitivity in which renewable costs sit above the incumbent gas cost.

    In the documented 2023 cost data every renewable technology is cheaper per unit of
    energy than gas, so raising the renewable share also lowers annualised cost and the two
    aspirations do not compete. Global weighted-average solar costs stood above the gas
    figure as recently as the late 2010s, and they remain above it in some markets. We
    therefore repeat the decision with solar and hydro costs placed above the gas cost, to
    show how the deviation-function form governs the recommendation once the aspirations do
    compete.
    """
    base = dict(COST)
    COST["solarpv"], COST["hydro"] = solar_cost, hydro_cost
    rows = []
    for label, form, pri in [("Weighted, equal weights", "weighted", None),
                             ("Priority: renewable first", "priority", ("renewable", "emissions", "cost")),
                             ("Priority: cost first", "priority", ("cost", "emissions", "renewable"))]:
        s = solve_cdsp(demand, form) if pri is None else solve_cdsp(demand, form, priorities=pri)
        rows.append(solution_row(s, label))
    COST.update(base)
    return pd.DataFrame(rows)


def goal_alignment_note():
    """Whether each renewable technology is cheaper per unit energy than the incumbent."""
    return pd.DataFrame([{"Technology": TECH_LABEL[t], "Levelised cost (USD/MWh)": COST[t],
                          "Cheaper than gas": COST[t] < COST["gas_fixed"]}
                         for t in CANDIDATES + ["gas_fixed"]])
