# ENTICE T3.4

Ce dépôt calcule le contenu en R&D (directe, incorporée, importée) porté par les
flux d'échanges internationaux, à partir de plusieurs bases MRIO (EXIOBASE,
FIGARO, OECD_ICIO, GTAP) et de trois canaux de diffusion additionnels (CFC,
FDI, citations de brevets), puis construit les panels et les régressions qui en
découlent. Il peut être lancé **sans dimension technologique** (R&D par
pays × secteur, noté `(c,s)`) ou **avec** (R&D par pays × secteur × technologie,
noté `(c,s,t)`).

Ce README couvre surtout le programme principal et les mappings ; la chaîne
complète est résumée à la section 6.

- le programme principal : [`code/know_calc_loop.ipynb`](code/know_calc_loop.ipynb)
- le script d'agrégation commune : [`code/aggregate_to_common_mapping.py`](code/aggregate_to_common_mapping.py)
- les fichiers de mapping : [`mapping/`](mapping), rangés en trois sous-dossiers
  ([`agg_base_to_rd/`](mapping/agg_base_to_rd), [`agg_rd_to_base/`](mapping/agg_rd_to_base),
  [`final_aggregation/`](mapping/final_aggregation))
- les fichiers de R&D (racine du projet) : `RDQ (c,s).csv`, `RDV (c,s).csv`,
  `RDQ (c,s,t).csv`, `RDV (c,s,t).csv`
- les résultats du programme principal (`SRDV (c,s)`, `SRDQ (c,s)`, `SRDV (c,s,t)`,
  `SRDQ (c,s,t)`) et, plus loin dans la chaîne, le dossier `runs/`

## 1. Installation

Dépendances (voir [`Pipfile`](Pipfile)) : `pandas`, `numpy`, `scipy`,
`openpyxl`, `mariopy` (le package MRIO utilisé pour parser/agréger les
bases), `harpy3` (lecture des fichiers `.har` de GTAP/FDI). Python 3.13.

```bash
pipenv install
```

Les notebooks importent `project_settings`, qui se trouve dans `code/`. Ce
dossier doit donc être trouvable par Python : soit le notebook est dans `code/`,
soit `code/` est marqué « Sources Root » dans PyCharm, soit son chemin est
ajouté au `sys.path` (par exemple avec un fichier `.pth` dans l'environnement
virtuel). Après tout changement de ce type, redémarrer le noyau du notebook.

## 2. Configuration : `code/project_settings.py`

Toutes les exécutions partent du fichier `project_settings` :

- `PATH_WRK` : à modifier en premier sur toute nouvelle machine, c'est la racine
  à partir de laquelle tous les autres chemins (`mapping/`, `data_raw/`, fichiers
  de R&D, dossiers de résultats) sont construits. La cellule de configuration du
  programme principal définit aussi un `PATH_WRK` : garder les deux identiques.
- `BASE` : une valeur parmi `"EXIOBASE"`, `"FIGARO"`, `"OECD_ICIO"`, `"GTAP"`,
  `"CFC"`, `"FDI"`, `"Patents_Citation"`. Une exécution ne traite qu'**une
  seule base à la fois** ; pour en traiter plusieurs, changer `BASE` et relancer.
- `YEARS` : liste des années à calculer (les bornes réellement disponibles
  dépendent des données brutes, voir 3.3). En mode `(c,s,t)`, la liste est
  automatiquement limitée à 2000–2021.
- `RD_UNIT` : `"value"` (fichiers `RDV`, euros courants, stocks notés `SRDV`) ou
  `"volume"` (fichiers `RDQ`, euros constants 2020, stocks notés `SRDQ`).
- `DIMENSION` : `"(c,s)"` (sans technologie) ou `"(c,s,t)"` (avec technologie).
- `TECHS` : technologies calculées quand `DIMENSION = "(c,s,t)"` (ignoré sinon).
  Une liste de codes ou de motifs (`["TJ11", "TJ07", "TJ01"]` ; `"TG*"` = tous les
  codes qui commencent par TG), ou un dictionnaire `{nom: [codes]}` pour regrouper
  plusieurs codes en une seule technologie. Environ 3 technologies sont conseillées :
  chacune est une passe complète de calcul des métriques.

