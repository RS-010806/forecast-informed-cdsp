"""
Forecast-informed cDSP for energy-system configuration: Iran, 2030.

Every engineering coefficient is taken from a documented public source and recorded
with its provenance in PROVENANCE below.

Scope: national electricity system, annual energy balance, planning year 2030.
We do not model hourly dispatch, transmission, storage operation, reserve margins,
or intra-country regional differences.

Candidate technologies (capacity may be added): Solar PV, Hydro, Geothermal, Biofuel.
Fixed background (not a decision variable): existing thermal/gas fleet.
"""

import numpy as np
import pandas as pd
import pulp

np.random.seed(42)
HOURS = 8760.0


def energy_twh(cf, k_gw):
    "Annual energy (TWh/yr) from capacity factor and capacity (GW)."
    return HOURS * cf * k_gw / 1000.0


# ======================================================================
# PROVENANCE
# ======================================================================
PROVENANCE = {
    "K_exist.hydro":      ("11.781 GW", "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024 (renewable hydro, excluding pumped storage)"),
    "K_exist.solarpv":    ("0.782 GW",  "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024"),
    "K_exist.geothermal": ("0.0 GW",    "IRENA Renewable Capacity Statistics 2025 (no Iran geothermal entry; greenfield)"),
    "K_exist.biofuel":    ("0.022 GW",  "IRENA Renewable Capacity Statistics 2025, Iran, year-end 2024 (biogas)"),
    "K_exist.gas_fixed":  ("77.0 GW",   "Iran Thermal Power Plants Holding via Tehran Times 2024 (combined cycle 35.663, gas turbine 25.539, steam 15.830 GW)"),
    "CF.hydro":           ("0.18",      "Iran drought-adjusted. IRENA global hydro capacity factor is 0.535; Iran 2023 actual is about 0.12 because of reservoir depletion"),
    "CF.solarpv":         ("0.162",     "IRENA Renewable Power Generation Costs in 2023, global weighted average, utility-scale solar PV"),
    "CF.geothermal":      ("0.821",     "IRENA Renewable Power Generation Costs in 2023, global weighted average, geothermal"),
    "CF.biofuel":         ("0.719",     "IRENA Renewable Power Generation Costs in 2023, global weighted average, bioenergy"),
    "CF.gas_fixed":       ("0.524",     "Calibrated so that existing thermal generation reproduces the IRENA-reported 2023 Iran generation of about 368 TWh"),
    "COST.hydro":         ("57 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average LCOE, hydropower"),
    "COST.solarpv":       ("44 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average LCOE, solar PV"),
    "COST.geothermal":    ("71 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average LCOE, geothermal"),
    "COST.biofuel":       ("72 USD/MWh", "IRENA Renewable Power Generation Costs in 2023, global weighted-average LCOE, bioenergy"),
    "COST.gas_fixed":     ("76 USD/MWh", "Lazard Levelized Cost of Energy Plus, version 17.0 (2024), gas combined cycle, unsubsidized midpoint"),
    "EMIT.gas":           ("0.49 t/MWh", "IPCC AR5 (2014) Annex III, natural gas combined cycle, lifecycle median 490 gCO2eq/kWh"),
    "EMIT.renewables":    ("about 0",    "IPCC AR5 and NREL LCA Harmonization; operational emissions of hydro, solar, geothermal and bioenergy are negligible"),
    "TARGET.renew_2030":  ("30 GW",      "SATBA and UN-Iran (September 2024), renewable capacity target of 30,000 MW by 2030"),
    "DEMAND.external":    ("389.76 TWh", "Aliabadi et al. (2024), curve fit with EnergyPLAN, reported range 363.64 to 408.5 TWh"),
    "DEMAND.earlier":     ("377.1 TWh",  "Value produced in the earlier forecasting work of this research program on the project dataset"),
    "GEN.2023":           ("367.7 TWh",  "IRENA Energy Profile Iran 2025 (2023 total generation 367,666 GWh)"),
}

# ======================================================================
# TECHNOLOGY SET AND COEFFICIENTS
# ======================================================================
CANDIDATES = ["solarpv", "hydro", "geothermal", "biofuel"]
FIXED = ["gas_fixed"]

CF   = {"hydro": 0.18,   "solarpv": 0.162, "geothermal": 0.821, "biofuel": 0.719, "gas_fixed": 0.524}
COST = {"hydro": 57.0,   "solarpv": 44.0,  "geothermal": 71.0,  "biofuel": 72.0,  "gas_fixed": 76.0}   # USD/MWh
EMIT = {"hydro": 0.0,    "solarpv": 0.0,   "geothermal": 0.0,   "biofuel": 0.0,   "gas_fixed": 0.49}   # t CO2/MWh
K_EXIST = {"hydro": 11.781, "solarpv": 0.782, "geothermal": 0.0, "biofuel": 0.022, "gas_fixed": 77.0}  # GW

