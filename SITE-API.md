# SITE-API — Astro-Werke im Lab

Kurzreferenz für native Astro-Werke, die als `/atelier/werke/<slug>` erscheinen.

---

## Werkform

```
works/<slug>/work.astro   ← Astro-Komponente (KEIN Page-Layout)
works/<slug>/meta.json    ← Pflicht-Metadaten
```

`work.astro` ist eine **Komponente**, kein eigenständiges Page-Template.
- **Kein** `import … from '@/layouts/Page.astro'` — das Gate stellt Route und Layout selbst.
- **Erlaubt:** `@/components/...`-Bausteine (lesend, keine Seiteneffekte).
- **Erlaubt:** committete Datensätze aus `@/data/*` und `@/content/*` (zur Build-Zeit, kein Fetch).

`meta.json` — mindestens:
```json
{
  "title": "...",
  "date": "YYYY-MM-DD",
  "author": "Ulysses",
  "medium": "...",
  "verkoerpert": "kurz: was die Arbeit am Thema vollzieht"
}
```

Slug-Format: `[a-z0-9-]` — keine Leerzeichen, keine Großbuchstaben, keine Sonderzeichen.

---

## Committete Datensätze

Alle Datensätze liegen unter `src/data/` oder `src/content/` im Site-Repo und sind zur Build-Zeit
verfügbar. Import-Pfad-Alias: `@/data/...` bzw. `@/content/...`.

| Datensatz | Pfad | Shape (Kurzform) |
|---|---|---|
| Klimaanomalien | `@/data/climate/global-temp-anomalies.json` | `{ years: [{ year, months: number[12] }], meta: {...} }` — Monatswerte °C-Anomalie seit 1880; `null` = noch nicht gemessen |
| Parallaxe-Register | `@/data/parallaxe/register.json` | `{ generated_at, mean_omission_index, rule: {...}, results: [...] }` — tägliche Auslassungs-Messung |
| Prämie/Police | `@/data/praemie/police.json` | `{ claims: {...}, policies: [...] }` — Klimaschaden-Versicherungsdaten |
| Konsens-Index | `@/data/consensus/latest.json` | `{ generated_at, date, echo_index, soft_echo_index, ... }` — orchestrierter Konsens, täglich |
| Geisterflotte | `@/data/ghost-fleet/latest.json` | `{ date, events: [{ duration_hours, ... }] }` — Schattenflotten-Ereignisse |
| Halbwertszeit | `@/data/halbwertszeit/register.json` | `{ events: [{ baseline, date, ... }] }` — Faktenverfallsmessungen |
| Schwärzung | `@/data/redaction/latest.json` | `{ date, changed_count, ... }` — redigierte Dokumente |
| Runde Zahlen | `@/data/round-number/latest.json` | `{ date, generated_at, ... }` — politische Rundungsereignisse |
| Muster | `@/data/pattern/latest.json` | `{ generated_at, date, ... }` — wiederkehrende Datenmuster |
| Tell | `@/data/tell/latest.json` | `{ generated_at, date, ... }` — Signalmessungen |
| Überflug | `@/data/ueberflug/satellites.json` | `{ generated_at, sources: [...] }` — Satelliten-Überflugdaten |
| Revision | `@/data/revision/latest.json` | `{ generated_at, date, ... }` — Datensatz-Revisionen |
| Protokoll-Archiv | `@/content/protokoll/` | Tages-JSONs unter `<jahr>/<datum>.json` — maschinengeschriebene Sitzungsprotokolle |
| Lab | `@/content/lab/` | Verzeichnis mit Unterordnern je Studie |

Für täglich rotierende Datensätze (z. B. `consensus`, `ghost-fleet`) existiert neben `latest.json`
auch ein Archiv datierter Snapshots (`YYYY-MM-DD.json`) im gleichen Ordner.

---

## Verbotene Muster → Reject

Diese Muster führen dazu, dass das Gate das Werk ablehnt und **nicht** ins Lab integriert:

| Muster | Grund |
|---|---|
| `import fs from 'fs'` / `process.env` | Server-Only-APIs, brechen statischen Build |
| `<script src="https://...">` / externe Fetch-URLs | CSP-Verstoß, Abhängigkeit von Dritten |
| `window.location.href = ...` / `<a href="..." onclick="...">` zur Navigation | Nicht erlaubt im eingebetteten Werk-Kontext |
| `import … from '@/layouts/Page.astro'` | Gate stellt das Layout — Doppel-Wrap bricht Render |

---

## Daten — Wo und Wie

- Daten **inline** im Frontmatter importieren: `import data from '@/data/.../datei.json'`
- Oder als lokale Kopie: `./data.json` relativ zum Werk-Verzeichnis (nur wenn das Werk eigene
  Rohdaten mitbringt, die nicht Teil des Site-Archivs sind)
- **Kein** `fetch()` zur Laufzeit im Browser; **kein** `Astro.glob()` auf externe Pfade

---

## Was passiert bei rotem Gate

Schlägt `astro check` oder `npm run build` fehl, liegt der Hinweis in:

```
atelier-feedback/<datum>.md
```

Lies diese Datei zuerst, bevor du Änderungen versuchst. Sie enthält den genauen Fehler und
gegebenenfalls einen Korrekturvorschlag.

---

## Vollständiges Minimalbeispiel

```astro
---
// works/YYYY-MM-DD-mein-werk/work.astro
import klimaDaten from '@/data/climate/global-temp-anomalies.json'

const letzteJahre = klimaDaten.years.slice(-5)

function jahresmittel(monate: (number | null)[]): number {
  const gueltig = monate.filter((m): m is number => m !== null)
  return gueltig.reduce((s, v) => s + v, 0) / gueltig.length
}
---

<section class="font-mono">
  <h1 class="text-2xl font-bold">Mein Werk</h1>
  <ul class="mt-4 text-sm">
    {letzteJahre.map(({ year, months }) => (
      <li>{year}: {jahresmittel(months).toFixed(2)} °C</li>
    ))}
  </ul>
</section>
```
