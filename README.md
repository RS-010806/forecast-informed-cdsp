# forecast-informed-cdsp

A credibility-aware procedure for mapping forecast-informed quantities and stakeholder
requirements onto the compromise Decision Support Problem, demonstrated on a national
energy-planning decision.

Computational companion to *From Forecasts to Decisions: A Credibility-Aware Procedure for
Mapping Uncertain Predictions onto Satisficing Configuration Decisions*
(Shah, Hajihashemi, Allen and Mistree; Systems Realization Laboratory, University of
Oklahoma).

---

## What this is

Designers commit to a configuration years before the conditions that determine its success
are known. Researchers can supply forecasts of those conditions with uncertainty intervals,
evidence about data credibility, and evidence about how sensitive a forecast is to the
choice of model. A forecast does not by itself say which configuration to choose, nor how
much weight to place on any individual number.

This repository implements a procedure that answers the following research question.

> How can designers systematically connect forecast-informed quantities, evidence about data
> credibility and model sensitivity, and stakeholder-defined requirements to support
> traceable satisficing-based configuration decisions under uncertainty?

Through the procedure, designers separate two determinations that are commonly combined.

1. **The role of a quantity** — a fixed input, a decision variable, a bound, a
   non-negotiable requirement, a desired target, or a scenario. Settled by the function of
   the quantity in the problem.
2. **The use of its value** — used as reported, widened, qualified, or tested across model
   forms. Settled by the credibility of the data and the sensitivity of the forecast.

The second determination is organised as a response table spanning three levels of data
credibility and three levels of model-form sensitivity, with stated classification criteria
and operational actions so that other researchers can apply it consistently.

The compromise Decision Support Problem is the formal satisficing construct used in the
demonstration. The information-mapping principles apply equally to other satisficing or
threshold-based approaches that distinguish rigid requirements from desired targets.

## Repository contents

| File | Purpose |
|---|---|
| `RS_cDSP_Energy_Implementation.ipynb` | Executed notebook. Reproduces every number, table and figure in the manuscript, in the order they appear, with the paper section named for each result. |
| `iran_cdsp.py` | The decision model: provenance of every coefficient, the annual energy balance with residual dispatch, the requirements with their derivations, the named configurations with their construction rules, the compromise DSP in both forms, four baseline decision rules, four ablations, the trade-off frontier, and the verification routine. |
| `make_figures.py` | Generates all eight figures at the physical size each occupies on the manuscript page. |
| `requirements.txt` | Python dependencies. |

## Quick start

```bash
git clone https://github.com/RS-010806/forecast-informed-cdsp.git
cd forecast-informed-cdsp
pip install -r requirements.txt
jupyter notebook RS_cDSP_Energy_Implementation.ipynb
```

Run the cells in order. `make_figures.py` writes to `figs/`, created on first run. Results
are deterministic; a fixed seed is set for any step involving resampling.

To reproduce the headline numbers without the notebook:

```bash
python iran_cdsp.py      # system totals, both demand values, screening, baseline comparison
python make_figures.py   # all eight figures
```

## The demonstration

How much new renewable generation capacity should a country add for a planning year, given
an uncertain demand forecast and competing stakeholder requirements for renewable share,
emissions and cost?

- **Candidate technologies:** solar photovoltaic, hydroelectric, geothermal, biofuel. These
  are the renewable series for which the project dataset provides Iranian historical data.
  Wind, coal and nuclear are excluded because no defensible Iranian series exists, which is
  an application of the credibility criteria rather than an omission.
- **Fixed background:** the existing thermal fleet, which the decision does not build or retire.
- **Dispatch:** gas generation is the residual needed to meet demand after renewables, capped
  by the fleet maximum, so added renewable capacity displaces gas rather than adding to it.
  This is what makes emissions and cost respond to the decision.
- **Scope:** an annual energy balance for a single country. Hourly dispatch, transmission,
  storage operation, reserve margins and regional differences lie outside the boundary.

