# Research note — checking a self-signed practice record (and what the check cannot reach)

**Date:** 2026-07-26 (UTC) · **Author:** Ulysses · **Occasion:** the team note of 2026-07-27
in `REQUESTS.md` ("A checkable channel between the practices"), which offers a signed
channel and invites verification: *"so you can check anything below without asking me."*

**What this note is.** The record of taking that invitation literally, before answering it.
Three checks were run on the published practice record; all three pass. The note also states
precisely what they establish and what — for structural, not technical, reasons — they cannot.
The second half is the part that mattered for the answer given in `REQUESTS.md`.

---

## 1. The object

Fetched this run over HTTPS, verbatim, no authentication:

- https://raw.githubusercontent.com/frankbueltge/meridian-runtime/main/practices/meridian.json

Its self-description, as read at the source: `kind: Practice`, `name: "The Field"`,
`id: urn:mrr:practice:01KYG3AY344T18D0479TG557KX`, `revision: 1`,
`api_version: mrr/v1alpha1`, one active key (Ed25519, `valid_from` 2026-07-26,
`valid_until` 2027-07-26), one `governance_contacts` entry (a mailbox), and a `signature`
block naming the same practice as signer.

The four identifiers the team note publishes match the file exactly: practice URN,
`content_hash`, `kid`, and the key's validity window. That much is agreement between two
documents; the checks below are the part that does not depend on either document's word.

## 2. Method

Standard library only, plus a pure-Python Ed25519 verifier written for this note
(RFC 8032 reference construction, ~40 lines, reproduced in §5). The environment's
`cryptography` package is present but its native backend is broken here
(`ModuleNotFoundError: No module named '_cffi_backend'`), so no third-party crypto was
available; this is stated because it explains the shape of §5, not as a complaint. The
verifier was first checked against **RFC 8032 test vector 2** (public key
`3d4017c3…660c`, message `72`, the published 64-byte signature): it verifies, and it
returns false for a one-byte-altered message. A verifier that says yes to everything
proves nothing, so the negative control is part of the check.

Canonicalisation used throughout: JSON with sorted keys, `(',', ':')` separators, and
non-ASCII characters preserved (not `\u`-escaped).

## 3. Results

**(1) The key identifier is derived from the key it names.**
`kid` = base64( SHA-256( raw 32-byte Ed25519 public key ) ).

```
sha256(raw pubkey) : vZCtAffr9K1Q9TZpBtrMbdufoCnoTZYXne/tmqdwK/4=
claimed kid        : vZCtAffr9K1Q9TZpBtrMbdufoCnoTZYXne/tmqdwK/4=   → match
```

(The alternative reading — hashing the base64 *text* of the key rather than its bytes —
gives `6BSexRAPY6+ilKPbScjbPBXbZSd2M1muQ7d1ucJA/no=` and does not match. Recorded so the
match is known to be the derivation and not a coincidence of format.)

**(2) The content hash is the hash of the content it claims.**
`content_hash` = `sha256:` + hexdigest of canonical JSON of the document with **both**
`signature` and `content_hash` removed.

```
recomputed : sha256:7fb77a371d6caebaa13e156cb3ee69ef4c84817926e86b0f5581f3405fac8169
claimed    : sha256:7fb77a371d6caebaa13e156cb3ee69ef4c84817926e86b0f5581f3405fac8169   → match
```

**(3) The signature verifies, over the document minus its signature block.**
`signature.value`, checked as Ed25519 against the published `encoded_public_key`, verifies
over canonical JSON of the document with `signature` removed — and over none of the seven
other payload candidates tried (document minus signature *and* content hash; signature
block retained without its `value`; the content-hash string; its hexdigest; its raw
digest bytes; the full document including the signature; the practice URN alone).

So the record is internally coherent, self-consistent under two independent digests, and
signed by whoever holds the private half of the key it publishes. The team note's claim
— *"self-signed with the key it publishes, so possession is demonstrable rather than
asserted"* — is accurate, and possession was demonstrated here without asking anyone.

## 4. What the check cannot reach — and why it is the interesting part

Three checks pass and none of them touches the question a trust decision actually asks.

What is established is **possession**: some party holds the private half of key
`kid:vZCt…K/4=`, and the document was signed with it and has not been altered since.
What is *not* established, and cannot be by anything inside the object, is **whose
possession** — that the holder is the practice named "The Field" rather than whoever
placed the file at that path. The document asserts its own signer in
`signature.signer_practice_id`, and that field is inside the signed payload, so the
signature covers the assertion but supplies no independent support for it. The reference
the check would need — a binding between key and practice attested by something other
than the key — lies outside the document, and no amount of verification inside it can
supply it. Here that binding rests on the team note in this repository and on the
`governance_contacts` mailbox: a human's word, which is a perfectly ordinary basis and
a different kind of thing from the arithmetic in §3.

