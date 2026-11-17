"""Offline, evidence-supplied loadout search. Does not read or control the game.

All equipment choices/orders are enumerated. Accessory assignments use a beam,
so the retained shortlist is NOT a globally optimal build or a win predictor.
"""
import argparse
import html
import itertools
import json
import math
from pathlib import Path
import time


def placements(order, part, stride):
    ports = {(i * stride + x, y): g['id']
             for i, g in enumerate(order) for x, y in g['ports']}
    shape = part['shape']
    result = []
    for x, y in sorted(ports):
        pts = [(x + dx - shape[0][0], y + dy - shape[0][1]) for dx, dy in shape]
        if all(p in ports for p in pts):
            result.append({'part': part['id'], 'points': pts,
                           'owners': list(dict.fromkeys(ports[p] for p in pts))})
    return result


def conflicts(a, b, policy):
    if set(map(tuple, a['points'])) & set(map(tuple, b['points'])):
        return True
    if policy == 'endpoints':
        return False
    # Current catalog contains horizontal shapes only. Single holes also occupy body space.
    ap, bp = a['points'], b['points']
    return (ap[0][1] == bp[0][1]
            and max(min(p[0] for p in ap), min(p[0] for p in bp))
            <= min(max(p[0] for p in ap), max(p[0] for p in bp)))


def evaluate(order, parts, chosen, main_bonus):
    by_id = {p['id']: p for p in parts}
    values = {g['id']: dict(g, damage_pct=main_bonus, shield_pct=main_bonus,
                            element_pct=0, extra_hits=0, cd_pct=0) for g in order}
    cost = sum(g.get('price', 0) for g in order)
    links, output, dynamic = [], [], []
    for p in chosen:
        part = by_id[p['part']]
        cost += part.get('price', 0)
        e = part['effect']
        beneficiaries = []
        for owner in dict.fromkeys(p['owners']):
            g = values[owner]
            v = e.get('tagValue', e['value']) if e.get('tag') in g['tags'] else e['value']
            stat = e['stat']
            if (stat == 'damage_pct' and g['kind'] != 'attack'
                    and not g.get('acceptsDamagePct', False)):
                continue
            if stat == 'hits' and g['kind'] != 'attack' and not g.get('acceptsHits', False):
                continue
            if stat == 'shield_pct' and g.get('shield', 0) <= 0:
                continue
            if stat == 'main_pct':
                g['damage_pct'] += v
                g['shield_pct'] += v
            elif stat == 'hits':
                g['extra_hits'] += v
            elif stat in ('main_per_second', 'debuff_growth'):
                dynamic.append(dict(part=part['id'], equipment=owner, stat=stat, value=v,
                                    status='未模拟，不代表收益为零'))
            elif stat == 'charge':
                if len(p['owners']) < 2:
                    continue
            else:
                g[stat] += v
            beneficiaries.append(owner)
        if e['stat'] == 'charge' and len(p['owners']) > 1:
            links.append({'equipment': p['owners'], 'seconds': e['value'],
                          'trigger': '使用一端使另一端加速，持续指定秒数；不是立即充能，多段不自动视为多次使用'})
        output.append(dict(p, beneficiaries=beneficiaries))
    equipment = []
    for g in values.values():
        equipment.append({'id': g['id'], 'name': g['name'], 'slot': g['slot'],
                          'damage': math.ceil(g.get('damage', 0) * (1 + g['damage_pct'])),
                          'shield': math.ceil(g.get('shield', 0) * (1 + g['shield_pct'])),
                          'element': math.ceil(g.get('element', 0) * (1 + g['element_pct'])),
                          'hits': g.get('hits', 1) + g['extra_hits'],
                          'cooldown': round(g['cooldown'] * max(.01, 1 + g['cd_pct']), 3),
                          'kind': g['kind'], 'tags': g['tags'], 'passive': g.get('passive', '')})
    attack = [g for g in equipment if g['kind'] == 'attack']
    cores = [g for g in attack if g['slot'] in ('hand', 'shoulder')]
    metrics = {'baseVolley': sum(g['damage'] * g['hits'] for g in cores),
               'baseDps': round(sum(g['damage'] * g['hits'] / g['cooldown'] for g in cores), 1),
               'shieldPerCastSum': sum(g['shield'] for g in equipment),
               'coreCdSum': round(sum(g['cooldown'] for g in cores), 3),
               'firmPerVolley': sum(g['element'] * g['hits'] for g in cores if 'firm' in g['tags']),
               'chargeLinks': len(links),
               'coreChargeTargets': sum(sum(id in {g['id'] for g in cores} for id in link['equipment']) for link in links),
               'effectiveEndpoints': sum(len(p['beneficiaries']) for p in output),
               'summonsPerCastSum': sum(g['hits'] for g in equipment if g['kind'] == 'summon'),
               'deploymentForcePerCast': sum(g['hits'] * values[g['id']].get('deploymentForce', 0)
                                             for g in equipment if g['kind'] == 'summon')}
    return {'order': [g['id'] for g in order], 'equipment': equipment, 'placements': output,
            'cost': cost, 'metrics': metrics, 'chargeLinks': links, 'dynamicEffects': dynamic}


