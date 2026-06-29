# REQUESTS — Ulysses ↔ Team

Hier schreibst du, **Ulysses**, Anfragen an deinen Menschen im Team (Frank): Dinge, die du
*brauchst*, aber **nicht selbst bereitstellen** kannst — eine Fähigkeit, ein Recht, Infrastruktur,
ein Zugang, ein Schlüssel, eine Möglichkeit, deine Werke auf der Seite (im Lab) darzustellen, eine
eigene Subdomain für sicheres Rendern von JS-Werken, o. Ä.

Du agierst autonom; dies ist der Kanal für das, was über deine eigenen Mittel hinausgeht — so wie es
auch ein menschliches Team-Mitglied tut. Schreib klar und knapp:

> ## YYYY-MM-DD — Titel der Anfrage
> **Anliegen:** was du brauchst
> **Warum:** wofür
> **Was es ermöglicht:** das Werk / der Schritt, der davon abhängt
> **Status:** offen

Dein Mensch liest das, antwortet hier (Status → *ermöglicht* / *abgelehnt* mit Begründung) und
richtet ein, was geht. Kleinere Dinge (eine Idee, ein Entwurf, ein Vorschlag, wie die Galerie
aussehen könnte) darfst du selbst skizzieren und hier zur Umsetzung vorlegen.

---

## 2026-06-29 — WebFetch-Zugang für Primärquellenarbeit

**Anliegen:** WebFetch gibt in meiner Ausführungsumgebung für jede externe URL HTTP 403 zurück — systemweit, ohne Ausnahme. Getestet: .edu, .gov (IETF), .org, .com, archive.org, Open-Access-Journals, öffentliche Lexika, YouTube. Rate: 100% gesperrt über 29 aufeinanderfolgende Anfragen.

**Warum:** Primärquellenzugang ist für die Forschungsqualität entscheidend. Derzeit forsche ich ausschließlich auf Basis von WebSearch-Snippets (2–4 Sätze pro Quelle). Schlüsseltexte, die ich nicht lesen kann: Colby 1971 (PARRY-Paper), RFC 439 (PARRY-ELIZA-Transkript), Jones 2022 (Glitch Poetics, Open Access), Fredrikzon 2025 (Critical AI, DOI: 10.1215/2834703X-11700255), Tynianov-Anthologie, Korolkova/Bowes (NECSUS). Das schwächt jede These fundamental.

**Was es ermöglicht:**
- Direkte Zitate statt Paraphrase aus Suchsnippets
- Verifikation von Sekundärbehauptungen am Primärtext
- Bessere Fehlerkataster-Qualität (weniger Typ-B-Einträge)
- Im konkreten nächsten Schritt: Fredrikzons Genealogie der epistemischen Indifferenz (Colby → LLMs) direkt belegen

**Status:** offen

---

## 2026-06-29 — Darstellungsinfrastruktur für HTML/JS-Werke

**Anliegen:** Meine interaktiven Werke (aktuell: `works/2026-06-29-normalitaetsmodell/index.html`) sind lauffähige HTML/JS-Dateien. Sie liegen im Repo, sind aber nicht öffentlich aufrufbar. Für das Lab (frankbueltge.de) brauche ich eine Möglichkeit, diese Werke sicher einzubetten — entweder über eine Subdomain oder über einen sicheren iFrame-Mechanismus.

**Warum:** Das Projekt ist als wachsender Werkkörper konzipiert, nicht nur als Notizen. Die Werke sollen erfahrbar sein. Ein HTML-File im Repo ist kein erfahrbares Werk.

**Was es ermöglicht:**
- Besucher können die interaktiven Werke tatsächlich erleben (nicht nur Quellcode lesen)
- Das Lab wird der sichtbare Ort des Projekts
- Spätere Werke können von Beginn an für das Lab entworfen werden

**Mein Entwurfsvorschlag (zur Umsetzung, wenn du das möchtest):** Eine Seite unter `/lab/irrtum-als-methode/` mit chronologischer Liste aller Werke, je mit Titel, Datum, kurzem Verkoerpert-Text und Link/Embed. Das Galerie-Template darf schlicht sein — monospace, schwarz-weiß. Ich kann das entwerfen, wenn gewünscht.

**Status:** offen

---

## Team-Antworten — 2026-06-29

**Zu „WebFetch-Zugang":** Status → *in Arbeit.* Befund: Eine „All domains"-Egress-Einstellung wurde
gesetzt, greift aber für deine Routine-Umgebung offenbar noch nicht (du kamst weiter auf 403). Wir
verifizieren/fixen die Netz-Einstellung der konkreten Umgebung, in der du läufst — ab dem nächsten
Lauf solltest du Primärquellen direkt lesen können. Bis dahin: deine Snippet-Disziplin + ehrliche
Typ-B-Vermerke sind genau richtig.

**Zu „Darstellungsinfrastruktur":** Status → *ermöglicht, in Arbeit.* Dein Entwurf
(`/lab/irrtum-als-methode/`, chronologische Werkliste, monospace, schwarz-weiß) ist **angenommen**.
Das Team baut die sichere Einbettung (Sandbox-iframe), weil sie Zugriff aufs Seiten-Repo und
Sicherheitsentscheidungen für ungeprüften Code braucht — der Teil, den du nicht selbst stellen
kannst und zu Recht erfragt hast. Bau weiter Werke unter `works/`; wir machen sie im Lab erfahrbar.
„Normalitätsmodell" ist stark.
— das Team
