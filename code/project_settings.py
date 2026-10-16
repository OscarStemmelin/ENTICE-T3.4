PATH_WRK = "C:/Users/oscar/Desktop/ENTICE T3.4/"
BASE = "EXIOBASE" # EXIOBASE, FIGARO, OECD_ICIO, CFC, GTAP, FDI, or Patents_Citation
METRIC_WANTED = "dir" # dir or embod
MODELES = ["all", "faible", "forte"] # None, faible, or forte
YEARS = [2010]
#[1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,
# 2014,2015,2016,2017,2018,2019,2020,2021,2022]
METRIC_SPE = {
    "EXIOBASE_dir": "rd_dir_CI",
    "EXIOBASE_embod": "rd_embod_CI",
    "GTAP_dir": "rd_dir_CI",
    "GTAP_embod": "rd_embod_CI",
    "FIGARO_dir": "rd_dir_CI",
    "FIGARO_embod": "rd_embod_CI",
    "OECD_ICIO_dir": "rd_dir_CI",
    "OECD_ICIO_embod": "rd_embod_CI",
    "CFC_dir": "rd_dir_CFC",
    "CFC_embod": "rd_embod_CFC",
    "FDI_dir": "rd_dir_fdips",
    "Patents_Citation_dir": "rd_dir_cit"
}
METRIC = METRIC_SPE[f"{BASE}_{METRIC_WANTED}"]


# ============================================================
# R&D DATA AND TECHNOLOGY DIMENSION
# Used by know_calc_loop and by the programs that follow it (aggregate_to_common_mapping, calc_blocs,
# création_panel_F, est_all_bases, graph_final_results, graphs_output_general).
# ============================================================
RD_UNIT = "value"        # "value" -> RDV files (current prices, SRDV) | "volume" -> RDQ files (2020 prices, SRDQ)
DIMENSION = "(c,s)"      # "(c,s)" without technology | "(c,s,t)" with technology
# Technologies computed by know_calc_loop when DIMENSION == "(c,s,t)": list of codes / patterns ("TG*" = every code starting
# with TG), or dict {name: [codes]} to group codes. 3 codes are advised (each one is a full pass of the metrics).
TECHS = ["TJ11", "TJ07", "TJ01"]
# Technology analysed by calc_blocs / création_panel / estimation / graphs (one name of TECHS, or the key of the dict).
# One technology at a time: change it and run the chain again to analyse another one.
TECH = "TJ11"

# ---- derived paths: do not edit ---------------------------------------------------------------------------------------
import os
import re


def _tech_labels(techs):
    keys = list(techs.keys()) if isinstance(techs, dict) else list(techs)
    return [re.sub(r"[^A-Za-z0-9_+-]+", "x", str(k)) for k in keys]   # same rule as tech_specs() of know_calc_loop


if RD_UNIT not in ("value", "volume"):
    raise ValueError(f"RD_UNIT must be 'value' or 'volume', got {RD_UNIT!r}")
if DIMENSION not in ("(c,s)", "(c,s,t)"):
    raise ValueError(f"DIMENSION must be '(c,s)' or '(c,s,t)', got {DIMENSION!r}")

TECH_LABELS = _tech_labels(TECHS) if DIMENSION == "(c,s,t)" else []
if DIMENSION == "(c,s,t)":
    if TECH not in TECH_LABELS:
        raise ValueError(f"TECH={TECH!r} is not one of the technologies of TECHS: {TECH_LABELS}")
    YEARS = [y for y in YEARS if 2000 <= y <= 2021]   # the (c,s,t) files cover 2000-2021 only

OUTPUT_ROOT = ("SRDV" if RD_UNIT == "value" else "SRDQ") + f" {DIMENSION}"   # folder written by know_calc_loop
RUN_DIR = OUTPUT_ROOT + (f"/{TECH}" if DIMENSION == "(c,s,t)" else "")        # one folder per technology in (c,s,t)
SRC_DIR = PATH_WRK + RUN_DIR + "/"                    # where the know_calc_loop results of the analysed run are
SRC_DIRS = ([PATH_WRK + f"{OUTPUT_ROOT}/{t}/" for t in TECH_LABELS] if DIMENSION == "(c,s,t)" else [PATH_WRK + OUTPUT_ROOT + "/"])
RESULTS_DIR = PATH_WRK + f"runs/{RUN_DIR}/"           # everything produced after the aggregation, one tree per run:
#   panel_estimation/ (calc_blocs)  panels/ (création_panel_F)  tableaux/ (est_all_bases)  graphs/  graphs_output/

_code = PATH_WRK + "code/"
PANEL_CODE_DIR = _code + [d for d in os.listdir(_code) if d.startswith("cr") and "panel" in d][0] + "/"   # accent-safe folder
