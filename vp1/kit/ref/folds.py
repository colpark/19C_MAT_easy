"""vP.1 reference: compound folds for cross-fitted program selection (PREREG_vP1.md, VP1-1).

Each family's compounds are ranked by sha256('vp1|' + formula). The first ceil(n/2) form fold 0 and the rest fold 1, so the two folds
differ in size by at most one and the split is fixed before any score exists."""
import hashlib
import math

SALT = 'vp1'


def rank_key(formula, salt=SALT):
    return hashlib.sha256(f'{salt}|{formula}'.encode()).hexdigest()


def folds(formulas, salt=SALT):
    """formula -> 0 or 1. Duplicates collapse to one compound."""
    uniq = sorted(set(formulas), key=lambda f: rank_key(f, salt))
    cut = math.ceil(len(uniq) / 2)
    return {f: (0 if i < cut else 1) for i, f in enumerate(uniq)}
