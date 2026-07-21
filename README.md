# Forecast Informed cDSP

A credibility-aware procedure for mapping forecast-informed quantities and stakeholder
requirements onto the compromise Decision Support Problem, demonstrated on a national
energy-planning decision.

Computational companion to *From Forecasts to Decisions: A Credibility-Aware Procedure for
Mapping Uncertain Predictions onto Satisficing Configuration Decisions*
(Systems Realization Laboratory, University of Oklahoma).

---

## What this is

Designers commit to a configuration before the conditions that determine its success are
known. Forecasting supplies estimates of those conditions with uncertainty intervals, but a
forecast does not by itself say which configuration to choose, nor how much to trust each
forecasted quantity: some rest on strong data and stable models, others on sparse data or on
assumptions to which the forecast is highly sensitive.

This repository implements a procedure that answers the following research question.

> How can designers systematically connect forecast-informed quantities, evidence about data
> credibility and model sensitivity, and stakeholder-defined requirements to support
> traceable satisficing-based configuration decisions under uncertainty?

The procedure separates two decisions that are commonly combined:

1. **The role of a quantity.** Whether it acts as a fixed input, a decision variable, a
   bound, a non-negotiable requirement, a desired target, or a scenario. Determined by the
   function of the quantity in the problem.
2. **The use of its value.** Whether it is used as reported, widened, qualified, or tested
   across model forms. Determined by the credibility of the supporting data and the
   sensitivity of the forecast to defensible modeling choices.

The second decision is organized as a response table spanning three levels of data
credibility and three levels of model-form sensitivity, with stated classification criteria
and operational actions so that other researchers can apply it consistently.

The compromise Decision Support Problem is used as the formal satisficing construct. The
information-mapping principles apply equally to other satisficing or threshold-based
approaches that distinguish rigid requirements from desired performance targets.

## Repository contents

| File | Purpose |
|---|---|
| `Iran_cDSP_Implementation.ipynb` | Main notebook. Reproduces every number, table, and figure reported in the paper. |
| `iran_cdsp.py` | The decision model: documented coefficients with provenance, annual energy balance with residual gas dispatch, the screening stage, and the compromise DSP in weighted and priority forms. |
| `make_figures.py` | Generates the four figures at the physical size they occupy in the manuscript. |
| `requirements.txt` | Python dependencies. |

## Quick start

```bash
git clone https://github.com/<your-account>/forecast-informed-cdsp.git
cd forecast-informed-cdsp
pip install -r requirements.txt
jupyter notebook Iran_cDSP_Implementation.ipynb
```

Run the cells in order. `make_figures.py` writes to `figs/`, which is created on first run.
Results are deterministic; a fixed seed is set for any step involving resampling.

To reproduce the key numbers without the notebook:

```bash
python iran_cdsp.py      # system totals and the two demand values
python make_figures.py   # the four figures
```

## The demonstration

How much new renewable generation capacity should a country add for a planning year, given
an uncertain demand forecast and competing stakeholder requirements for renewable share,
emissions, and cost?

- **Candidate technologies:** solar photovoltaic, hydroelectric, geothermal, biofuel.
- **Fixed background:** the existing thermal fleet, which the decision does not build or retire.
- **Dispatch:** gas generation is the residual needed to meet demand after renewables, capped
  by the fleet maximum, so added renewable capacity displaces gas rather than adding to it.
  This is what makes emissions and cost respond to the decision.
- **Scope:** an annual energy balance for a single country. Hourly dispatch, transmission,
  storage operation, reserve margins, and regional differences are outside the model.

Two stages are used. The first screens four named configurations built by stated rules and
classifies each as acceptable, flagged, or rejected. The second searches the allowable design
space with continuous decision variables and is **not** restricted to the configurations named
in the first stage.

## Selected results

| Quantity | Value |
|---|---|
| Existing system generation | about 373 TWh/yr |
| Largest annual generation the 2030 system can deliver | 414.4 TWh/yr |
| Demand, earlier forecast on the project dataset | 377.1 TWh/yr |
| Demand, external country-specific projection | 389.8 TWh/yr (difference 3.4%) |
| Screening outcome | 2 configurations acceptable, 2 rejected on demand adequacy |
| Compromise solution at the central projection | +8.93 GW solar, +0.20 GW geothermal, +0.80 GW biofuel, 10% renewable share |
| Solar capacity required, conservative vs optimistic capacity factor | 14.0 GW vs 7.9 GW |

Three findings from varying the demand value:

1. The earlier forecast and the external projection give configurations that satisfy the same
   requirements at the same renewable share, differing only in the scale of the build.
2. The renewable share holds at its target until demand approaches the upper end of the
   interval, where the capacity limit of the incumbent fleet forces it higher.
3. Five percent above the upper end of the interval, no feasible configuration exists within
   the stated build limits. This identifies a capacity-adequacy limit that no adjustment of
   goal priorities can overcome.

## Data provenance

Every engineering coefficient comes from a documented public source and is recorded with its
provenance in the `PROVENANCE` dictionary in `iran_cdsp.py`. Sources include IRENA renewable
capacity statistics and cost reports, national thermal-fleet reporting, the Lazard levelized
cost analysis, IPCC lifecycle emission factors, the national renewable programme target, and
a peer-reviewed national demand study.

Where no value specific to the country is published, a documented global representative value
is used and identified as such. This is itself an application of the credibility reasoning the
procedure describes: a global representative value carries medium credibility rather than high
and is treated accordingly.

## Verification

The notebook verifies the solution against the conditions a compromise solution must satisfy:

- each goal equation holds in its normalized form,
- at most one deviation of each pair is positive,
- all deviation variables are non-negative,
- the demand requirement is met.

It also confirms that when every requirement is treated as rigid, the set the compromise DSP
admits as feasible equals the set the screening stage accepts, on every named configuration.
The compromise formulation therefore extends the screening procedure rather than replacing it.

## Scope and limitations

- An annual energy balance for a single country, without hourly dispatch, transmission,
  storage operation, or reliability margins.
- Several inputs are documented global representative values rather than measured national
  ones, identified as such in the traceability record.
- Four candidate technologies, those for which the case provides data.
- Uncertainty is examined through scenarios rather than through a probability model.

The contribution is the procedure and its demonstration, not a forecast of any country's
energy future.

## Citation

<!-- Complete this block once the paper has a venue and a DOI. -->

```
Systems Realization Laboratory, University of Oklahoma.
"From Forecasts to Decisions: A Credibility-Aware Procedure for Mapping Uncertain
Predictions onto Satisficing Configuration Decisions." Manuscript in preparation.
```

## License

<!-- Choose a license before making the repository public. MIT is a common choice for
     research code; CC BY 4.0 is common for accompanying data and figures. -->
