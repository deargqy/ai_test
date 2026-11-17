"""Audited, narrowly scoped screenshot cleanup. Plan first; explicit apply second."""
import collections
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'runs/run05/image-retention-audit.json'
IMAGE = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}
TEXT = {'.md', '.json', '.jsonl', '.html', '.js', '.cjs', '.css', '.py', '.txt', '.csv', '.yaml', '.yml'}
IMPORTANT = re.compile(r'enemy|opponent|boss|danger|result|stats|buff|defense|tech|tooltip|rule|pilot|version|final|verified|complete|victory|loss|fight|battle|combat|frame|gear|part|choice|upgrade|detail|timed|numbers|force|cooldown|-(hand|back|armor|shoulder|drone)\.', re.I)
TRANSIENT = re.compile(r'clear|return|click|focus|drag|staged|stage-|pick|cancel|reorder|reopen|restor|detach|adjust|anchor|retry|rebound|close|sale-|sell-|sold|buy-|bought|start|shop|inventory|reward|event|resum|enter|equipp|install|fit-|selected|swap|transfer', re.I)

def tracked():
    return [ROOT / p for p in subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True, encoding='utf-8').splitlines()]

def rel(p):
    return p.relative_to(ROOT).as_posix()

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe(p):
    resolved = p.resolve(strict=True)
    assert resolved.is_relative_to(ROOT / 'docs'), resolved
    assert resolved.parent.name.startswith('playtest-'), resolved
    assert resolved.suffix.lower() in IMAGE and resolved.is_file() and not p.is_symlink(), resolved
    return resolved

def sources(paths):
    # Historical removal manifests are provenance, not live consumer references.
    return [p for p in paths if p.is_file() and p.suffix.lower() in TEXT
            and 'screenshot-cleanup' not in p.name
            and p not in {REPORT, Path(__file__).resolve()}]

def references(paths, images):
    refs = collections.defaultdict(set)
    known = {p.name.casefold(): p.name for p in images}
    for p in sources(paths):
        s = p.read_text(encoding='utf-8', errors='replace')
        # ASCII filename tokenization also handles Chinese prose touching a filename.
        for n in re.findall(r'[A-Za-z0-9_.@+-]+\.(?:jpe?g|png|webp|gif|svg)\b', s, re.I):
            if n.casefold() in known:
                refs[n.casefold()].add(rel(p))
    return refs

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'src', 'href', 'poster'} and value:
                self.urls.append(value)
            if key == 'srcset' and value:
                self.urls.extend(v.strip().split()[0] for v in value.split(','))

def html_links(paths):
    missing, checked, templates = [], 0, []
    for p in paths:
        if not p.is_file() or p.suffix != '.html':
            continue
        parser = Links(); parser.feed(p.read_text(encoding='utf-8'))
        # These fragments/templates are inserted into generated pages under docs/.
        base = p.parent
        if rel(p) in {'tools/loadout-template.html', 'runs/run05/day16-armor-report-section.html'}:
            base = ROOT/'docs'
            templates.append({'source':rel(p), 'renderBase':'docs/'})
        for raw in parser.urls:
            url = urlsplit(raw)
            if url.scheme or url.netloc or not url.path or any(c in raw for c in '{}'):
                continue
            target = (base / unquote(url.path)).resolve()
            checked += 1
            if not target.exists():
                missing.append({'source': rel(p), 'url': raw})
    return {'checked': checked, 'missing': missing, 'templateRenderContexts': templates}

