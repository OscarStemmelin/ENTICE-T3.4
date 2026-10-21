# ENTICE-T3.4

This repository computes the R&D content (direct, embodied, imported) carried by international trade flows, from MRIO databases (EXIOBASE, FIGARO, OECD_ICIO, GTAP) and three additional diffusion channels (CAPITAL, FDI, patent citations). It can be run **without a technology dimension** (R&D by country × sector, written `(c,s)`) or **with one** (R&D by country × sector × technology, written `(c,s,t)`).

- the main program: [`code/know_calc_loop.ipynb`](code/know_calc_loop.ipynb)
- the settings: variables at the top of each program (section 2)
- the mapping files: [`mapping/`](mapping)
- the R&D files (project root): `RDQ_(c,s).csv`, `RDV_(c,s).csv`, `RDQ_(c,s,t).csv`, `RDV_(c,s,t).csv`
- the results: `SRDV_(c,s)`, `SRDQ_(c,s)`, `SRDV_(c,s,t)`, `SRDQ_(c,s,t)`
- two optional programs, described at the end (section 5): the common aggregation and the graphs

## 1. Installation

**1. Adapt the Python version in the `Pipfile`.** Check the version installed on the computer (`py --version`), then, in the `[requires]` section of the `Pipfile`, set that version and delete the `python_full_version` line. Python 3.12 or 3.13 works (the project was tested with 3.13). Example for Python 3.12:

```
[requires]
python_version = "3.12"
```

**2. Open the computer's terminal** (Command Prompt on Windows) and go to the project folder:

```
cd "C:\path\to\ENTICE T3.4"
```

**3. Install `pipenv`, then the virtual environment with the right package versions:**

```
pip install pipenv
py -m pipenv sync
```

In PyCharm, then select the interpreter of this environment (its path is given by `py -m pipenv --venv`) and restart the notebook kernel.

## 2. Configuration

There is no shared settings file: **the variables are defined at the top of each program** (first cell of the notebooks, top of the `.py` script). When several programs are run one after the other, they must be given the **same values**, otherwise the optional programs (section 5) will not find the results of the main program.

| Variable | Where | Role |
|---|---|---|
| `PATH_WRK` | all three programs | project path, to be adapted first on each computer |
| `BASE` | all three programs | database to process |
| `YEARS` | all three programs | years to compute |
| `RD_UNIT`, `DIMENSION` | all three programs | unit and dimension of the R&D |
| `TECHS` | main program, common aggregation | technologies processed in `(c,s,t)` mode |
| `TECH` | graphs | the technology plotted (only one) |
| `METRIC_WANTED` | graphs | `"dir"` or `"embod"` |
| `METRICS_WANTED` | main program | metrics computed (`"ALL"` = all those of the database) |
| `VERSION_EXIO` | main program | EXIOBASE version downloaded |

Details of the common variables:

- `BASE`: `"EXIOBASE"`, `"FIGARO"`, `"OECD_ICIO"`, `"GTAP"`, `"CAPITAL"`, `"FDI"` or `"Patents_Citation"`. A run processes a single database: to process another one, change `BASE` and run again.
- `YEARS`: list of the years to compute. In `(c,s,t)` mode, it is automatically limited to 2000–2021.
- `RD_UNIT`: `"value"` (`RDV` files, current euros, stocks written `SRDV`) or `"volume"` (`RDQ` files, constant 2020 euros, stocks written `SRDQ`).
- `DIMENSION`: `"(c,s)"` (without technology) or `"(c,s,t)"` (with technology).
- `TECHS`: technologies computed in `(c,s,t)` mode, for example `["TJ11", "TJ07", "TJ01"]` (`"TG*"` = every code starting with TG). About three technologies are recommended: each one is a full computation pass.

## 3. The main program: `know_calc_loop.ipynb`

### 3.1 What it does and how to run it

For each year of `YEARS`, it downloads (if needed) and parses the MRIO database, aggregates it with `mapping/agg_base_to_rd/agg_{BASE}_to_rd.xlsx`, computes exports, imports and production, builds the R&D stock (perpetual inventory, 15% depreciation) mapped with `mapping/agg_rd_to_base/agg_rd_to_{BASE}.xlsx`, then computes the metrics below and writes them as CSV. In `(c,s,t)` mode, the stock and the metrics are recomputed for each technology, while the database is parsed only once per year.