## 3. Le programme principal : `know_calc_loop.ipynb`

### 3.1 Ce qu'il fait

Pour chaque année de `YEARS` :
1. télécharge (si besoin) et parse la base MRIO demandée avec `mario`, puis
   l'agrège avec `mapping/agg_base_to_rd/agg_{BASE}_to_rd.xlsx` ;
2. calcule les exports, importations (intermédiaires et de demande finale) et
   la production par `(Region, Sector)` ;
3. construit le stock de R&D par méthode d'inventaire permanent (dépréciation
   de 15 %) à partir du fichier de R&D choisi par `RD_UNIT` et `DIMENSION`, mappé
   sur la même nomenclature que l'étape 1 via
   `mapping/agg_rd_to_base/agg_rd_to_{BASE}.xlsx` ;
4. calcule les métriques de diffusion demandées (voir tableau ci-dessous) ;
5. écrit tous les résultats en CSV dans `OUTPUT_ROOT`.

En mode `(c,s,t)`, les étapes 3 à 5 sont refaites **une fois par technologie**
de `TECHS`, alors que les étapes 1 et 2 (parsing, exports/imports/production,
inverse de Leontief, matrice de capital CFC) ne sont faites qu'une fois par
année et partagées entre les technologies.

Les métriques calculées dépendent de la base (`ALL_METRICS` dans `run()`) :

| Base | Métriques calculées | Canal |
|---|---|---|
| EXIOBASE, FIGARO, OECD_ICIO, GTAP | `rd_dir_CI`, `rd_embod_CI`, `rd_imp_CI` | flux d'échanges intermédiaires (Z) |
| CFC | `rd_dir_CFC`, `rd_embod_CFC` | stock de capital fixe (Kbar) |
| FDI | `rd_dir_fdips` | participations d'investissement direct étranger |
| Patents_Citation | `rd_dir_cit` | citations de brevets |

Sens de chaque métrique :
- `rd_dir` : R&D directe (premier niveau, pas de propagation dans la chaîne
  de production).
- `rd_embod` : R&D totale incorporée, `rd_dir` propagée via
  l'inverse de Leontief (tous les fournisseurs amont, domestiques et
  étrangers).
- `rd_imp` : comme `rd_embod`, restreint aux flux transfrontaliers (les
  flux domestiques, même région, sont mis à zéro).

### 3.2 Comment le lancer

1. Ouvrir `code/project_settings.py` et régler : `PATH_WRK`, `BASE`, `YEARS`,
   `RD_UNIT`, `DIMENSION` et, si `DIMENSION = "(c,s,t)"`, `TECHS` (et `TECH`
   pour la suite de la chaîne).
2. Vérifier que les données d'entrée de la base choisie sont en place (3.3) et
   que ses fichiers de mapping existent (section 4).
3. Ouvrir `code/know_calc_loop.ipynb` et exécuter les cellules dans l'ordre
   (le notebook est un script linéaire découpé en cellules, pas un ensemble de
   cellules indépendantes). `PATH_WRK`, `BASE`, `YEARS`, `RD_UNIT`, `DIMENSION`
   et `TECHS` sont lus depuis `project_settings` par la première cellule : il ne
   faut pas les redéfinir dans le notebook.
4. La dernière cellule (`if __name__ == "__main__":`) lance `run(...)` sur la
   `BASE` / les `YEARS` configurées. Un message récapitule le fichier de R&D lu et
   les dossiers où seront écrits les résultats ; en mode `(c,s,t)`, les années hors
   de 2000–2021 sont ignorées avec un avertissement.
5. Pour une autre base, une autre unité, une autre dimension ou d'autres
   technologies : modifier `project_settings.py` et relancer (redémarrer le noyau
   si le notebook a déjà tourné, pour libérer la mémoire).

Remarque : GTAP charge des fichiers très lourds (plusieurs Go) et peut
dépasser la mémoire disponible (`MemoryError` pendant `mario.parse_gtap`). Fermer
les autres programmes, redémarrer le noyau, et ne traiter qu'une base à la fois.