def plan():
    paths = tracked(); images = [p for p in paths if p.is_file() and p.suffix.lower() in IMAGE]
    assert all(p.name.isascii() for p in images), 'Review non-ASCII filenames before tokenizing'
    refs = references(paths, images)
    hashes = {rel(p): digest(p) for p in images}
    groups = collections.defaultdict(list)
    for p in images:
        groups[hashes[rel(p)]].append(p)
    remove, keep = [], []
    for p in images:
        r = rel(p); duplicate = None
        protection = ('consumer-reference' if refs[p.name.casefold()] else
                      'protected-evidence' if '/bugs/' in r or '/model-view-qa/' in r or IMPORTANT.search(p.name) else
                      'out-of-scope' if not (p.is_relative_to(ROOT/'docs') and p.parent.name.startswith('playtest-')) else None)
        if not protection:
            peers = groups[hashes[r]]
            keeper = min(peers, key=lambda q: (not bool(refs[q.name.casefold()]), not bool(IMPORTANT.search(q.name)), rel(q)))
            if keeper != p:
                duplicate = rel(keeper)
        reason = 'unreferenced-exact-duplicate' if duplicate else 'unreferenced-intermediate-ui' if not protection and TRANSIENT.search(p.name) else None
        item = {'path': r, 'bytes': p.stat().st_size, 'sha256': hashes[r]}
        if reason:
            safe(p)
            item.update(reason=reason)
            if duplicate:
                item['identicalKeptImage'] = duplicate
            remove.append(item)
        else:
            item.update(reason=protection or 'uncertain-unique-evidence', referenceSources=sorted(refs[p.name.casefold()]))
            keep.append(item)
    deleted = {r['path'] for r in remove}
    # Do not remove a representative needed to explain an exact duplicate.
    required = {r['identicalKeptImage'] for r in remove if 'identicalKeptImage' in r}
    for r in list(remove):
        if r['path'] in required:
            remove.remove(r); r['reason'] = 'duplicate-representative'; keep.append(r)
    data = dict(status='planned', baseCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        policy='Keep every live literal reference, all bug/pilot/version/model QA and combat/equipment/tech evidence. Delete only unreferenced exact duplicates or identifiable intermediate UI captures. Preserve uncertain unique evidence. Prior cleanup manifests are historical provenance.',
        baseline={'images':len(images),'bytes':sum(x.stat().st_size for x in images)},
        beforeLinks=html_links(paths), delete=remove, keep=keep,
        expectedFreedBytes=sum(x['bytes'] for x in remove))
    REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'images':len(images),'delete':len(remove),'keep':len(keep),'freedMiB':round(data['expectedFreedBytes']/2**20,2),'links':data['beforeLinks'],'byReason':dict(collections.Counter(x['reason'] for x in remove))},ensure_ascii=False))

def apply():
    data=json.loads(REPORT.read_text(encoding='utf-8'))
    assert data['status']=='planned'
    assert data['baseCommit']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths=tracked(); images=[p for p in paths if p.is_file() and p.suffix.lower() in IMAGE]
    refs=references(paths,images)
    for item in data['delete']:
        p=safe(ROOT/item['path'])
        assert not refs[p.name.casefold()], str(p)
        assert digest(p)==item['sha256'] and p.stat().st_size==item['bytes']
    # Validation above completes for every target before the first unlink.
    for item in data['delete']:
        safe(ROOT/item['path']).unlink()
    data['status']='deleted-awaiting-validation'
    REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    check()

def check():
    data=json.loads(REPORT.read_text(encoding='utf-8'))
    for item in data['keep']:
        p=ROOT/item['path']; assert p.is_file() and digest(p)==item['sha256'], item['path']
    assert all(not (ROOT/x['path']).exists() for x in data['delete'])
    after=html_links(tracked())
    assert after['missing']==data['beforeLinks']['missing'], after
    data.update(status='verified',afterLinks=after,after={'images':len(data['keep']),'bytes':sum(x['bytes'] for x in data['keep'])})
    REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':data['status'],'deleted':len(data['delete']),'kept':len(data['keep']),'freedMiB':round(data['expectedFreedBytes']/2**20,2),'afterLinks':after},ensure_ascii=False))

if __name__=='__main__':
    {'plan':plan,'apply':apply,'check':check}[sys.argv[1]]()