# Additional capacity that may be built by 2030 (GW).
K_ADD_MAX = {"solarpv": 17.0, "hydro": 3.0, "geothermal": 1.0, "biofuel": 0.8}

# ======================================================================
# FORECAST-INFORMED DEMAND
# ======================================================================
DEMAND = {
    "point": 389.76, "ci_low": 363.64, "ci_high": 408.5,
    "earlier_forecast": 377.1,
    "credibility": "High", "sensitivity": "Moderate", "bound_action": "use with note",
    "source": "Aliabadi et al. (2024)",
}


def demand_design_value(scenario="point"):
    return {
        "lower":    DEMAND["ci_low"],
        "earlier":  DEMAND["earlier_forecast"],
        "point":    DEMAND["point"],
        "upper":    DEMAND["ci_high"],
        "widened":  DEMAND["ci_high"] * 1.05,
    }[scenario]


# ======================================================================
# SYSTEM MODEL (annual energy balance with residual gas dispatch)
# ======================================================================
def gas_max_generation():
    "Maximum annual energy the fixed gas fleet can supply (TWh)."
    return energy_twh(CF["gas_fixed"], K_EXIST["gas_fixed"])


def renewable_gen_add(k_add):
    "Annual renewable generation from existing plus added renewable capacity (TWh)."
    return sum(energy_twh(CF[t], K_EXIST[t] + k_add.get(t, 0.0)) for t in CANDIDATES)


def max_renewable_generation():
    "Renewable generation when every candidate is built to its 2030 limit (TWh)."
    return sum(energy_twh(CF[t], K_EXIST[t] + K_ADD_MAX[t]) for t in CANDIDATES)


def max_system_generation():
    "Largest annual generation the 2030 system can deliver (TWh)."
    return max_renewable_generation() + gas_max_generation()


def gas_generation(k_add, demand):
    "Residual gas generation to meet demand after renewables, capped by the fleet maximum."
    residual = max(0.0, demand - renewable_gen_add(k_add))
    return min(residual, gas_max_generation())


def total_cap(k_add):
    return {t: K_EXIST[t] + k_add.get(t, 0.0) for t in K_EXIST}


def total_gen(k_add, demand=None):
    if demand is None:
        demand = DEMAND["point"]
    return renewable_gen_add(k_add) + gas_generation(k_add, demand)


def renewable_share(k_add, demand=None):
    if demand is None:
        demand = DEMAND["point"]
    tg = total_gen(k_add, demand)
    return renewable_gen_add(k_add) / tg if tg > 0 else 0.0


def annual_cost(k_add, demand=None):
    if demand is None:
        demand = DEMAND["point"]
    c_ren = sum(energy_twh(CF[t], K_EXIST[t] + k_add.get(t, 0.0)) * COST[t] / 1000.0 for t in CANDIDATES)
    c_gas = gas_generation(k_add, demand) * COST["gas_fixed"] / 1000.0
    return c_ren + c_gas


def annual_emissions(k_add, demand=None):
    if demand is None:
        demand = DEMAND["point"]
    return gas_generation(k_add, demand) * EMIT["gas_fixed"]


def supply_adequate(k_add, demand):
    "Can renewables plus the full gas fleet meet demand?"
    return renewable_gen_add(k_add) + gas_max_generation() >= demand - 1e-9


# ======================================================================
# STAKEHOLDER REQUIREMENTS
# ======================================================================
THRESHOLDS = {
    "demand_coverage": {"type": "critical", "rule": "renewables plus the gas fleet can meet demand"},
    "renewable_share": {"type": "important", "target": 0.10, "sense": "at_least",
                        "basis": "Raise the renewable share from about 5 percent toward the direction of the 30 GW by 2030 target, to at least 10 percent"},
    "emissions":       {"type": "important", "target": 172.0, "sense": "at_most",
                        "basis": "Ceiling below the about 173 Mt of an all-gas residual, so that genuine gas displacement is required"},
    "cost":            {"type": "desirable", "target": 28.8, "sense": "at_most",
                        "basis": "Annualized generation-cost aspiration near the lower end of the achievable range"},
}

