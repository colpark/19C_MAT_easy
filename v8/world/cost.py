"""Cost model for the V8-2 instrument. Scan minutes from pixels, line rate and frames.

minutes = frames * n_lines / (line_rate_hz * 60) + overhead_min
The free m0 is one 500 nm overview at 256 px (one frame, 1 Hz). Budget 180 min.
"""
from dataclasses import dataclass, asdict

BUDGET_MIN = 180.0
OVERHEAD_MIN = 1.0       # stage move + approach + settle per scan (assumed, uncalibrated)
LINE_RATE_REF = 1.0      # Hz, reference tapping-mode line rate (uncalibrated typical value)
MAX_PX = 1024
MAX_LINE_RATE = 5.0
M0_FOV_NM, M0_NPX = 500.0, 256


@dataclass
class Plan:
    kind: str = "rods"          # "rods" or "lattice"
    fov_nm: float = 500.0
    npx: int = 256
    line_rate_hz: float = 1.0
    frames: int = 1
    cx_nm: float = 0.0          # window centre in the scan frame
    cy_nm: float = 0.0
    nlines: int = 0             # 0 -> square (nlines = npx); lattice scans may use fewer lines

    def validate(self):
        assert self.kind in ("rods", "lattice")
        assert 4 <= self.npx <= MAX_PX and 4 <= self.ny <= MAX_PX, "npx out of range"
        assert 0.05 <= self.line_rate_hz <= MAX_LINE_RATE, "line rate out of range"
        assert 1 <= int(self.frames) <= 64
        assert 2.0 <= self.fov_nm <= 1000.0
        return self

    @property
    def ny(self):
        return int(self.nlines) if self.nlines else int(self.npx)

    def frame_minutes(self):
        """Duration of one frame: sets the drift distortion inside an image (frames are registered)."""
        return self.ny / (self.line_rate_hz * 60.0)

    def minutes(self, free=False):
        return 0.0 if free else scan_minutes(self.ny, self.line_rate_hz, self.frames)

    def asdict(self):
        return asdict(self)


def scan_minutes(npx, line_rate_hz=1.0, frames=1, overhead_min=OVERHEAD_MIN):
    return frames * npx / (line_rate_hz * 60.0) + overhead_min


def m0_plan():
    return Plan("rods", M0_FOV_NM, M0_NPX, 1.0, 1)


def noise_scale(plan):
    """White-noise multiplier: faster lines are noisier, frames average down (documented model)."""
    return (plan.line_rate_hz / LINE_RATE_REF) ** 0.5 / plan.frames ** 0.5


class Ledger:
    def __init__(self, budget=BUDGET_MIN):
        self.budget, self.spent, self.log = budget, 0.0, []

    def charge(self, plan, free=False):
        c = plan.minutes(free)
        if self.spent + c > self.budget + 1e-9:
            raise RuntimeError("budget exceeded: need %.1f, left %.1f" % (c, self.budget - self.spent))
        self.spent += c
        self.log.append((plan.asdict(), c))
        return c

    @property
    def left(self):
        return self.budget - self.spent


if __name__ == "__main__":
    print("m0 free scan would cost %.2f min; budget %.0f" % (m0_plan().minutes(), BUDGET_MIN))
    for n in (64, 128, 256, 512):
        print(n, "px, 1 Hz, 1 frame: %.2f min" % scan_minutes(n))
