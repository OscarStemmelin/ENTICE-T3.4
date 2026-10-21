import glob
import os
import pandas as pd
import re

PATH_WRK = "C:/Users/oscar/Desktop/ENTICE T3.4/"

BASE = "EXIOBASE" # EXIOBASE, FIGARO, OECD_ICIO, CAPITAL, GTAP, FDI, or Patents_Citation

YEARS = [2020]
#[1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,
# 2014,2015,2016,2017,2018,2019,2020,2021,2022]

RD_UNIT = "volume"        # "value" -> RDV files (current prices, SRDV) | "volume" -> RDQ files (2020 prices, SRDQ)

DIMENSION = "(c,s)"      # "(c,s)" without technology | "(c,s,t)" with technology

# Technologies computed by know_calc_loop when DIMENSION == "(c,s,t)": list of codes / patterns ("TG*" = every code starting
# with TG), or dict {name: [codes]} to group codes. 3 codes are advised (each one is a full pass of the metrics).
TECHS = ["TJ11", "TJ07", "TJ01"]

def _tech_labels(techs):
    keys = list(techs.keys()) if isinstance(techs, dict) else list(techs)
    return [re.sub(r"[^A-Za-z0-9_+-]+", "x", str(k)) for k in keys]   # same rule as tech_specs() of know_calc_loop


if RD_UNIT not in ("value", "volume"):
    raise ValueError(f"RD_UNIT must be 'value' or 'volume', got {RD_UNIT!r}")
if DIMENSION not in ("(c,s)", "(c,s,t)"):
    raise ValueError(f"DIMENSION must be '(c,s)' or '(c,s,t)', got {DIMENSION!r}")

TECH_LABELS = _tech_labels(TECHS) if DIMENSION == "(c,s,t)" else []
if DIMENSION == "(c,s,t)":
    YEARS = [y for y in YEARS if 2000 <= y <= 2021]   # the (c,s,t) files cover 2000-2021 only

OUTPUT_ROOT = ("SRDV" if RD_UNIT == "value" else "SRDQ") + f"_{DIMENSION}"   # folder written by know_calc_loop
SRC_DIRS = ([PATH_WRK + f"{OUTPUT_ROOT}/{t}/" for t in TECH_LABELS] if DIMENSION == "(c,s,t)" else [PATH_WRK + OUTPUT_ROOT + "/"])

# folders written by know_calc_loop: "SRDV_(c,s)" / "SRDQ_(c,s)", or one folder per technology of TECHS in (c,s,t)
# (RD_UNIT, DIMENSION and TECHS are set at the top of this script)
OUT_DIRS = SRC_DIRS
MAP_DIR = PATH_WRK + "mapping/final_aggregation"
BASES = [BASE]
# BASES = ["FIGARO", "EXIOBASE", "CAPITAL", "GTAP", "FDI", "OECD_ICIO", "Patents_Citation"]

MATRIX_PREFIXES = ["rd_dir_CI", "rd_embod_CI", "rd_imp_CI", "rd_dir_CAPITAL", "rd_embod_CAPITAL",
                   "rd_dir_cit", "rd_dir_fdips"]

# rd_dir_cit (Patents_Citation) is not a mario-based matrix: it has only 2
# column levels (Region, Sector) instead of 3 (Region, Level, Item), and an
# extra "Year" level on the rows (Year, Region, Sector) -- needs its own parser
ASYMMETRIC_PREFIXES = {"rd_dir_cit"}

# "long" files Region[,Sector] + year columns, separator ";"
# -> a single file (all years as columns), in SRDQ_(c,s)/{base}/output_loop_{base}/
LONG_SECTOR_FILES = ["production_{base}.csv", "exports_{base}.csv", "imports_intermediate_{base}.csv"]

# "long" files with no Sector column (Region + year columns only) -> no sector
# aggregation needed, just copied as-is under the _agg name
NO_SECTOR_FILES = ["imports_final_demand_{base}.csv"]


def load_mapping(base):
    p = os.path.join(MAP_DIR, f"map_agg_{base}.xlsx")
    df = pd.read_excel(p, sheet_name="Sector", dtype=str)
    # column "nace_code (aggregated)" = the base's own aggregation target (source, e.g. "C20_C21")
    # column "nace_code (common)" = the common final sector (destination, e.g. "C20+C21")
    return dict(zip(df["nace_code (aggregated)"], df["nace_code (common)"]))


def warn_unmapped(items, mapping, source):
    # sectors present in the file but missing from the base's map_agg:
    # kept as-is (identity) instead of raising -- the state of the mapping
    # is left to the user to handle.
    missing = sorted(set(items) - set(mapping))
    if missing:
        print(f"  [warning] {os.path.basename(source)}: sectors missing from map_agg (kept as-is) -> {missing}")
    return missing