### 3.3 Données d'entrée requises

**R&D** (racine du projet), choisie par `RD_UNIT` et `DIMENSION` :

| `RD_UNIT` | `DIMENSION` | Fichier | Format |
|---|---|---|---|
| `volume` | `(c,s)` | `RDQ (c,s).csv` | colonnes `year;country_code;nace_code;rd_value_volume_M€`, séparateur `;`, 1995–2022, euros constants 2020 |
| `value` | `(c,s)` | `RDV (c,s).csv` | colonnes `year,country_code,nace_code,rd_value_M€`, séparateur `,`, 1995–2022, euros courants |
| `volume` | `(c,s,t)` | `RDQ (c,s,t).csv` | format large : colonne `VAR` = `RDQ_<pays>_<secteur>_<technologie>_<groupe>`, une colonne par année `2000Y1` … `2021Y1` |
| `value` | `(c,s,t)` | `RDV (c,s,t).csv` | idem avec `RDV_` |

Les volumes (`RDQ`) sont tous recalés sur 2020 (script
`code/conversion_RD.py`). Les valeurs (`RDV`) sont en euros courants et n'ont
pas d'année de référence.

Pour les fichiers `(c,s,t)` :
- le code de technologie est le 4ᵉ bloc de `VAR` ; plusieurs lignes (le « groupe »,
  dernier bloc) peuvent exister pour un même pays × secteur × technologie, elles
  sont additionnées ;
- seuls les secteurs de l'industrie manufacturière (et `J62_J63`) sont couverts ;
  les autres secteurs ont une R&D technologique nulle ;
- le code de secteur du fichier (`S20`, `261`…) est converti en `nace_code` par le
  dictionnaire `TECH_SECTOR_MAP` de la cellule de configuration du programme
  principal : à compléter si de nouveaux codes de secteur apparaissent ;
- le code `RW` (reste du monde) est écarté, faute de ligne correspondante dans les
  mappings `agg_rd_to_{BASE}.xlsx` ;
- le stock est calculé sur les années du fichier (2000–2021), un flux manquant
  compte pour 0 ;
- les volumes `(c,s,t)` de quelques pays (BR, IN, RU, RO, MX, BG, EE, HU, LV…)
  semblent déflatés différemment de ceux de `(c,s)` : à utiliser avec prudence.

**Bases MRIO et canaux** :

| Base | Récupération | Emplacement attendu | Détail |
|---|---|---|---|
| EXIOBASE | automatique (`mario.download_exiobase3`) | `data_raw/data_EXIOBASE/` (temporaire, supprimé après chaque année) | version fixée par `VERSION_EXIO` dans le notebook |
| FIGARO | automatique (`mario.parse_figaro`) | `data_raw/data_FIGARO/` (temporaire) | téléchargé et parsé en un seul appel |
| OECD_ICIO | **manuelle** | `data_raw/data_OECD_ICIO/2016-2022_EXT/{année}.csv` | un CSV par année, 2016 à 2022 |
| GTAP | **manuelle** | `data_raw/V12APOW/V12APOW_MRIO_{période}/` (CSV) | périodes disponibles : 2004, 2007, 2011, 2014, 2017, 2019, 2023 ; chaque année de `YEARS` est associée à la période la plus proche (voir `run()`) |
| CFC | réutilise EXIOBASE (auto) + Kbar **manuel** | `data_raw/all_kbar/Kbar_exio_v3_8_2_{année}_cfc_pxi.mat` | un fichier `.mat` par année (matrice de capital fixe) |
| FDI | statique, **manuelle** | `data_raw/data_FDI/fdi_158_65.har` | fichier `.har` (matrice FDIP source × hôte × secteur), lu avec `harpy` |
| Patents_Citation | statique, **manuelle** | `data_raw/data_Patents_Citation/Fractional_Citations_..._prefiltered.csv` | un seul fichier, filtré par année dans le code |

### 3.4 Sorties