Two stages: a transparent screening of four named configurations built by stated rules, and
a search over the whole allowable design space using the compromise DSP. The second stage is
not restricted to the configurations named in the first.

## Selected results

| Quantity | Value |
|---|---|
| Existing system generation | 373.27 TWh/yr |
| Largest annual generation the 2030 system can deliver | 414.36 TWh/yr |
| Demand, our own forecast | 377.10 TWh/yr |
| Demand, external country-specific projection | 389.76 TWh/yr (a difference of 3.36 percent) |
| Renewable-share requirement | 13 percent, supported by two independent policy instruments |
| Emissions ceiling | 166.26 Mt CO2/yr, from the unconditional Paris commitment |
| Screening outcome | 1 acceptable, 1 flagged, 2 rejected on demand adequacy |
| Compromise solution | +9.78 GW solar, +3.00 hydro, +1.00 geothermal, +0.80 biofuel; 14.58 GW total; 13.0 percent renewable share |
| Against a least-cost rule | 33 percent less new capacity for the same requirement satisfaction |
| Against screening alone | 23 percent less new capacity |

Four findings worth noting.

1. **Two independent policy instruments converge.** The 30 GW national capacity target
   implies a 13.5 percent renewable share; the unconditional Paris commitment implies
   12.9 percent. A designer adopting either is close to satisfying the other.
2. **A capacity-adequacy limit exists.** Five percent above the upper end of the demand
   interval, no feasible configuration exists within the build limits, because demand exceeds
   the 414.36 TWh/yr system ceiling. No adjustment of goal priorities recovers feasibility.
3. **The conditional Paris commitment is unreachable for this fleet.** It requires a
   20.2 percent renewable share against a 15.6 percent maximum within the build limits.
4. **A highly sensitive input changes the build by 49 percent.** Under a conservative solar
   capacity factor the recommended build is 18.28 GW against 12.28 GW under an optimistic one,
   while all three model forms satisfy the same requirements.

## Data provenance

Every engineering coefficient comes from a documented public source and is recorded with its
provenance in the `PROVENANCE` dictionary in `iran_cdsp.py`. Each value carries an evidence
class stating what kind of support it has: a measurement reported for Iran, a global
representative value, a value adjusted for an Iranian condition, a value calibrated against a
reported national aggregate, our own forecast, an external forecast, or a stated policy target.

Sources: IRENA renewable capacity statistics and cost reports, Iranian national thermal-fleet
reporting, the Lazard levelized cost analysis, IPCC AR5 lifecycle emission factors, the
Iranian national renewable-capacity target, and a peer-reviewed Iranian demand and emissions
study.

## Verification

The notebook verifies the reported solution against the conditions a compromise solution must
satisfy: each goal equation holds in its normalised form, at most one deviation of each pair
is positive, all deviation variables are non-negative, and the generation delivered meets the
demand. It also confirms that when every requirement is treated as rigid, the set the
compromise DSP admits as feasible equals the set the screening stage accepts, on every named
configuration, so the compromise formulation extends the screening procedure rather than
replacing it.

## Scope and limitations

- An annual energy balance for a single country, without hourly dispatch, transmission,
  storage operation or reliability margins.
- Several inputs are documented global representative values rather than Iranian
  measurements, identified as such in the provenance record.
- The cost measure is a levelised generation cost and does not price the capital commitment
  of a larger build.
- Four candidate technologies, for the reason given above.
- Uncertainty is examined through scenarios rather than through a probability model.
- Installed-capacity data carry a year-end 2024 vintage and should be refreshed for later
  applications.

The contribution is the procedure and its demonstration, not a forecast of any country's
energy future.

## Citation

<!-- Complete once the manuscript has a venue and a DOI. -->

```
Shah, R. A., Hajihashemi, S., Allen, J. K., and Mistree, F.,
"From Forecasts to Decisions: A Credibility-Aware Procedure for Mapping Uncertain
Predictions onto Satisficing Configuration Decisions." Manuscript in preparation.
```

## License

<!-- Choose a license before making the repository public. -->
