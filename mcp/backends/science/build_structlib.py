"""Build ~/mcp/science/structlib from COD CIFs. Candidate COD IDs chosen from Dara's cod_filtered_info_2024 index
(formula + space group, lowest e_above_hull), downloaded from crystallography.net, verified with pymatgen."""
import gzip, json, time, urllib.request, os, sys
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import warnings; warnings.filterwarnings("ignore")
HOME = os.path.expanduser("~/mcp/science")
idx = json.load(gzip.open(f"{HOME}/repos/dara/src/dara/data/cod_filtered_info_2024.json.gz"))
PH = [  # name, formula, spacegroup number(s)
 ("Si","Si",[227]),("Al","Al",[225]),("Cu","Cu",[225]),("Fe_bcc","Fe",[229]),("Fe_fcc","Fe",[225]),("Ni","Ni",[225]),
 ("Ti_hcp","Ti",[194]),("Mg","Mg",[194]),("Zn","Zn",[194]),("Au","Au",[225]),("Ag","Ag",[225]),
 ("Al2O3_corundum","Al2O3",[167]),("TiO2_anatase","TiO2",[141]),("TiO2_rutile","TiO2",[136]),("ZnO_wurtzite","ZnO",[186]),
 ("SiO2_quartz","SiO2",[154,152]),("Fe2O3_hematite","Fe2O3",[167]),("Fe3O4_magnetite","Fe3O4",[227]),("CeO2","CeO2",[225]),
 ("ZrO2_monoclinic","ZrO2",[14]),("ZrO2_tetragonal","ZrO2",[137]),("BaTiO3_tetragonal","BaTiO3",[99]),("BaTiO3_cubic","BaTiO3",[221]),
 ("SrTiO3","SrTiO3",[221]),("NaCl","NaCl",[225]),("CaCO3_calcite","CaCO3",[167]),("hydroxyapatite","Ca5(PO4)3(OH)",[176,173]),
 ("MgO","MgO",[225]),("NiO","NiO",[225,166]),("CuO_tenorite","CuO",[15]),("Cu2O_cuprite","Cu2O",[224]),("Co3O4","Co3O4",[227]),
 ("MnO2_pyrolusite","MnO2",[136]),("graphite","C",[194]),("SiC_3C","SiC",[216]),("SiC_6H","SiC",[186]),("Si3N4_beta","Si3N4",[176,173]),
 ("WC","WC",[187]),("TiN","TiN",[225]),("AlN","AlN",[186]),("LiFePO4","LiFePO4",[62]),("LiCoO2","LiCoO2",[166]),("MoS2_2H","MoS2",[194]),
]
out = {}
for name, f, sgs in PH:
    comp = Composition(f); rf = comp.reduced_formula
    chemsys = "-".join(sorted(e.symbol for e in comp.elements))
    cands = [c for c in idx.get(chemsys, []) if c[2] in sgs]
    def match(c):
        try: return Composition(c[0]).reduced_formula == rf
        except Exception: return False
    exact = [c for c in cands if match(c)]
    if not exact and name == "hydroxyapatite":  # H often missing in CIF; accept Ca5P3O13-ish
        exact = [c for c in idx.get("Ca-O-P", []) + idx.get("Ca-H-O-P", []) if c[2] in sgs and "Ca5" in c[0] or c[0].startswith("Ca10")]
    exact.sort(key=lambda c: (c[3] is None, c[3] if c[3] is not None else 9, sgs.index(c[2]) if c[2] in sgs else 9))
    ok = False
    for c in exact[:6]:
        cid = c[1]
        try:
            txt = urllib.request.urlopen(f"https://www.crystallography.net/cod/{cid}.cif", timeout=60).read().decode("utf-8", "replace")
            s = Structure.from_str(txt, fmt="cif")
            sg = SpacegroupAnalyzer(s, symprec=0.1).get_space_group_number()
            if s.composition.reduced_formula != rf and name != "hydroxyapatite":
                print("  formula mismatch", name, cid, s.composition.reduced_formula); continue
            path = f"{HOME}/structlib/{name}.cif"
            open(path, "w").write(txt)
            out[name] = dict(file=f"{name}.cif", formula=rf, cod_id=cid, url=f"https://www.crystallography.net/cod/{cid}.cif",
                             sg_number=sg, sg_index=c[2], e_above_hull=c[3], lattice_abc=[round(x,4) for x in s.lattice.abc],
                             natoms=len(s), license="COD: public domain / CC0 (crystallography.net/cod/ terms)")
            print(name, cid, rf, s.composition.reduced_formula, sg, c[3]); ok = True; break
        except Exception as e:
            print("  fail", name, cid, repr(e)[:120])
        time.sleep(0.5)
    if not ok: print("MISSING", name, len(cands), [c[:3] for c in cands[:5]])
json.dump(out, open(f"{HOME}/structlib/index.json", "w"), indent=1)
print(len(out), "phases")