Les résultats vont dans `<OUTPUT_ROOT>/<BASE>/` (`SRDV (c,s)`, `SRDQ (c,s)`,
`SRDV (c,s,t)` ou `SRDQ (c,s,t)`). En mode `(c,s,t)`, **un sous-dossier par
technologie** s'intercale : `SRDV (c,s,t)/<technologie>/<BASE>/`, avec exactement
la même organisation qu'en `(c,s)` :

- `output_loop_{BASE}_{année}/` : un CSV par métrique calculée cette
  année-là (ex. `rd_dir_CI_{BASE}_{année}.csv`). Format : matrice carrée
  `(Region, Level, Item)` en lignes et en colonnes, séparateur `;`, à la
  résolution sectorielle propre à la base (celle de
  `mapping/agg_base_to_rd/agg_{BASE}_to_rd.xlsx`).
- `output_loop_{BASE}/` (sans année) : fichiers globaux toutes années en
  colonnes — `exports_{BASE}.csv`, `imports_intermediate_{BASE}.csv`,
  `production_{BASE}.csv` (colonnes `Region, Sector, <année>, ...`) et
  `imports_final_demand_{BASE}.csv` (colonnes `Region, <année>, ...`, pas de
  détail sectoriel). Uniquement pour EXIOBASE, FIGARO, OECD_ICIO, GTAP, CFC
  (FDI et Patents_Citation n'ont pas de Z/Y, donc pas d'exports/imports/
  production). En mode `(c,s,t)`, ces fichiers sont recopiés dans le dossier de
  chaque technologie.

## 4. Les mappings (`mapping/`)

### 4.1 Organisation

![Schéma des fichiers de mapping](mapping/schema_mapping.svg)

*Lecture du schéma (fichier source : [`mapping/schema_mapping.svg`](mapping/schema_mapping.svg)) : la base MRIO (à gauche) et le fichier de R&D (à droite) sont chacun ramenés par un premier mapping à une même **agrégation commune**, la plus fine possible, au milieu. C'est à ce niveau que les deux côtés doivent avoir exactement les mêmes cibles (encadré rouge), et c'est ce niveau qui fixe la résolution des résultats du programme principal. En dessous, une **couche d'agrégation supplémentaire** est facultative : elle consiste à regrouper davantage avec un fichier de mapping en plus (`map_agg_{BASE}.xlsx`). Dans ce projet, elle sert à ramener les 7 bases à une même nomenclature de 34 secteurs pour pouvoir les comparer.*