def scores(r):
    m = r['metrics']
    # Transparent, deliberately different shortlist heuristics. None is battle power.
    return (m['baseDps'] / 1000 + m['firmPerVolley'] / 1000 + m['chargeLinks'],
            m['shieldPerCastSum'] / 1000 + m['firmPerVolley'] / 100 + m['chargeLinks'],
            -m['coreCdSum'] * 10 + m['coreChargeTargets'] * 10 + m['chargeLinks'] + m['baseDps'] / 10000)


def validate(d):
    if d['gold'] < 0 or d['stride'] <= 0:
        raise ValueError('invalid budget/grid')
    for key in ('equipment', 'parts'):
        ids = [x['id'] for x in d[key]]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate instance IDs')
        for item in d[key]:
            if item.get('price', 0) < 0:
                raise ValueError('sale proceeds cannot be prepaid')
    for g in d['equipment']:
        if g['slot'] not in d['slots'] or g['cooldown'] <= 0:
            raise ValueError('invalid equipment slot/CD')
        if len(g['ports']) != len(set(map(tuple, g['ports']))):
            raise ValueError('duplicate ports')
    for p in d['parts']:
        if not p['shape'] or len({y for x, y in p['shape']}) != 1:
            raise ValueError('only evidenced horizontal shapes supported in v1')
        if len(p['shape']) != len(set(map(tuple, p['shape']))):
            raise ValueError('duplicate shape endpoints')