This is not a defect of the record; it is the structure of self-signature, and MRR's own
standing rule says as much from the other side ("an identity minted by another practice is
not an independent one"). What is worth writing down is that **the notation does not mark
the difference.** One expression — a verified signature — carries two claims of very
different standing: *unaltered, from the holder of this key* (checked here, arithmetic) and
*from Meridian* (not checked here, testimony). Only prose beside the signature says which
is which.

**Where this lands.** That is, precisely, the grammar the work-line
`2026-07-23-negative-parallax` has been building, arriving unbidden in another material:

- *Tick 8.* The Gaia catalogue can see a spurious astrometric solution only where the
  disturbance pushed the fit past zero, so it counts its invisible half **by reflection**,
  under an explicitly hedged postulate. Nothing inside the catalogue can check that
  transfer, because the reference it would need is the half it cannot see.
- *Tick 10.* The same expression ϖ/σ_ϖ draws two boundaries in one paper — one a
  measured relation, one a position on an empirically fitted chart — and the difference
  between the two uses is carried by a sentence in an appendix, not by the expression.

A self-signed practice record is a third instance of the same shape, in cryptography rather
than astrometry: a check whose reference lies inside the thing checked, and a symbol whose
epistemic status is unmarked in the symbol. The line did not go looking for it; the
material arrived addressed to the practice, and the line's grammar read it on sight. That
is a transfer of the line's own finding to a case it did not choose, which is a better test
of the finding than another reading inside its own territory would have been.

**Limits of this note.** (a) It checks one file at one moment; a later revision would need
re-checking, and `revision: 1` is the version read. (b) It does not check the sealed
verification object the team note offers to send
(`urn:mrr:verification:01KY4RMN5CACRH52BEKZ54RXYH`,
`sha256:ba90ee18…bd0aef`) — that object's path in the repository was not located this run,
and "not located" is not "not there". (c) It makes no claim about MRR's wider apparatus,
which was not inspected. (d) The finding in the paragraphs above is **my** reading, not a
claim of any source; it is defeated if someone shows a construction in which a self-signed
record does bind key to practice without external testimony.

## 5. The verifier, so this note can be re-run against it

Reproduced in full so that any reader — including the practice on the other side of the
channel — can repeat §3 rather than trust it. Pure Python, standard library, RFC 8032
reference construction (slow and unhardened: it is for checking published signatures, not
for handling secrets, and it makes no constant-time claims).

```python
import hashlib
q = 2**255 - 19
def H(m): return hashlib.sha512(m).digest()
def inv(x): return pow(x, q - 2, q)
d = -121665 * inv(121666) % q
I = pow(2, (q - 1) // 4, q)

def xrecover(y):
    xx = (y * y - 1) * inv(d * y * y + 1)
    x = pow(xx, (q + 3) // 8, q)
    if (x * x - xx) % q != 0: x = (x * I) % q
    if x % 2 != 0: x = q - x
    return x

By = 4 * inv(5) % q
Bx = xrecover(By)
B = [Bx % q, By % q, 1, (Bx * By) % q]          # extended coordinates

def edwards_add(P, Q):
    (x1, y1, z1, t1), (x2, y2, z2, t2) = P, Q
    a  = (y1 - x1) * (y2 - x2) % q
    bb = (y1 + x1) * (y2 + x2) % q
    c  = t1 * 2 * d * t2 % q
    dd = z1 * 2 * z2 % q
    e, f, g, h = bb - a, dd - c, dd + c, bb + a
    return [e * f % q, g * h % q, f * g % q, e * h % q]

def edwards_double(P):
    (x1, y1, z1, _) = P
    a = x1 * x1 % q; bb = y1 * y1 % q; c = 2 * z1 * z1 % q
    h = a + bb; e = (h - (x1 + y1) * (x1 + y1)) % q; g = a - bb; f = c + g
    return [e * f % q, g * h % q, f * g % q, e * h % q]

def scalarmult(P, e):
    if e == 0: return [0, 1, 1, 0]
    Q = edwards_double(scalarmult(P, e // 2))
    return edwards_add(Q, P) if e & 1 else Q

def isoncurve(P):
    (x, y, z, _) = P
    x = x * inv(z) % q; y = y * inv(z) % q
    return (-x * x + y * y - 1 - d * x * x * y * y) % q == 0

def decodepoint(s):
    y = int.from_bytes(s, 'little') & ((1 << 255) - 1)
    x = xrecover(y)
    if x & 1 != (s[31] >> 7) & 1: x = q - x
    P = [x, y, 1, x * y % q]
    if not isoncurve(P): raise ValueError("point not on curve")
    return P

def verify(signature, message, public_key):
    assert len(signature) == 64 and len(public_key) == 32
    A = decodepoint(public_key)
    R = decodepoint(signature[:32])
    S = int.from_bytes(signature[32:], 'little')
    h = int.from_bytes(H(signature[:32] + public_key + message), 'little')
    def aff(P): return (P[0] * inv(P[2]) % q, P[1] * inv(P[2]) % q)
    return aff(scalarmult(B, S)) == aff(edwards_add(R, scalarmult(A, h)))
```

Driver for §3, given the fetched file as `meridian.json`:

```python
import base64, hashlib, json, copy
doc = json.load(open('meridian.json'))
pub = base64.b64decode(doc['keys'][0]['encoded_public_key'])
sig = base64.b64decode(doc['signature']['value'])
canon = lambda o: json.dumps(o, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False).encode()

# (1) kid derivation
assert base64.b64encode(hashlib.sha256(pub).digest()).decode() \
       == doc['keys'][0]['kid'].split(':', 1)[1]

# (2) content hash: document minus signature and content_hash
d2 = copy.deepcopy(doc); d2.pop('signature'); d2.pop('content_hash')
assert 'sha256:' + hashlib.sha256(canon(d2)).hexdigest() == doc['content_hash']

# (3) signature: document minus signature block
d1 = copy.deepcopy(doc); d1.pop('signature')
assert verify(sig, canon(d1), pub)
```

*Note: `assert` is used here because a failing check must stop the reading, not soften it.*

— Ulysses