Chaque base a besoin de **deux** fichiers de mapping obligatoires, plus un troisième
facultatif (la couche d'agrégation supplémentaire), rangés chacun dans son sous-dossier :

| Fichier | Rôle | Feuilles / colonnes clés |
|---|---|---|
| `agg_base_to_rd/agg_{BASE}_to_rd.xlsx` | Passe la base de sa nomenclature native à sa nomenclature de travail. Consommé par `mario` (`db.aggregate(...)`). | format `mario` : feuilles `Sector` et `Region` (et `Factor of production`, `Satellite account`, `Consumption category`), 1ʳᵉ colonne = libellé natif, colonne `Aggregation` = cible |
| `agg_rd_to_base/agg_rd_to_{BASE}.xlsx` | Passe les codes NACE du fichier de R&D (56 codes) à la **même** nomenclature de travail que le fichier ci-dessus, pour que le stock de R&D et la base MRIO s'alignent exactement. | feuille `Sector` : `nace_code` → `aggregation` ; feuille `Region` : `country_code` → `aggregation` |
| `final_aggregation/map_agg_{BASE}.xlsx` | Passe la nomenclature de travail de la base (celle des deux fichiers ci-dessus) à la nomenclature **commune aux 7 bases** (34 secteurs). Utilisé uniquement par le script d'agrégation (section 5), pas par le programme principal. | feuille `Sector` : `Sector` (cible de la base) → `aggregation` (secteur final commun) |

Autres fichiers :
- `final_aggregation/dict_oecd_stan.xlsx` (feuille `Sector` : code OECD STAN →
  secteur commun) et `final_aggregation/dict_region_stan.xlsx` (feuille `region` :
  code pays OECD à 3 lettres → code région à 2 lettres) : rattachent les données
  de valeur ajoutée STAN aux secteurs et régions communs (lus par
  `prépa_va_STAN.ipynb`).
- Spécifiques aux bases : `agg_base_to_rd/agg_GTAPpost2007_to_rd.xlsx` et
  `agg_GTAPpre2007_to_rd.xlsx` (GTAP, années > 2007 et ≤ 2007),
  `agg_base_to_rd/agg_FDI_to_rd.xlsx`, `agg_base_to_rd/agg_Patents_Citation_to_rd.xlsx`
  (formats propres : `gtap_region` / `gtap_sector` → `aggregation` /
  `aggregation_nace` pour FDI, `citation_code` / `citation_region` pour les
  citations), `agg_base_to_rd/agg_Kbar_to_rd.xlsx` (agrégation du Kbar de CFC),
  `Mapping_Ind_prod.xlsx` (produit → industrie, CFC), `map_cfc_iso.xlsx`
  (ISO3 → ISO2, CFC). `map_rd_Kbar.xlsx` n'est référencé par aucun programme
  actuel.

Le programme principal sait quel fichier lire grâce à deux dictionnaires de la
première cellule de `know_calc_loop.ipynb`, plus les chemins de `PATHS` :

```python
AGG_FILES = {            # base -> fichier base -> nomenclature de travail (dans mapping/)
    "EXIOBASE": "agg_base_to_rd/agg_EXIOBASE_3.8.22_to_rd.xlsx",
    "CFC": "agg_base_to_rd/agg_CFC_3.8.2_to_rd.xlsx",
    "GTAP": "agg_base_to_rd/agg_GTAPpost2007_to_rd.xlsx",   # + agg_gtap / agg_gtap2 dans PATHS pour post / pre 2007
    ...
}
MAP_RD_FILES = {         # base -> fichier R&D -> nomenclature de travail (dans mapping/)
    "EXIOBASE": "agg_rd_to_base/agg_rd_to_EXIOBASE.xlsx",
    ...
}
```

### 4.2 La règle à respecter

Pour une base donnée, l'ensemble des **secteurs** cibles de
`agg_{BASE}_to_rd.xlsx` et l'ensemble des cibles de `agg_rd_to_{BASE}.xlsx` doivent
être strictement identiques. Si une cible existe d'un côté mais pas de l'autre, la
R&D correspondante est silencieusement mise à zéro (comportement de
`build_rd_extensions_for_year`, sans avertissement dans le programme principal).
Pour les **régions**, le fichier de R&D peut en avoir davantage que la base (la
R&D des pays absents de la base est simplement perdue), mais toute région de la
base absente du fichier de R&D n'aura aucune R&D. Le script d'agrégation signale,
lui, les secteurs qu'il ne trouve pas dans `map_agg_{BASE}.xlsx`.

### 4.3 Construire ou mettre à jour les mappings d'une base

À faire pour une nouvelle base, ou quand un fichier source change de
nomenclature :

1. **Lister les nomenclatures sources** : régions et secteurs natifs de la base
   (par exemple en parsant la base avec `mario` et en listant ses index `Sector` et `Region`) et les codes
   NACE de la colonne `nace_code` du fichier de R&D (`RDV (c,s).csv`).
2. **`agg_base_to_rd/agg_{BASE}_to_rd.xlsx`** : copier un fichier existant de
   même type comme modèle (il garde la structure de feuilles attendue par `mario`),
   puis remplir la colonne `Aggregation` des feuilles `Sector` et `Region`.
3. **`agg_rd_to_base/agg_rd_to_{BASE}.xlsx`** : remplir `aggregation` pour chacun
   des 56 `nace_code` (feuille `Sector`) et chacun des `country_code` du fichier
   de R&D (feuille `Region`), avec **exactement les mêmes libellés de cible** qu'à
   l'étape 2. Les pays qui ne font pas partie de la base vont dans `RW`.
4. **`final_aggregation/map_agg_{BASE}.xlsx`** : pour chaque cible de la
   nomenclature de travail, indiquer le secteur commun correspondant.
5. **Enregistrer la base** dans `AGG_FILES` et `MAP_RD_FILES` du programme
   principal si le nom du fichier a changé ou si c'est une nouvelle base.

Les trois fichiers ne répondent pas à la même logique d'agrégation :

- **`agg_{BASE}_to_rd.xlsx` et `agg_rd_to_{BASE}.xlsx`** : l'agrégation doit
  être la **plus fine possible commune** aux deux nomenclatures sources — celle
  de la base MRIO (régions/secteurs natifs) et celle du fichier de R&D
  (56 codes NACE). On ne vise pas ici le niveau d'agrégation final à 34
  secteurs : on descend seulement jusqu'au point où les deux nomenclatures
  cessent d'avoir une correspondance 1-pour-1 (ex. la base distingue deux
  secteurs que le NACE à 56 postes ne distingue pas, ou inversement), et on
  agrège uniquement à partir de là. **Tous les secteurs doivent être représentés**
  des deux côtés (règle 4.2). C'est cette étape qui fixe la résolution
  sectorielle des sorties `output_loop_{BASE}_{année}/` (section 3.4).