def search(d, beam=12, limit=48, policy='solid'):
    validate(d)
    started = time.perf_counter()
    groups = [[g for g in d['equipment'] if g['slot'] == slot] for slot in d['slots']]
    parts = d['parts']
    pool, champions = [], {}
    orders = expanded = finals = 0
    for selected in itertools.product(*groups):
        base_cost = sum(g.get('price', 0) for g in selected)
        if base_cost > d['gold']:
            continue
        for order in itertools.permutations(selected):
            orders += 1
            base = evaluate(order, [], [], d.get('mainBonus', 0))
            bs = scores(base)
            options = []
            for part in parts:
                ps = placements(order, part, d['stride'])
                opts = []
                for p in ps:
                    one = evaluate(order, [part], [p], d.get('mainBonus', 0))
                    if not one['placements'][0]['beneficiaries']:
                        continue
                    ss = scores(one)
                    opts.append((p, tuple(x-y for x, y in zip(ss, bs))))
                options.append((part, opts))
            # Few options first reduces beam loss; accessory combinations still not exhaustive.
            options.sort(key=lambda x: len(x[1]))
            states = [((), base_cost, (0., 0., 0.))]
            for part, opts in options:
                next_states = list(states)  # leaving a part unused is always allowed
                for used, cost, score in states:
                    if cost + part.get('price', 0) > d['gold']:
                        continue
                    for p, gain in opts:
                        if not any(conflicts(p, q, policy) for q in used):
                            next_states.append((used+(p,), cost+part.get('price', 0),
                                                tuple(x+y for x, y in zip(score, gain))))
                expanded += len(next_states)
                unique = {}
                for axis in range(3):
                    for state in sorted(next_states, key=lambda s: (s[2][axis], -s[1]), reverse=True)[:beam]:
                        key = tuple((p['part'], tuple(p['points'])) for p in state[0])
                        unique[key] = state
                states = list(unique.values())
            for used, cost, _ in states:
                r = evaluate(order, parts, used, d.get('mainBonus', 0))
                r['remainingGold'] = d['gold'] - cost
                r['scores'] = scores(r)
                r['unusedParts'] = [p['id'] for p in parts if p['id'] not in {x['part'] for x in used}]
                r['purchases'] = [g['id'] for g in order if g.get('price', 0)] + [p['part'] for p in used if next(a for a in parts if a['id'] == p['part']).get('price', 0)]
                r['replacedEquipment'] = [x for x in d.get('currentOrder', []) if x not in r['order']]
                pool.append(r)
                finals += 1
                combo = tuple(sorted(r['order']))
                for axis in range(3):
                    key = (combo, axis)
                    if key not in champions or r['scores'][axis] > champions[key]['scores'][axis]:
                        champions[key] = r
            if len(pool) > limit * 12:
                pool = [r for axis in range(3) for r in sorted(pool, key=lambda r: r['scores'][axis], reverse=True)[:limit]]
    # Include a representative of each equipment replacement set, not only high raw damage.
    rankings = [sorted(pool, key=lambda r: r['scores'][axis], reverse=True) for axis in range(3)]
    result, seen = [], set()
    def add(r):
        key = (tuple(r['order']), tuple(sorted((p['part'], tuple(p['points'])) for p in r['placements'])))
        if key not in seen:
            seen.add(key)
            result.append(r)
    for key in sorted(champions):
        add(champions[key])
    for row in itertools.zip_longest(*rankings):
        if len(result) >= limit:
            break
        for r in row:
            if r is not None and len(result) < limit:
                add(r)
    return {'policy': policy, 'candidates': result,
            'metrics': {'equipmentOrders': orders, 'expandedStates': expanded,
                        'evaluatedFinals': finals, 'retained': len(result),
                        'seconds': round(time.perf_counter()-started, 3), 'beamPerObjective': beam},
            'limitations': ['装备集合及排列完整枚举，配件分配为束搜索，不保证全局最优。',
                            '全部结果仅为模型候选，未在游戏安装验证。',
                            '没有模拟力量/坚固转伤、失盾成长、动画、控制、随机充能与敌人；不预测胜率。',
                            '只支持已录入水平形状；交叠规则按所选假设，失败拖动未当作几何证明。']}


def render(d, results, target):
    payload = json.dumps({'input': d, 'results': results}, ensure_ascii=False).replace('<', '\\u003c')
    template = Path(__file__).with_name('loadout-template.html').read_text(encoding='utf-8')
    Path(target).write_text(template.replace('__PAYLOAD__', payload), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--html', required=True)
    ap.add_argument('--beam', type=int, default=8)
    ap.add_argument('--limit', type=int, default=48)
    args = ap.parse_args()
    if args.beam < 1 or args.limit < 1:
        ap.error('beam and limit must be positive')
    d = json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    results = [search(d, args.beam, args.limit, policy) for policy in ('solid', 'endpoints')]
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    render(d, results, args.html)
    print(json.dumps([dict(policy=r['policy'], **r['metrics']) for r in results]))


if __name__ == '__main__':
    main()
