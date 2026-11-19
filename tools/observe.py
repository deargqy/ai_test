"""Pack visible screenshot artifacts for one visual reading; never controls the game.

pack --input manifest.json --output new-directory
annotate --bundle new-directory/bundle.json --input readings.json
Sources are relative to the manifest. Crop boxes use Pillow's x0,y0,x1,y1.
Recognition is performed separately by the assistant, not by this program.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from PIL import Image, ImageDraw


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pack(manifest_path, output):
    started = time.perf_counter()
    manifest_path, output = Path(manifest_path).resolve(), Path(output).resolve()
    m = read(manifest_path)
    require(bool(m.get('batchId')), 'batchId is required')
    require(not (output/'bundle.json').exists(), 'use a new output directory to preserve existing readings')
    expected = tuple(m['expectedSize'])
    require(len(expected) == 2 and all(type(n) is int and n > 0 for n in expected), 'invalid expectedSize')
    require(bool(m.get('entries')), 'entries must not be empty')
    entries, unique, ids = [], {}, set()
    # Validate and load everything before writing a partial batch.
    for e in m['entries']:
        identifier = e['id']
        require(isinstance(identifier, str) and identifier and identifier not in ids, 'duplicate or invalid entry id')
        ids.add(identifier)
        source = (manifest_path.parent/e['source']).resolve()
        require(source.is_file(), f'missing source: {source}')
        with Image.open(source) as image:
            require(image.size == expected, f'resolution mismatch: {source.name}: {image.size} != {expected}')
            box = e.get('box', [0, 0, *expected])
            require(len(box) == 4 and all(type(n) is int for n in box), 'box must have four integers')
            x0, y0, x1, y1 = box
            require(0 <= x0 < x1 <= expected[0] and 0 <= y0 < y1 <= expected[1], f'invalid crop: {identifier}')
            crop = image.convert('RGB').crop(box)
        digest = hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest()
        if digest not in unique:
            unique[digest] = {'image': crop, 'file': f'crop-{len(unique)+1:02d}.png', 'ids': []}
        unique[digest]['ids'].append(identifier)
        entries.append({'id': identifier, 'label': e.get('label', identifier), 'source': str(source),
                        'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'box': box,
                        'crop': unique[digest]['file'], 'cropSha256': digest, 'reading': None})
    context = m.get('context', {})
    if m.get('contextFile'):
        require(not context, 'choose context or contextFile, not both')
        context = read(manifest_path.parent/m['contextFile'])
    output.mkdir(parents=True, exist_ok=True)
    crops = list(unique.values())
    for u in crops:
        u['image'].save(output/u['file'])
    sheets = []
    # No text downsampling: native-pixel crops, up to four per sheet.
    for offset in range(0, len(crops), 4):
        group = crops[offset:offset+4]
        columns = 1 if max(u['image'].width for u in group) > 1100 else min(2, len(group))
        width = max(u['image'].width for u in group)+20
        height = max(u['image'].height for u in group)+44
        sheet = Image.new('RGB', (width*columns, height*((len(group)+columns-1)//columns)), '#e8eedf')
        draw = ImageDraw.Draw(sheet)
        for index, u in enumerate(group):
            x, y = index % columns*width, index//columns*height
            draw.text((x+10, y+8), f'{offset+index+1:02d} | '+', '.join(u['ids']), fill='#193b30')
            sheet.paste(u['image'], (x+10, y+32))
        name = f'contact-{len(sheets)+1:02d}.jpg'
        sheet.save(output/name, quality=95, subsampling=0)
        sheets.append(name)
    bundle = {'schemaVersion': 1, 'batchId': m['batchId'], 'createdAt': datetime.now(timezone.utc).isoformat(),
              'recognition': 'pending-assistant-visual', 'context': context, 'entries': entries,
              'sheets': sheets, 'metrics': {'inputImages': len(entries), 'uniqueCrops': len(unique),
              'packSeconds': round(time.perf_counter()-started, 3)},
              'notes': ['Exact pixel deduplication only; no semantic matching.',
                        'Context is a supplied snapshot, not a fresh observation.',
                        'Use original screenshots for coordinates and uncertain text.']}
    save(output/'bundle.json', bundle)
    save(output/'readings-template.json', {'entries': [{'id': e['id'], 'name': None, 'grade': None,
         'price': None, 'stats': {}, 'passive': None, 'slots': None, 'uncertain': ['not read']} for e in entries]})
    return bundle


def annotate(bundle_path, readings_path, *, save_bundle=save):
    bundle_path = Path(bundle_path)
    bundle, readings = read(bundle_path), read(readings_path)
    by_id = {e['id']: e for e in bundle['entries']}
    seen = set()
    for r in readings['entries']:
        require(r.get('id') in by_id and r['id'] not in seen, 'unknown or duplicate reading id')
        require(isinstance(r.get('uncertain'), list), 'uncertain must be an explicit list')
        seen.add(r['id'])
        e = by_id[r['id']]
        require(e['reading'] is None, 'reading already exists; preserve it and create a new batch for corrections')
        e['reading'] = {**r, 'method': 'assistant-visual', 'evidenceSha256': e['sourceSha256'],
                        'readAt': datetime.now(timezone.utc).isoformat()}
    bundle['recognition'] = 'assistant-visual-complete' if all(e['reading'] for e in by_id.values()) else 'assistant-visual-partial'
    save_bundle(bundle_path, bundle)
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pack'); p.add_argument('--input', required=True); p.add_argument('--output', required=True)
    p = sub.add_parser('annotate'); p.add_argument('--input', required=True); p.add_argument('--bundle', required=True)
    a = parser.parse_args()
    try:
        result = pack(a.input, a.output) if a.command == 'pack' else annotate(a.bundle, a.input)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps({'batchId': result['batchId'], 'recognition': result['recognition'],
                      'metrics': result['metrics'], 'sheets': result['sheets']}, ensure_ascii=False))


if __name__ == '__main__': main()