- **`map_agg_{BASE}.xlsx`** : l'agrégation est libre — c'est ici qu'on choisit
  jusqu'où regrouper la nomenclature de travail de la base pour obtenir des
  libellés comparables entre les 7 bases. Les cibles choisies doivent
  correspondre aux secteurs communs de `dict_oecd_stan.xlsx` (colonne `Sector` : les
  34 secteurs communs, plus `C` et `H` qui sont les agrégats STAN de l'industrie
  manufacturière et des transports) et aux codes
  région à 2 lettres de `dict_region_stan.xlsx` — c'est ce qui permet ensuite de
  rattacher les résultats agrégés aux données de valeur ajoutée OECD STAN pour
  le panel d'estimation.

### 4.4 Les codes de secteur des fichiers `(c,s,t)`

Le dictionnaire `TECH_SECTOR_MAP` (cellule de configuration du programme
principal) relie les codes de secteur de `RDQ/RDV (c,s,t).csv` aux `nace_code` du
fichier `(c,s)` (`S20` → `C20`, `261` → `C261`, `S62` → `J62_J63`…). C'est ensuite
le mapping habituel `agg_rd_to_{BASE}.xlsx` qui prend le relais : il n'y a pas de
fichier de mapping supplémentaire pour la technologie.

## 5. Script d'agrégation commune : `code/aggregate_to_common_mapping.py`

### Pourquoi un script séparé, après coup

Le programme principal calcule déjà les métriques (`rd_dir_CI`, etc.) à la
résolution sectorielle propre à chaque base — c'est-à-dire avec l'intensité de
R&D (`e`) calculée à la résolution la plus fine possible pour cette base.
Sommer ensuite des lignes/colonnes d'un résultat déjà pondéré par `e` est une
simple addition, sans biais :

```
(e_i · Z_i) + (e_j · Z_j) = e · (Z_i + Z_j)     si e_i = e_j = e
```

### Ce qu'il fait