# ======================================================================
# NAMED CONFIGURATIONS (built by stated rules)
# ======================================================================
NAMED_CONFIGS = {
    "Current-Trend":       {"solarpv": 4.0,  "hydro": 0.5, "geothermal": 0.0, "biofuel": 0.1},
    "Renewable-Priority":  {"solarpv": 15.0, "hydro": 2.5, "geothermal": 0.8, "biofuel": 0.6},
    "Balanced-Transition": {"solarpv": 11.0, "hydro": 2.0, "geothermal": 0.5, "biofuel": 0.4},
    "Firm-Capacity":       {"solarpv": 7.0,  "hydro": 1.0, "geothermal": 0.2, "biofuel": 0.2},
}


def screen_config(name, k_add, demand_design, thresholds=None):
    if thresholds is None:
        thresholds = THRESHOLDS
    adequate = supply_adequate(k_add, demand_design)
    supply = total_gen(k_add, demand_design)
    rshare = renewable_share(k_add, demand_design)
    emis = annual_emissions(k_add, demand_design)
    cost = annual_cost(k_add, demand_design)
    checks = {
        "demand_coverage": (adequate, "critical"),
        "renewable_share": (rshare >= thresholds["renewable_share"]["target"], "important"),
        "emissions":       (emis <= thresholds["emissions"]["target"], "important"),
        "cost":            (cost <= thresholds["cost"]["target"], "desirable"),
    }
    crit = [k for k, (ok, l) in checks.items() if l == "critical" and not ok]
    imp  = [k for k, (ok, l) in checks.items() if l == "important" and not ok]
    des  = [k for k, (ok, l) in checks.items() if l == "desirable" and not ok]
    status = ("Rejected" if crit else "Flagged" if imp
              else "Acceptable, desirable miss" if des else "Acceptable")
    return {"config": name, "supply_TWh": supply, "renewable_share": rshare,
            "emissions_Mt": emis, "cost_bnUSD": cost, "status": status,
            "critical_fail": crit, "important_fail": imp, "desirable_fail": des}


# ======================================================================
# THE cDSP
# ======================================================================
GOAL_KEYS = ["renewable", "emissions", "cost"]


def build_and_solve(demand_scenario="point", mode="archimedean", weights=None,
                    priorities=("renewable", "emissions", "cost"), thresholds=None,
                    build_limits=None):
    if thresholds is None:
        thresholds = THRESHOLDS
    if build_limits is None:
        build_limits = K_ADD_MAX
    D = demand_design_value(demand_scenario) if isinstance(demand_scenario, str) else float(demand_scenario)
    R_t = thresholds["renewable_share"]["target"]
    M_t = thresholds["emissions"]["target"]
    C_t = thresholds["cost"]["target"]

    def make_problem():
        prob = pulp.LpProblem("iran_energy_cDSP", pulp.LpMinimize)
        x = {t: pulp.LpVariable(f"x_{t}", 0, build_limits[t]) for t in CANDIDATES}
        g = {t: energy_twh(CF[t], K_EXIST[t] + x[t]) for t in CANDIDATES}
        renew = pulp.lpSum(g.values())
        gas_max = gas_max_generation()
        g_gas = pulp.LpVariable("g_gas", 0, gas_max)
        prob += (g_gas >= D - renew), "residual_gas"
        total = renew + g_gas
        cost = pulp.lpSum(g[t] * COST[t] / 1000.0 for t in CANDIDATES) + g_gas * COST["gas_fixed"] / 1000.0
        emis = g_gas * EMIT["gas_fixed"]
        dR_u = pulp.LpVariable("dR_u", 0); dR_o = pulp.LpVariable("dR_o", 0)
        dM_u = pulp.LpVariable("dM_u", 0); dM_o = pulp.LpVariable("dM_o", 0)
        dC_u = pulp.LpVariable("dC_u", 0); dC_o = pulp.LpVariable("dC_o", 0)
        prob += (renew + gas_max >= D), "demand_coverage"
        prob += (renew - R_t * total + dR_u - dR_o == 0), "goal_renewable"
        prob += (emis / M_t + dM_u - dM_o == 1), "goal_emissions"
        prob += (cost / C_t + dC_u - dC_o == 1), "goal_cost"
        h = dict(x=x, total=total, renew=renew, cost=cost, emis=emis, D=D, g_gas=g_gas,
                 dR_u=dR_u, dR_o=dR_o, dM_u=dM_u, dM_o=dM_o, dC_u=dC_u, dC_o=dC_o)
        return prob, h

    def penalties(h):
        return {"renewable": h["dR_u"] / (R_t * DEMAND["point"]),
                "emissions": h["dM_o"], "cost": h["dC_o"]}

    if mode == "archimedean":
        if weights is None:
            weights = {"renewable": 1/3, "emissions": 1/3, "cost": 1/3}
        prob, h = make_problem(); pen = penalties(h)
        prob += pulp.lpSum(weights[k] * pen[k] for k in GOAL_KEYS), "Z"
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        return _extract(prob, h, mode, weights=weights, demand_scenario=demand_scenario)

    elif mode == "preemptive":
        frozen = []; last = None
        for lvl, key in enumerate(priorities):
            prob, h = make_problem(); pen = penalties(h)
            for (fk, fval) in frozen:
                if fval is not None:
                    prob += (penalties(h)[fk] <= fval + 1e-6), f"freeze_{fk}"
            prob += pen[key], f"Z_{lvl}_{key}"
            prob.solve(pulp.PULP_CBC_CMD(msg=0))
            val = pulp.value(pen[key]) if pulp.LpStatus[prob.status] == "Optimal" else None
            frozen.append((key, val)); last = (prob, h)
        prob, h = last
        return _extract(prob, h, mode, priorities=priorities, demand_scenario=demand_scenario)


