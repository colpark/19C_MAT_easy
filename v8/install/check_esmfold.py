"""V8-0 install check: ESMFold (facebook/esmfold_v1) through transformers on GPU, one 100-residue sequence."""
import time, torch, transformers
from transformers import AutoTokenizer, EsmForProteinFolding
# first 100 residues of T4 lysozyme (public; the literal is its first 99, padded by repetition), used only as an install probe
seq = ("MNIFEMLRIDEGLRLKIYKDTEGYYTIGIGHLLTKSPSLNAAKSELDKAIGRNTNGVITKDEAEKLFNQDVDAAVRGILRNAKLKPVYDSLDAVRRAAL" * 2)[:100]
assert len(seq) == 100
tok = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
m = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1").cuda().eval()
m.esm = m.esm.half()
t = time.time()
with torch.no_grad():
    out = m(**tok([seq], return_tensors="pt", add_special_tokens=False).to("cuda"))
plddt = out["plddt"][0, :, 1].mean().item()
pdb = m.output_to_pdb(out)[0]
open("esmfold_check.pdb", "w").write(pdb)
print("transformers", transformers.__version__, f"fold {time.time()-t:.1f} s, mean pLDDT {plddt:.3f}, CA atoms {pdb.count(' CA ')}")
print("ESMFOLD OK")