To run it:
1. open `code/know_calc_loop.ipynb` and set the variables of the first cell (section 2);
2. check that the input data of the chosen database are in place (3.2);
3. run the cells in order.

GTAP loads very heavy files and may exceed memory (`MemoryError`): close the other programs, restart the kernel, and process only one database at a time.

| Database | Metrics computed | Channel |
|---|---|---|
| EXIOBASE, FIGARO, OECD_ICIO, GTAP | `rd_dir_CI`, `rd_embod_CI`, `rd_imp_CI` | intermediate trade flows |
| CAPITAL | `rd_dir_CAPITAL`, `rd_embod_CAPITAL` | fixed capital stock (Kbar) |
| FDI | `rd_dir_fdips` | foreign direct investment |
| Patents_Citation | `rd_dir_cit` | patent citations |

`rd_dir` is the direct R&D (first tier, with no propagation through the production chain); `rd_embod` is the total embodied R&D (`rd_dir` propagated by the Leontief inverse); `rd_imp` is `rd_embod` restricted to cross-border flows.

### 3.2 Input data

**R&D** (project root), chosen by `RD_UNIT` and `DIMENSION`:

| `RD_UNIT` | `DIMENSION` | File | Content |
|---|---|---|---|
| `volume` | `(c,s)` | `RDQ_(c,s).csv` | `year;country_code;nace_code;rd_value_volume_M€`, `;` separator, 1995–2022, constant 2020 euros |
| `value` | `(c,s)` | `RDV_(c,s).csv` | `year,country_code,nace_code,rd_value_M€`, `,` separator, 1995–2022, current euros |
| `volume` / `value` | `(c,s,t)` | `RDQ_(c,s,t).csv` / `RDV_(c,s,t).csv` | wide format, `VAR` column = `RDQ_<country>_<sector>_<technology>_<group>`, one column per year 2000–2021 |

The `(c,s,t)` files only cover manufacturing (and `J62_J63`): the other sectors have zero technological R&D. The volumes of a few countries (BR, IN, RU, RO, MX…) seem to be deflated differently there than in `(c,s)`: use with caution.

**MRIO databases and channels** (`data_raw/` folder):

| Database | How to get it | Expected location |
|---|---|---|
| EXIOBASE | automatic | `data_raw/data_EXIOBASE/` (temporary); version set by `VERSION_EXIO` in the notebook |
| FIGARO | automatic | `data_raw/data_FIGARO/` (temporary) |
| OECD_ICIO | **manual** | `data_raw/data_OECD_ICIO/2016-2022_EXT/{year}.csv` |
| GTAP | **manual** | `data_raw/V12APOW/V12APOW_MRIO_{period}/` (periods 2004, 2007, 2011, 2014, 2017, 2019, 2023; each year uses the closest period) |
| CAPITAL | EXIOBASE (auto) + Kbar **manual** | `data_raw/all_kbar/Kbar_exio_v3_8_2_{year}_cfc_pxi.mat` |
| FDI | **manual** | `data_raw/data_FDI/fdi_158_65.har` |
| Patents_Citation | **manual** | `data_raw/data_Patents_Citation/Fractional_Citations_..._prefiltered.csv` |

### 3.3 Outputs

Results go to `<OUTPUT_ROOT>/<BASE>/` (`SRDV_(c,s)`, `SRDQ_(c,s)`…). In `(c,s,t)` mode, a subfolder per technology is inserted: `SRDV_(c,s,t)/<technology>/<BASE>/`.
- `output_loop_{BASE}_{year}/`: one CSV per metric (for example `rd_dir_CI_{BASE}_{year}.csv`), square `(Region, Level, Item)` matrix, `;` separator, at the sector resolution of the database.
- `output_loop_{BASE}/`: files with all years as columns, `exports_`, `imports_intermediate_`, `imports_final_demand_` and `production_{BASE}.csv` (EXIOBASE, FIGARO, OECD_ICIO, GTAP, CAPITAL only).

## 4. The mappings (`mapping/`)

![Diagram of the mapping files](mapping/schema_mapping_en.svg)

The MRIO database (left) and the R&D file (right) are each brought by a first mapping to the same **common aggregation**, as fine as possible (middle). This is the level at which both sides must have exactly the same targets, and it sets the resolution of the results. An **additional aggregation layer** is optional (section 5.1).

