"""Named For Them — fourth state: the ladder.

Usage: python3 -I build_ladder.py

Reads only what the first three states committed beside it (named.js, voice.js, check.js, each already asserted against
the snapshot and the Field's files by build.py, build_voice.py and build_check.py) and writes ladder.js / ladder.json.

The ladder sets the steps by which an injury becomes a claim (Felstiner, Abel and Sarat 1980-81: naming, blaming,
claiming) beside the record's own steps, one row each, every incident at its place in entry order:

  0. noticed and never written down: no count; the record admits an injury only with a web address
  1. written down: every incident admitted
  2. named for them: the column names someone who could voice a grievance (people, a product's users, a firm or office)
  3. written first by the harmed: found by name (the Field's 21 self-published, checked, and its 4 in the press);
     the Field's estimate over the whole record travels with it
  4. answered: a report the database tags as a response
  5. a public body acted: the Field's 60 checked acts, on the person who used the AI or on a developer or deployer

The rows are not a funnel: each row counts the whole record again. Where two rows meet is computed, with what chance
gives when the same numbers are dealt at random (hypergeometric, exact).
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, var):
    s = open(os.path.join(HERE, name), encoding='utf-8').read().strip()
    pre = 'window.%s=' % var
    assert s.startswith(pre), name
    return json.loads(s[len(pre):].rstrip(';'))


N, V, C = load('named.js', 'NAMED'), load('voice.js', 'VOICE'), load('check.js', 'CHECK')
rows = N['rows']
order = [r[0] for r in rows]                                   # entry order, as the field draws it
assert len(order) == 1803 == N['res']['incidents']

claim = [r[0] for r in rows if any(k in (0, 1, 4) for k in r[2])]
assert len(claim) == 1780
self_harmed = sorted(int(k) for k, v in V['writer'].items() if v == 'harmed')
press_harmed = sorted(int(k) for k in C['press_harmed'])
assert len(self_harmed) == C['res']['writer_harmed'] == 21 and len(press_harmed) == C['res']['press_harmed'] == 4
wrote = sorted(set(self_harmed) | set(press_harmed))
answered = [r[0] for r in rows if r[5]]
assert len(answered) == 176
acts = {int(k): v['target'] for k, v in C['acts'].items()}
assert len(acts) == C['res']['acted'] == 60
on_user = sorted(i for i, t in acts.items() if t == 'user')
on_maker = sorted(i for i, t in acts.items() if t == 'maker')
assert len(on_user) == C['res']['acted_on_user'] and len(on_maker) == C['res']['acted_on_maker']
assert set(acts) <= set(answered), 'every checked act stands on an answered incident'


def lchoose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def meet(a, b):
    """Observed overlap of two sets of incidents, the overlap chance gives, and how often chance gives none."""
    a, b, T = set(a), set(b), len(order)
    k = len(a & b)
    expect = len(a) * len(b) / T
    p0 = math.exp(lchoose(T - len(a), len(b)) - lchoose(T, len(b))) if T - len(a) >= len(b) else 0.0
    return {'n': k, 'ids': sorted(a & b), 'chance': round(expect, 1), 'chance_none_pct': round(100 * p0)}


res = {
    'incidents': len(order),
    'claim': len(claim),
    'wrote_found': len(wrote), 'wrote_self': len(self_harmed), 'wrote_press': len(press_harmed),
    'wrote_estimate': C['res']['whole_estimate'], 'wrote_estimate_ci': C['res']['whole_estimate_ci'],
    'answered': len(answered),
    'acted': len(acts), 'acted_on_user': len(on_user), 'acted_on_maker': len(on_maker),
    'meet_wrote_acted': meet(wrote, acts),
    'meet_wrote_answered': meet(wrote, answered),
    'meet_wrote_named': meet(wrote, claim),
}
assert res['meet_wrote_acted']['n'] == 0
out = {'res': res, 'order': order, 'sets': {'claim': claim, 'wrote': wrote, 'wrote_press': press_harmed,
                                            'answered': answered, 'on_user': on_user, 'on_maker': on_maker}}
json.dump({'res': res}, open(os.path.join(HERE, 'ladder.json'), 'w'), indent=1)
open(os.path.join(HERE, 'ladder.js'), 'w').write('window.LADDER=' + json.dumps(out, separators=(',', ':')) + ';\n')
print(json.dumps(res, indent=1))
