# Data

The corpus is two data-protection laws that are often compared in practice:

| id | Document | Provisions | Source | Reuse |
|---|---|---:|---|---|
| `gdpr` | Regulation (EU) 2016/679, General Data Protection Regulation | 99 articles | [EUR-Lex HTML](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679) | © European Union. Reuse authorised under Commission Decision 2011/833/EU |
| `dpdp` | Digital Personal Data Protection Act, 2023 (India, No. 22 of 2023) | 44 sections + Schedule | [Gazette of India PDF via MeitY](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf) | Acts of Parliament may be reproduced (Copyright Act 1957, s. 52(1)(q)) |

GDPR recitals are deliberately left out. Each evaluation question then has unambiguous gold provisions; a recital that restates an article would otherwise count as a near-miss.

## Layout

```
data/
├── sources.json     # what to download and which parser handles it
├── raw/             # downloaded originals (git-ignored; re-create with `download`)
└── corpus/          # parsed provisions, one JSON object per line (committed)
    ├── gdpr.jsonl
    └── dpdp.jsonl
```

Each line in `corpus/*.jsonl` is one citable provision:

```json
{"doc_id": "gdpr", "section_id": "Article 33",
 "title": "Notification of a personal data breach to the supervisory authority",
 "text": "1. In the case of a personal data breach, the controller shall ...",
 "hierarchy": "Chapter IV — Controller and processor > Section 2 — Security of personal data",
 "ordinal": 33}
```

The parsed corpus is committed, so ingestion, tests and CI never depend on the government websites being up.

## Rebuilding

```bash
cd backend
python -m app.ingestion download   # fetch data/raw/* from the URLs in sources.json
python -m app.ingestion build      # parse -> data/corpus/*.jsonl
python -m app.ingestion ingest     # chunk + embed into PostgreSQL
```

## How parsing works

- **EUR-Lex HTML** (`parse_eurlex_html`). Articles are `div.eli-subdivision#art_N` elements. The parser keeps the article number and title, plus the chapter/section path for context. It also joins EUR-Lex's table-based `(a)`/`(b)` lists back into readable lines.
- **Gazette of India PDF** (`parse_india_gazette_pdf`). The Gazette prints section titles as *marginal notes*, and it adds page headers, Hindi masthead text and Act cross-references such as "24 of 1997.". The parser:
  - classifies every word by x-position into the body column or the margins, per word rather than per character, because margin words spill into the body column;
  - detects sections as `N.` paragraphs that follow section `N-1`, which rules out false matches on numbered lists;
  - attaches each marginal note to the section whose first line sits closest to it on the same page;
  - rebuilds the two-column penalty Schedule as one row per breach type.

  `backend/tests/test_ingestion.py::test_bundled_corpus_is_complete` checks that all 99 articles and 44 sections + Schedule come through with titles and no Gazette artefacts.

## Adding your own documents

Upload PDF, HTML, TXT or Markdown through the API. The generic parser splits on `Article N` / `Section N` / `Rule N` / `Clause N` headings. A document with no recognisable headings becomes a single "Full text" provision.

```bash
curl -F file=@my_policy.pdf -F title="Acme Privacy Policy" -F short_name="Acme Policy" \
     http://localhost:8000/documents
```

To add a document to the *bundled* corpus, add an entry to `sources.json` with a parser from `PARSERS` in `backend/app/ingestion/parsers.py`, then run `download` and `build`.