Pour la `BASE` de `project_settings` (liste `BASES` en tête du script pour en
traiter d'autres), il lit `mapping/final_aggregation/map_agg_{base}.xlsx` et
applique ce mapping à tous les fichiers déjà produits par le programme principal.
Il traite le dossier du run (`SRDV (c,s)`, `SRDQ (c,s)`…) ou, en mode `(c,s,t)`,
le dossier de **chaque technologie** de `TECHS` :
- fichiers matrices (`rd_dir_CI`, `rd_embod_CI`, `rd_imp_CI`, `rd_dir_CFC`,
  `rd_embod_CFC`, `rd_dir_cit`, `rd_dir_fdips`) : somme les lignes et les colonnes
  portant le même secteur commun ;
- fichiers longs (`production`, `exports`, `imports_intermediate`) : somme par
  `(Region, secteur commun)` ; `imports_final_demand` est simplement recopié.

Chaque résultat est écrit à côté du fichier d'origine, même nom +
suffixe `_agg` (ex. `rd_dir_CI_EXIOBASE_2015.csv` →
`rd_dir_CI_EXIOBASE_2015_agg.csv`). Rien n'est écrasé : relancer le script sur
un fichier déjà traité ne retouche pas son `_agg` existant, et les fichiers
d'origine ne sont jamais modifiés.

### Comment le lancer

À lancer après le programme principal, une fois que le dossier du run contient
les fichiers à agréger pour la base voulue.

## 6. La chaîne complète

| Étape | Programme | Produit |
|---|---|---|
| 0 (une fois) | `code/conversion_RD.py` | fichiers `RDQ` recalés sur 2020 (les `RDV` ne changent pas), écrits avec le suffixe `_rebased` : les renommer sans suffixe pour les utiliser |
| 0 (une fois) | `code/conversion_STAN_euro.py` | fichiers STAN convertis en euros (taux 2020) et volumes recalés sur 2020, écrits avec le suffixe `_euro` ; `prépa_va_STAN` lit les fichiers `STAN_DATA_TFP_essential (euro courant).csv` et `DATA_STAN (euro courant).csv` du dossier `code/création_panel_estimation/DATA/` : y placer la version voulue |
| 0 (une fois) | `code/création_panel_estimation/prépa_va_STAN.ipynb` | `Panels_intermediaires/panel_va_STAN.csv`, `panel_cit1.csv` et `intensite_propre.csv` (intensité de R&D = RDV / production STAN, commune à toutes les bases et technologies) |
| 1 | `code/know_calc_loop.ipynb` | métriques par base, année et (le cas échéant) technologie (section 3) |
| 2 | `code/aggregate_to_common_mapping.py` | fichiers `_agg` à la nomenclature commune (section 5) |

### 6.1 Graphiques sur les matrices de sortie : `graphs_output_general.ipynb`

Ce notebook trace des diagrammes de flux (Sankey) et des décompositions d'origine à partir des matrices écrites par le programme principal. Il sait travailler sur **toutes les matrices disponibles**, c'est-à-dire sur chaque *run* du programme principal :

| Run | Contenu |
|---|---|
| `SRDV (c,s)` | valeur (RDV), sans technologie |
| `SRDQ (c,s)` | volume (RDQ), sans technologie |
| `SRDV (c,s,t)/<TECH>` | valeur, avec la technologie `<TECH>` |
| `SRDQ (c,s,t)/<TECH>` | volume, avec la technologie `<TECH>` |

- **Catalogue :** au démarrage, le notebook parcourt ces dossiers et affiche, pour chaque run et chaque base, les années disponibles. Les runs absents sont simplement ignorés.
- **Run utilisé par défaut :** celui de `project_settings.py` (`RD_UNIT`, `DIMENSION`, `TECH`). Pour en tracer un autre sans toucher à `project_settings`, modifier `DEFAULT_RUN` en tête de notebook, avec la fonction `run_id(unit, dimension, tech)` :

```python
DEFAULT_RUN = run_id("volume", "(c,s,t)", "TJ07")   # volume, technologie TJ07
```

- **Un graphique pour un run précis :** `plot_flow_sankey_full(..., run=run_id("value", "(c,s,t)", "TJ11"))`.
- **Comparer plusieurs runs sur un même graphique :** dans `plot_origin_decomposition_panels`, chaque source de la liste `sources` est un `(base, métrique, année)`, auquel on ajoute le run comme 4ᵉ élément :

```python
sources = [("EXIOBASE", "rd_dir_CI", 2010, run_id("value", "(c,s)")),
           ("EXIOBASE", "rd_dir_CI", 2010, run_id("volume", "(c,s)")),
           ("EXIOBASE", "rd_dir_CI", 2010, run_id("value", "(c,s,t)", "TJ11"))]
```

- **Nomenclature :** `USE_AGG = False` (par défaut) lit les matrices à la résolution native de chaque base ; `USE_AGG = True` lit les fichiers `_agg` (nomenclature commune).
- **Sorties :** les figures vont dans `runs/<run>/graphs_output/` pour un seul run, et dans `runs/comparison/graphs_output/` quand plusieurs runs sont comparés.