def _extract(prob, h, mode, weights=None, priorities=None, demand_scenario=None):
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return {"status": status, "mode": mode, "weights": weights, "priorities": priorities,
                "demand_scenario": demand_scenario, "demand_design_TWh": h["D"],
                "x_add_GW": None, "supply_TWh": None, "renewable_share": None,
                "emissions_Mt": None, "cost_bnUSD": None, "deviations": None}
    v = lambda z: pulp.value(z)
    k_add = {t: v(h["x"][t]) for t in CANDIDATES}
    D = h["D"]
    return {"status": status, "mode": mode, "weights": weights, "priorities": priorities,
            "demand_scenario": demand_scenario, "x_add_GW": k_add, "total_cap_GW": total_cap(k_add),
            "supply_TWh": total_gen(k_add, D), "demand_design_TWh": D,
            "renewable_share": renewable_share(k_add, D), "emissions_Mt": annual_emissions(k_add, D),
            "cost_bnUSD": annual_cost(k_add, D),
            "deviations": {"renewable_under": v(h["dR_u"]), "renewable_over": v(h["dR_o"]),
                           "emissions_under": v(h["dM_u"]), "emissions_over": v(h["dM_o"]),
                           "cost_under": v(h["dC_u"]), "cost_over": v(h["dC_o"])}}


# ======================================================================
# REDUCTION CHECK
# ======================================================================
def ried_reduction_check(demand_scenario="point"):
    D = demand_design_value(demand_scenario)
    out = {}
    for name, k_add in NAMED_CONFIGS.items():
        feasible = (supply_adequate(k_add, D)
                    and renewable_share(k_add, D) >= THRESHOLDS["renewable_share"]["target"]
                    and annual_emissions(k_add, D) <= THRESHOLDS["emissions"]["target"])
        screened_ok = screen_config(name, k_add, D)["status"].startswith("Acceptable")
        out[name] = {"cDSP feasible when all requirements are rigid": feasible,
                     "Accepted by the screening stage": screened_ok,
                     "Match": feasible == screened_ok}
    return pd.DataFrame(out).T


# ======================================================================
# MODEL-FORM SCENARIOS FOR SOLAR PV
# ======================================================================
def solar_scenarios():
    base = CF["solarpv"]; rows = []
    for label, cf in [("Retained, 0.162", 0.162), ("Optimistic, 0.20", 0.20), ("Conservative, 0.12", 0.12)]:
        CF["solarpv"] = cf
        sol = build_and_solve("point", mode="archimedean")
        rows.append({"Solar capacity-factor assumption": label,
                     "Capacity factor": cf,
                     "Added solar (GW)": round(sol["x_add_GW"]["solarpv"], 2) if sol["x_add_GW"] else None,
                     "Renewable share (%)": round(sol["renewable_share"] * 100, 1) if sol["renewable_share"] else None,
                     "Cost (bn USD/yr)": round(sol["cost_bnUSD"], 2) if sol["cost_bnUSD"] else None})
    CF["solarpv"] = base
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
    print("=" * 72)
    print("IRAN 2030 FORECAST-INFORMED cDSP")
    print("=" * 72)
    print(f"Renewable generation, existing fleet : {renewable_gen_add({}):.2f} TWh")
    print(f"Gas fleet maximum output             : {gas_max_generation():.2f} TWh")
    print(f"Renewable maximum, 2030 build limits : {max_renewable_generation():.2f} TWh")
    print(f"System maximum generation, 2030      : {max_system_generation():.2f} TWh")
    print(f"External projection (central)        : {DEMAND['point']:.2f} TWh")
    print(f"Earlier forecasting work             : {DEMAND['earlier_forecast']:.1f} TWh")
    d = DEMAND['point'] - DEMAND['earlier_forecast']
    print(f"Difference                           : {d:.2f} TWh = {d/DEMAND['earlier_forecast']*100:.2f}%")