def apply_mapping(values, mapping):
    return [mapping.get(v, v) for v in values]


def aggregate_matrix_file(path, mapping):
    df = pd.read_csv(path, sep=";", header=[0, 1, 2], index_col=[0, 1, 2])
    df.index.names = df.columns.names = ["Region", "Level", "Item"]
    warn_unmapped(df.index.get_level_values("Item").unique(), mapping, path)

    idx = df.index.to_frame(index=False)
    idx["Item"] = apply_mapping(idx["Item"], mapping)
    df.index = pd.MultiIndex.from_frame(idx)

    cols = df.columns.to_frame(index=False)
    cols["Item"] = apply_mapping(cols["Item"], mapping)
    df.columns = pd.MultiIndex.from_frame(cols)

    df = df.groupby(level=["Region", "Level", "Item"]).sum()               # rows
    df = df.T.groupby(level=["Region", "Level", "Item"]).sum().T           # columns
    return df.sort_index().sort_index(axis=1)


def aggregate_citation_matrix_file(path, mapping):
    # columns: 2 levels (Region, Sector) ; rows: 3 levels (Year, Region, Sector)
    df = pd.read_csv(path, sep=";", header=[0, 1], index_col=[0, 1, 2])
    df.index.names = ["Year", "Region", "Sector"]
    df.columns.names = ["Region", "Sector"]
    warn_unmapped(df.index.get_level_values("Sector").unique(), mapping, path)

    idx = df.index.to_frame(index=False)
    idx["Sector"] = apply_mapping(idx["Sector"], mapping)
    df.index = pd.MultiIndex.from_frame(idx)

    cols = df.columns.to_frame(index=False)
    cols["Sector"] = apply_mapping(cols["Sector"], mapping)
    df.columns = pd.MultiIndex.from_frame(cols)

    df = df.groupby(level=["Year", "Region", "Sector"]).sum()               # rows
    df = df.T.groupby(level=["Region", "Sector"]).sum().T                   # columns
    return df.sort_index().sort_index(axis=1)


def aggregate_long_file(path, mapping):
    df = pd.read_csv(path, sep=";", dtype={"Region": str, "Sector": str})
    warn_unmapped(df["Sector"].unique(), mapping, path)
    df["Sector"] = apply_mapping(df["Sector"], mapping)
    year_cols = [c for c in df.columns if c not in ("Region", "Sector")]
    return df.groupby(["Region", "Sector"], as_index=False)[year_cols].sum()


def out_path(path):
    root, ext = os.path.splitext(path)
    return root + "_agg" + ext


def is_already_aggregated(path):
    return path.endswith("_agg.csv")


def run_base(base, out_dir):
    mapping = load_mapping(base)
    done = 0
    base_dir = os.path.join(out_dir, base)
    if not os.path.isdir(base_dir):
        print(f"[{base}] folder missing, skipped: {base_dir}")
        return

    for year_dir in sorted(glob.glob(os.path.join(base_dir, f"output_loop_{base}_*"))):
        for prefix in MATRIX_PREFIXES:
            aggregator = aggregate_citation_matrix_file if prefix in ASYMMETRIC_PREFIXES else aggregate_matrix_file
            for f in glob.glob(os.path.join(year_dir, f"{prefix}_{base}_*.csv")):
                if is_already_aggregated(f):
                    continue
                aggregator(f, mapping).to_csv(out_path(f), sep=";")
                done += 1

    no_year_dir = os.path.join(base_dir, f"output_loop_{base}")
    if os.path.isdir(no_year_dir):
        for pattern in LONG_SECTOR_FILES:
            f = os.path.join(no_year_dir, pattern.format(base=base))
            if os.path.exists(f) and not is_already_aggregated(f):
                aggregate_long_file(f, mapping).to_csv(out_path(f), sep=";", index=False)
                done += 1

        for pattern in NO_SECTOR_FILES:
            f = os.path.join(no_year_dir, pattern.format(base=base))
            if os.path.exists(f) and not is_already_aggregated(f):
                pd.read_csv(f, sep=";").to_csv(out_path(f), sep=";", index=False)
                done += 1

    print(f"[{base}] _agg files created: {done} ({out_dir})")


if __name__ == "__main__":
    for out_dir in OUT_DIRS:
        for b in BASES:
            try:
                run_base(b, out_dir)
            except Exception as e:
                print(f"[{b}] ERROR ({out_dir}): {e}")