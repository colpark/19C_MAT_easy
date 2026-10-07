#!/usr/bin/env python3
"""inventory_s.py: Track S desk checks on downloaded deposits (requirements R2 readers and R4 calibration, SEM block).

Commands (each takes --dataset ID ...; default: every dataset folder under <root>)
  extract   unpack .zip and .7z archives from files/ into extracted/<archive path>/ (path traversal guarded, marker per archive)
  scan      walk files/ and extracted/, write inventory.jsonl and inventory_summary.json with native SEM metadata per image
  readers   open a sample of every file type with its open reader, write readers.json with the R2 verdict

Native pixel size sources, most trusted first: FEI or Thermo tags 34680/34682 ([Scan] PixelWidth), Zeiss tag 34118
(ap_image_pixel_size), TESCAN tag 50431 (PixelSizeX), OME-XML PhysicalSizeX, ImageJ resolution, Hitachi or JEOL sidecar text,
a pixel size printed in ImageDescription, and last the TIFF resolution tags (only with cm or inch units and a plausible value).
The scan never guesses a scale from a scale bar. Images without native metadata are listed so that a validated scale-bar
reader (or exclusion) can follow.

Data files are untrusted: this script only reads them and never executes anything from a deposit.
Environment: HARBOR (default /home/aid1/Documents/harbor). Needs numpy and tifffile; uses Pillow, h5py, orix, kikuchipy,
hyperspy (RosettaSciIO), mrcfile, openpyxl and py7zr when installed.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HARBOR = os.environ.get('HARBOR', '/home/aid1/Documents/harbor')
ROOT_DEFAULT = os.path.join(HARBOR, 'v4_host/trackS')
IMG = {'.tif', '.tiff'}
RASTER = {'.png', '.bmp', '.gif', '.jpg', '.jpeg'}
ARCH = {'.zip', '.7z'}


def now():
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')


def ext_of(p):
    e = os.path.splitext(p)[1].lower()
    return e if e else '(none)'


# ---------------------------------------------------------------- extract
def _safe_target(base, member):
    target = os.path.realpath(os.path.join(base, member))
    if not target.startswith(os.path.realpath(base) + os.sep) and target != os.path.realpath(base):
        raise ValueError(f'unsafe member path {member!r}')
    return target


def extract_archive(arc, out):
    marker = os.path.join(out, '.extracted.json')
    if os.path.exists(marker):
        return json.load(open(marker))
    os.makedirs(out, exist_ok=True)
    members = []
    if arc.lower().endswith('.zip'):
        with zipfile.ZipFile(arc) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                target = _safe_target(out, info.filename)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(info) as src, open(target, 'wb') as dst:
                    shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
                members.append({'name': info.filename, 'bytes': info.file_size})
        tool = 'zipfile'
    else:
        try:
            import py7zr  # noqa: PLC0415
            with py7zr.SevenZipFile(arc, 'r') as z:
                names = z.getnames()
                for n in names:
                    _safe_target(out, n)
                z.extractall(path=out)
            members = [{'name': n} for n in names]
            tool = 'py7zr'
        except ImportError:
            exe = shutil.which('7z') or shutil.which('7za') or shutil.which('7zz')
            if not exe:
                raise RuntimeError('no 7z support: uv pip install py7zr, or install p7zip')
            listing = subprocess.run([exe, 'l', '-slt', arc], capture_output=True, text=True, check=True).stdout
            names = re.findall(r'^Path = (.+)$', listing, flags=re.M)[1:]
            for n in names:
                _safe_target(out, n)
            subprocess.run([exe, 'x', '-y', f'-o{out}', arc], capture_output=True, check=True)
            members = [{'name': n} for n in names]
            tool = os.path.basename(exe)
    rec = {'archive': arc, 'tool': tool, 'members': len(members), 'extracted': now(), 'list': members[:20000]}
    json.dump(rec, open(marker, 'w'), indent=1)
    return rec


def cmd_extract(root, ids):
    for ds in ids:
        fdir = os.path.join(root, ds, 'files')
        for base, _, names in os.walk(fdir):
            for n in names:
                if ext_of(n) in ARCH:
                    arc = os.path.join(base, n)
                    rel = os.path.relpath(arc, fdir)
                    out = os.path.join(root, ds, 'extracted', os.path.splitext(rel)[0])
                    try:
                        r = extract_archive(arc, out)
                        print(f'{ds}: {rel} -> {r["members"]} members ({r["tool"]})', flush=True)
                    except Exception as e:  # noqa: BLE001
                        print(f'{ds}: {rel} FAILED: {e}', flush=True)


# ---------------------------------------------------------------- native SEM metadata
def _num(x):
    try:
        return float(str(x).strip().split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _to_nm(value, unit):
    if value is None:
        return None
    u = (unit or '').strip().lower().replace('µ', 'u').replace('μ', 'u')
    f = {'m': 1e9, 'mm': 1e6, 'um': 1e3, 'micron': 1e3, 'microns': 1e3, 'micrometer': 1e3, 'nm': 1.0, 'pm': 1e-3, 'a': 0.1}.get(u)
    return value * f if f else None


def _ini(text):
    out, sec = {}, ''
    for line in str(text).splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            sec = line[1:-1]
            out.setdefault(sec, {})
        elif '=' in line:
            k, v = line.split('=', 1)
            out.setdefault(sec, {})[k.strip()] = v.strip()
    return out


def _sidecar(path):
    stem = os.path.splitext(path)[0]
    for ext in ('.txt', '.TXT', '.hdr', '.HDR'):
        p = stem + ext
        if os.path.exists(p) and os.path.getsize(p) < 200000:
            return p, open(p, 'r', errors='replace').read()
    return None, None


def tiff_meta(path):
    import tifffile  # noqa: PLC0415
    m = {'kind': 'tiff'}
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        m.update({'width': int(page.imagewidth), 'height': int(page.imagelength), 'dtype': str(page.dtype),
                  'bits': int(page.bitspersample) if page.bitspersample else None, 'pages': len(tf.pages),
                  'samples': int(page.samplesperpixel)})
        tags = page.tags
        src = None
        # FEI / Thermo Fisher
        fei = None
        for code in (34682, 34680):
            if code in tags:
                v = tags[code].value
                fei = v if isinstance(v, dict) else _ini(v)
                break
        if fei:
            scan = fei.get('Scan') or {}
            beam = fei.get('Beam') or fei.get('EBeam') or {}
            det = fei.get('Detectors') or {}
            ps = _num(scan.get('PixelWidth'))
            m.update({'pixel_size_nm': ps * 1e9 if ps else None, 'hfw_um': (_num(scan.get('HorFieldsize')) or 0) * 1e6 or None,
                      'kv': (_num(beam.get('HV')) or 0) / 1000 or None, 'detector': det.get('Name'), 'detector_mode': det.get('Mode'),
                      'dwell_s': _num(scan.get('Dwelltime')), 'wd_mm': (_num((fei.get('Stage') or {}).get('WorkingDistance')) or 0) * 1e3 or None,
                      'date': (fei.get('User') or {}).get('Date'), 'instrument': (fei.get('System') or {}).get('SystemType')})
            src = 'fei' if m.get('pixel_size_nm') else None
        # Zeiss SmartSEM
        if not src and 34118 in tags:
            z = tags[34118].value
            if isinstance(z, dict):
                def zget(key):
                    """tifffile stores (name, value) or (name, value, unit)."""
                    v = z.get(key)
                    if isinstance(v, tuple):
                        return (v[1] if len(v) > 1 else None), (v[2] if len(v) > 2 else '')
                    return v, ''
                val, unit = zget('ap_image_pixel_size')
                ps = _to_nm(_num(val), unit or 'nm')
                mag, mag_unit = zget('ap_mag')
                mag_num = _num(mag)
                if mag_num is not None and ((isinstance(mag, str) and re.search(r'\d\s*K', mag)) or 'K' in str(mag_unit).upper()):
                    mag_num *= 1000  # '10.00 K X' stays a string, '50.00 KX' parses to (50.0, 'KX')
                kv, kvu = zget('ap_actualkv')
                det, _ = zget('dp_detector_channel')
                m.update({'pixel_size_nm': ps, 'magnification': mag_num, 'kv': _num(kv), 'detector': det})
                src = 'zeiss' if ps else None
        # TESCAN
        if not src and 50431 in tags:
            t = _ini(tags[50431].value if not isinstance(tags[50431].value, bytes) else tags[50431].value.decode('utf-8', 'replace'))
            main = t.get('MAIN') or {}
            ps = _num(main.get('PixelSizeX'))
            m.update({'pixel_size_nm': ps * 1e9 if ps else None, 'kv': (_num(main.get('HV')) or 0) / 1000 or None,
                      'detector': main.get('Detector'), 'magnification': _num(main.get('Magnification'))})
            src = 'tescan' if ps else None
        # OME
        if not src and tf.ome_metadata:
            mm = re.search(r'PhysicalSizeX="([\d.eE+-]+)"(?:\s+PhysicalSizeXUnit="([^"]+)")?', tf.ome_metadata)
            if mm:
                m['pixel_size_nm'] = _to_nm(float(mm.group(1)), mm.group(2) or 'um')
                src = 'ome' if m['pixel_size_nm'] else None
        # ImageJ
        if not src and tf.imagej_metadata and 282 in tags:
            unit = tf.imagej_metadata.get('unit')
            xr = tags[282].value
            px_per_unit = xr[0] / xr[1] if isinstance(xr, tuple) and xr[1] else _num(xr)
            if unit and px_per_unit:
                m['pixel_size_nm'] = _to_nm(1.0 / px_per_unit, unit)
                src = 'imagej' if m['pixel_size_nm'] else None
        # sidecar (Hitachi PixelSize in nm, JEOL micron bar)
        if not src:
            sp, text = _sidecar(path)
            if text:
                mm = re.search(r'^\s*PixelSize\s*=\s*([\d.eE+-]+)', text, re.M)
                if mm:
                    m['pixel_size_nm'] = float(mm.group(1))
                    mg = re.search(r'^\s*Magnification\s*=\s*([\d.]+)', text, re.M)
                    m['magnification'] = float(mg.group(1)) if mg else None
                    src = 'hitachi_sidecar'
                else:
                    bar = re.search(r'\$\$SM_MICRON_BAR\s+(\d+)', text)
                    mark = re.search(r'\$\$SM_MICRON_MARKER\s+([\d.]+)\s*(\w+)', text)
                    if bar and mark:
                        m['pixel_size_nm'] = _to_nm(float(mark.group(1)) / int(bar.group(1)), mark.group(2))
                        mg = re.search(r'\$CM_MAG\s+(\d+)', text)
                        m['magnification'] = float(mg.group(1)) if mg else None
                        src = 'jeol_sidecar' if m['pixel_size_nm'] else None
                m['sidecar'] = os.path.basename(sp)
        # pixel size printed in ImageDescription (AZtec and others)
        if not src and 270 in tags:
            desc = str(tags[270].value)
            mm = re.search(r'pixel[ _]?size[^0-9]{0,20}([\d.eE+-]+)\s*(nm|um|µm|μm|micron|mm|m)\b', desc, re.I)
            if mm:
                m['pixel_size_nm'] = _to_nm(float(mm.group(1)), mm.group(2))
                src = 'description' if m['pixel_size_nm'] else None
        # resolution tags (low trust)
        if not src and 282 in tags and 296 in tags:
            unit = tags[296].value
            xr = tags[282].value
            ppu = xr[0] / xr[1] if isinstance(xr, tuple) and xr[1] else _num(xr)
            length_nm = {2: 2.54e7, 3: 1e7}.get(int(unit)) if unit else None
            if ppu and length_nm:
                ps = length_nm / ppu
                if 0.05 <= ps <= 1e5:
                    m['pixel_size_nm'] = ps
                    src = 'resolution_tag'
        m['pixel_size_source'] = src or 'none'
    return m


def text_header(path, limit=400):
    out = {}
    with open(path, 'r', errors='replace') as fh:
        lines = [next(fh, '') for _ in range(limit)]
    e = ext_of(path)
    if e == '.ang':
        for line in lines:
            mm = re.match(r'#\s*(XSTEP|YSTEP|NCOLS_ODD|NCOLS_EVEN|NROWS|GRID|MaterialName)\s*:?\s*(.*)', line.strip())
            if mm:
                out.setdefault(mm.group(1), mm.group(2).strip())
    elif e == '.ctf':
        for line in lines:
            parts = line.strip().split('\t')
            if parts and parts[0] in ('XCells', 'YCells', 'XStep', 'YStep', 'AcqE1', 'Euler angles refer to Sample Coordinate system (CS0)!'):
                out[parts[0]] = parts[1] if len(parts) > 1 else True
    elif e in ('.csv', '.tsv', '.txt'):
        out['first_line'] = lines[0].strip()[:300] if lines else ''
    return out


def h5_meta(path):
    try:
        import h5py  # noqa: PLC0415
    except ImportError:
        return {'h5': 'h5py not installed'}
    with h5py.File(path, 'r') as f:
        keys = list(f.keys())[:20]
        out = {'h5_keys': keys}
        for cand in ('1/EBSD/Header/X Step', 'Scan 1/EBSD/Header/Step X'):
            if cand in f:
                out['ebsd_step'] = float(f[cand][()].ravel()[0])
        return out


def scan_dataset(root, ds):
    out_rows = []
    for sub in ('files', 'extracted'):
        top = os.path.join(root, ds, sub)
        for base, _, names in os.walk(top):
            for n in names:
                if n == '.extracted.json' or n.endswith(('.part', '.bad')):
                    continue
                p = os.path.join(base, n)
                rel = os.path.relpath(p, os.path.join(root, ds))
                e = ext_of(n)
                row = {'path': rel, 'ext': e, 'bytes': os.path.getsize(p), 'in_archive': sub == 'extracted'}
                try:
                    if e in IMG:
                        row.update(tiff_meta(p))
                    elif e in RASTER:
                        from PIL import Image  # noqa: PLC0415
                        with Image.open(p) as im:
                            row.update({'kind': 'raster', 'width': im.width, 'height': im.height, 'mode': im.mode,
                                        'lossy': e in ('.jpg', '.jpeg'), 'pixel_size_source': 'none'})
                    elif e in ('.ang', '.ctf', '.csv', '.tsv', '.txt'):
                        row.update(text_header(p))
                    elif e in ('.h5', '.h5oina', '.hdf5', '.h5ebsd'):
                        row.update(h5_meta(p))
                except Exception as ex:  # noqa: BLE001
                    row['error'] = f'{type(ex).__name__}: {ex}'[:300]
                out_rows.append(row)
    return out_rows


def summarize(rows):
    by_ext = collections.Counter(r['ext'] for r in rows)
    imgs = [r for r in rows if r.get('kind') in ('tiff', 'raster')]
    src = collections.Counter(r.get('pixel_size_source', 'none') for r in imgs)
    ps = sorted({round(r['pixel_size_nm'], 4) for r in imgs if r.get('pixel_size_nm')})
    return {'files': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'by_ext': dict(by_ext.most_common()),
            'images': len(imgs), 'images_native_pixel_size': sum(1 for r in imgs if r.get('pixel_size_source') not in (None, 'none', 'resolution_tag')),
            'pixel_size_sources': dict(src), 'distinct_pixel_sizes_nm': ps[:200], 'n_distinct_pixel_sizes': len(ps),
            'detectors': dict(collections.Counter(str(r.get('detector')) for r in imgs if r.get('detector'))),
            'kv': sorted({r['kv'] for r in imgs if r.get('kv')}), 'magnifications': sorted({r['magnification'] for r in imgs if r.get('magnification')})[:100],
            'lossy_images': sum(1 for r in imgs if r.get('lossy')), 'errors': [r['path'] for r in rows if r.get('error')][:50],
            'tile_layouts': [r['path'] for r in rows if re.search(r'TileConfiguration|\.maps$|LayersData|montage|mosaic', r['path'], re.I)][:50],
            'slide_or_document_exports': [r['path'] for r in rows if r['ext'] in ('.pptx', '.ppt', '.docx', '.doc')]}


def cmd_scan(root, ids):
    for ds in ids:
        rows = scan_dataset(root, ds)
        with open(os.path.join(root, ds, 'inventory.jsonl'), 'w') as fh:
            for r in rows:
                fh.write(json.dumps(r, default=str) + '\n')
        s = summarize(rows)
        s.update({'dataset': ds, 'scanned': now()})
        json.dump(s, open(os.path.join(root, ds, 'inventory_summary.json'), 'w'), indent=1, default=str)
        print(f"{ds}: {s['files']} files, {s['images']} images, native pixel size on {s['images_native_pixel_size']}, "
              f"{s['n_distinct_pixel_sizes']} distinct pixel sizes, sources {s['pixel_size_sources']}", flush=True)


# ---------------------------------------------------------------- R2 reader checks
TWINS = {'.osc': ['.ang'], '.cpr': ['.ctf'], '.crc': ['.ctf']}   # K2: proprietary file -> open twins with the same stem
NO_OPEN_READER = {'.osc': 'EDAX OIM binary: export .ang', '.opju': 'Origin project', '.opj': 'Origin project', '.crp': 'proprietary creep file',
                  '.rtx': 'Bruker Esprit project', '.cpr': 'Oxford Channel 5 binary (try DefDAP)', '.crc': 'Oxford Channel 5 binary (try DefDAP)'}
KEYED = IMG | RASTER | {'.ang', '.ctf', '.h5', '.h5oina', '.hdf5', '.h5ebsd', '.up1', '.up2', '.bcf', '.spx', '.emd', '.dm3', '.dm4', '.msa',
                        '.emsa', '.rpl', '.spd', '.pts', '.csv', '.tsv', '.xlsx', '.xls', '.mrc', '.osc', '.cpr', '.crc', '.opju', '.rtx', '.vtk'}


def try_read(path):
    e = ext_of(path)
    if e in NO_OPEN_READER:
        return 'none', False, NO_OPEN_READER[e]
    if e in IMG:
        import tifffile  # noqa: PLC0415
        a = tifffile.imread(path, key=0)
        return 'tifffile', True, f'{a.shape} {a.dtype}'
    if e in RASTER:
        from PIL import Image  # noqa: PLC0415
        with Image.open(path) as im:
            im.load()
            return 'Pillow', True, f'{im.size} {im.mode}' + (' lossy' if e in ('.jpg', '.jpeg') else '')
    if e in ('.csv', '.tsv', '.txt', '.md', '.svg'):
        with open(path, 'r', errors='replace') as fh:
            rows = list(csv.reader(fh.readlines()[:2000], delimiter='\t' if e == '.tsv' else ','))
        return 'csv', len(rows) > 0, f'{len(rows)} rows read'
    if e == '.xlsx':
        import openpyxl  # noqa: PLC0415
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        return 'openpyxl', True, f'{len(wb.worksheets)} sheets'
    if e in ('.ang', '.ctf'):
        orix_note = 'orix not installed'
        try:
            from orix import io as oio  # noqa: PLC0415
            xm = oio.load(path)
            return 'orix', True, f'{xm.shape}'
        except ImportError:
            pass
        except Exception as ex:   # V4-E20: orix rejects files without a vendor header; fall back to the plain-text parse and say why
            orix_note = f'orix failed: {type(ex).__name__}: {str(ex)[:80]}'
        if True:
            import numpy as np  # noqa: PLC0415
            with open(path, 'r', errors='replace') as fh:
                data = [line for line in fh.readlines()[:5000] if line.strip() and not line.startswith('#')]
            if e == '.ctf':
                data = [line for line in data if re.match(r'^\s*\d', line)]
            arr = np.loadtxt(data[:2000])
            return f'numpy ({orix_note})', arr.ndim == 2 and arr.shape[0] > 0, f'{arr.shape}'
    if e in ('.h5', '.h5oina', '.hdf5', '.h5ebsd'):
        import h5py  # noqa: PLC0415
        with h5py.File(path, 'r') as f:
            return 'h5py', True, f'{list(f.keys())[:5]}'
    if e in ('.up1', '.up2'):
        import kikuchipy as kp  # noqa: PLC0415
        s = kp.load(path, lazy=True)
        return 'kikuchipy', True, f'{s.data.shape}'
    if e in ('.bcf', '.spx', '.emd', '.dm3', '.dm4', '.msa', '.emsa', '.rpl', '.spd', '.pts'):
        import hyperspy.api as hs  # noqa: PLC0415
        s = hs.load(path, lazy=True)
        s = s if isinstance(s, list) else [s]
        return 'hyperspy/rsciio', True, ' | '.join(f'{type(x).__name__} {x.data.shape}' for x in s[:3])
    if e == '.mrc':
        import mrcfile  # noqa: PLC0415
        with mrcfile.open(path, permissive=True, header_only=True) as mf:
            return 'mrcfile', True, f'{mf.header.nx} {mf.header.ny} {mf.header.nz}'
    if e == '.zip':
        with zipfile.ZipFile(path) as z:
            return 'zipfile', z.testzip() is None, f'{len(z.namelist())} members'
    if e in ('.pptx', '.ppt', '.docx', '.doc'):
        return 'n/a', True, 'slide or document export: not raw data (inclusion rule)'
    if e in ('.pdf',):
        with open(path, 'rb') as fh:
            return 'pdf header', fh.read(5) == b'%PDF-', ''
    return 'untested', None, 'no reader rule for this extension'


def cmd_readers(root, ids, per_ext=3):
    for ds in ids:
        inv = os.path.join(root, ds, 'inventory.jsonl')
        if not os.path.exists(inv):
            print(f'{ds}: run scan first')
            continue
        rows = [json.loads(line) for line in open(inv)]
        by = collections.defaultdict(list)
        for r in rows:
            by[r['ext']].append(r['path'])
        res = {}
        for e, paths in sorted(by.items()):
            step = max(1, len(paths) // per_ext)
            sample = paths[::step][:per_ext]
            out = {'files': len(paths), 'tested': 0, 'ok': 0, 'fail': 0, 'reader': None, 'notes': [], 'keyed': e in KEYED}
            for rel in sample:
                try:
                    reader, ok, note = try_read(os.path.join(root, ds, rel))
                except ImportError as ex:
                    reader, ok, note = 'missing package', None, str(ex)
                except Exception as ex:  # noqa: BLE001
                    if 'imagecodecs' in str(ex).lower():  # compressed TIFF (LZW, JPEG, ZSTD) without the codec package
                        reader, ok, note = 'missing package', None, 'install imagecodecs: ' + str(ex)[:150]
                        out['reader'] = reader
                        out['tested'] += 1
                        out['notes'].append(f'{os.path.basename(rel)}: {note}')
                        continue
                    reader, ok, note = out['reader'] or 'error', False, f'{type(ex).__name__}: {ex}'[:200]
                out['reader'] = reader
                out['tested'] += 1
                out['ok'] += ok is True
                out['fail'] += ok is False
                out['notes'].append(f'{os.path.basename(rel)}: {note}')
            out['status'] = 'pass' if out['ok'] == out['tested'] else ('fail' if out['reader'] == 'none' or out['fail'] else 'check')
            res[e] = out
        # K2: a proprietary file is redundant (never keyed, ignored by R2) when every copy has an open twin with the same stem
        stems = collections.defaultdict(set)
        for r in rows:
            stems[os.path.splitext(r['path'])[0]].add(r['ext'])
        for e, twins in TWINS.items():
            if e in res and res[e]['status'] == 'fail':
                ok_twins = [t for t in twins if t in res and res[t]['status'] == 'pass']
                if ok_twins and all(stems[os.path.splitext(pth)[0]] & set(ok_twins) for pth in by[e]):
                    res[e].update({'status': 'redundant', 'keyed': False, 'redundant_with': ok_twins})
                    res[e]['notes'].append(f'redundant: open twin {ok_twins} with the same stem for every file (K2)')
        keyed = {e: v for e, v in res.items() if v['keyed']}
        verdict = 'fail' if any(v['status'] == 'fail' for v in keyed.values()) else (
            'pass' if keyed and all(v['status'] == 'pass' for v in keyed.values()) else 'check')
        doc = {'dataset': ds, 'checked': now(), 'R2': verdict, 'by_ext': res}
        json.dump(doc, open(os.path.join(root, ds, 'readers.json'), 'w'), indent=1)
        print(f'{ds}: R2 {verdict} ' + ', '.join(f'{e} {v["status"]}' for e, v in keyed.items()), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['extract', 'scan', 'readers'])
    ap.add_argument('--dataset', nargs='*')
    ap.add_argument('--root', default=ROOT_DEFAULT)
    ap.add_argument('--per-ext', type=int, default=3)
    a = ap.parse_args(argv)
    ids = a.dataset or sorted(d for d in os.listdir(a.root) if os.path.isdir(os.path.join(a.root, d)) and not d.startswith('_'))
    if a.cmd == 'extract':
        cmd_extract(a.root, ids)
    elif a.cmd == 'scan':
        cmd_scan(a.root, ids)
    else:
        cmd_readers(a.root, ids, a.per_ext)


if __name__ == '__main__':
    main()