| File | Role |
|---|---|
| `agg_base_to_rd/agg_{BASE}_to_rd.xlsx` | converts the database from its native nomenclature to the working nomenclature (read by `mario`); sheets `Sector` (`sector_name (BASE)` → `nace_code (aggregated)`) and `Region` (`region_code (BASE)` → `country_code (aggregated)`); `mario` reads the 1st column as source and the 2nd as target, whatever their titles |
| `agg_rd_to_base/agg_rd_to_{BASE}.xlsx` | converts the 56 NACE codes and the countries of the R&D file to the **same** working nomenclature; sheets `Sector` (`nace_code (RD)` → `nace_code (aggregated)`) and `Region` (`country_code (RD)` → `country_code (aggregated)`) |
| `final_aggregation/map_agg_{BASE}.xlsx` | optional: converts the working nomenclature to the 34 sectors common to the 7 databases (section 5.1) |

The main program finds these files through the `AGG_FILES` and `MAP_RD_FILES` dictionaries in the first cell of `know_calc_loop.ipynb`. The other files in `mapping/` (GTAP before and after 2007, FDI, citations, Kbar for CAPITAL, `Mapping_Ind_prod.xlsx`, `map_capital_iso.xlsx`) are specific to one database and read by the same notebook.

**The rule to follow:** for a given database, the target **sectors** of `agg_{BASE}_to_rd.xlsx` and `agg_rd_to_{BASE}.xlsx` must be strictly identical. A target present on one side only sets the corresponding R&D to zero, without any warning. For regions, the R&D file may have more than the database (their R&D is lost), but a region of the database missing from the R&D file will get no R&D.

**Creating or updating the mappings of a database:**
1. list the native regions and sectors of the database (for example by parsing it with `mario`) and the NACE codes of the R&D file;
2. in `agg_{BASE}_to_rd.xlsx` (copy an existing file as a template), fill in the `nace_code (aggregated)` column of the `Sector` sheet and `country_code (aggregated)` of the `Region` sheet: the aggregation must be the finest one common to both nomenclatures;
3. in `agg_rd_to_{BASE}.xlsx`, fill in `nace_code (aggregated)` and `country_code (aggregated)` for each NACE code and each country of the R&D file, with **exactly the same target labels** as in step 2 (countries absent from the database go to `RW`);
4. declare the file in `AGG_FILES` and `MAP_RD_FILES` of the main program if its name has changed or if the database is new.

## 5. Optional programs

These two programs are not needed for the computation: they use the results of the main program.

### 5.1 Common aggregation: `code/aggregate_to_common_mapping.py`

Groups the matrices produced by the main program onto a sector nomenclature common to the 7 databases (34 sectors), with `mapping/final_aggregation/map_agg_{BASE}.xlsx`, so that the databases can be compared with each other. Each result is written next to the original file with the `_agg` suffix (for example `rd_dir_CI_EXIOBASE_2015_agg.csv`); nothing is overwritten. As the matrices are already weighted by R&D intensity, summing rows or columns creates no bias. Run it after the main program, with the same `BASE`, `RD_UNIT`, `DIMENSION` and `TECHS` set at the top of the script:

```
py -m pipenv run python code/aggregate_to_common_mapping.py
```

### 5.2 Graphs: `code/graphs_output_general.ipynb`

Draws flow diagrams (Sankey) and origin decompositions from the output matrices. It scans all available *runs* (value or volume, with or without technology) and displays their catalogue at startup. By default it uses the run defined by `RD_UNIT`, `DIMENSION` and `TECH` at the top of the notebook; to plot another one, change these variables or `DEFAULT_RUN`:

```python
DEFAULT_RUN = run_id("volume", "(c,s,t)", "TJ07")   # volume, technology TJ07
```

To compare several runs on the same graph, add the run as the 4th element of each source of `plot_origin_decomposition_panels`, for example `("EXIOBASE", "rd_dir_CI", 2010, run_id("value", "(c,s)"))`. `USE_AGG = True` reads the `_agg` files instead of the matrices at each database's own resolution. The figures are written to `runs/<run>/graphs_output_loop/` (or `runs/comparison/graphs_output_loop/` for a comparison).
