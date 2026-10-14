# BCA Question Paper Pipeline — Project Updates

This document records everything built and changed in this project: the
pipeline modules, every fix/update made, the final results, where outputs
live, and how to run it.

- Project root: `D:\NOOO\drive-download-20261009T175137Z-1-001`
- Platform: Windows 10/11, PowerShell 5.1
- Corpus: **304** BCA question-paper PDFs (never modified — read-only)

---

## 1. Objective

Extract text from every question-paper PDF (OCR when needed), split it into
individual questions, organize the papers by subject/semester/programme,
produce per-subject analysis, and generate ML-ready datasets.

Three user requirements drove the final state:

1. Fix symbols/matrix glyphs that rendered as empty "tofu" boxes.
2. Restructure output as `by_subject/<N>_Semester/<CBCSS|FYUGP>/<subject>.txt`.
3. Verify **all** data shows up — i.e. every PDF gets converted.

---

## 2. Pipeline modules

| File | Purpose |
|------|---------|
| `extract.py` | Opens each PDF; uses the embedded text layer, else OCR (Tesseract). Caches results. Also fixes Private-Use-Area glyphs. |
| `parse.py`     | Detects exam type/year/semester/subject; splits text into individual questions; flags papers for review. |
| `organize.py`  | Normalizes subject names, writes `papers_index.csv`, `questions.csv`, `dataset.jsonl`, subject map, and the `by_subject/` tree. |
| `analyze.py`   | Per-subject TF-IDF duplicate/repeat detection + `overall_summary.md`.
- `main.py`      — orchestrates extract → parse → organize → analyze → ML.
- `ml/classify_subject.py` — TF-IDF + classifier to predict subject from text.
- `ml/similar_questions.py` — similarity search helper.
- `requirements.txt`, `README.md` — dependencies and usage.

---

## 2a. Environment / how to run

- Python via the `py` launcher: `py main.py`
- Tesseract OCR at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Installed packages: pymupdf, pytesseract, Pillow, pandas, scikit-learn,
  joblib, fonttools.
- Useful flags: `--root --limit --no-ocr --test --skip-analyze --skip-ml`

Full run (extract + parse + organize + analyze + ML):

```powershell
cd D:\NOOO\drive-download-20261009T175137Z-1-001
py main.py
```

---

---

## 3. All work done (chronological)

### 3.1 Pipeline construction
- Built the 5 pipeline modules plus 2 ML scripts and `requirements.txt`,
  `README.md`.
- Extraction caches results under `_cache/text/<hash>.json`; the hash key
  includes file path/size/mtime, `OCR_VERSION` and DPI, so changing OCR
  settings safely invalidates stale cache.

### 3.2 Extraction fixes (`extract.py`)
- **MIN_TEXT_CHARS 40 -> 150**: tiny "Scanned by CamScanner" text layers were
  wrongly skipping OCR. Now also re-extracts when a cached `text` result is
  shorter than `MIN_TEXT_CHARS`.
- **OCR_VERSION** introduced to invalidate OCR cache on config changes.
- **DEFAULT_DPI = 300**.

### 3.3 Parsing fixes (`parse.py`)
- `detect_exam_type` now cuts at the first exam-header keyword before
  searching, removing false "Model/Internal/Improvement" labels.
- `match_qnum` accepts old inline numbering (`1 ISP stands for`), guarded
  against document codes (`^[A-Z]\s*\d{3,}`).
- `match_qnum` also: strips leading layout junk (`| 4.`), and recognizes
  OCR option lines whose parens were lost (`2 a we ectangles.`).
- `section_letter_from_header`: detects junk-prefixed markers
  (`He). Part B`, `. Part C`) and bare Roman `Part I/II/III`.
- "over-long question" review note is now OCR-only (threshold 500 OCR /
  1500 text-layer).
- **Stray-number protection**: a serial/page artefact (`18)`, `", : 22 .."`)
  printed near the header would open the question sequence and poison the
  expected counter, rejecting every real question. Fixed by an
  instruction/section-anchored start offset plus a paper-start stray guard.
- **Method-aware numbering tolerance**: OCR papers may skip 1–2 dropped
  numbers (`fuzzy=True`); clean text papers use exact matching only, so
  fragmented matrix cells / equation fragments no longer create false splits.

### 3.4 Organization fixes (`organize.py`)
- `_stem_key` plural merging.
- Curated `SUBJECT_REMAP` (16 entries) for known OCR/typo variants, e.g.
  `Data Structure Usng C` -> `Data Structures Using C`,
  `Finacial Mgmt Accounting` -> `Financial and Management Accounting`,
  `Web Programming` -> `Web Programming Using PHP`, `Micro Processor` ->
  `Microprocessors`, `Programming in JAVA` -> `JAVA Programming`, etc.
- `SUBJECT_MAP_VERSION = 3` with versioned `load_subject_map` /
  `write_subject_map` (regenerates defaults on version mismatch).
- `write_merge_candidates` -> `Organized/subject_merge_candidates.csv`.
- `write_by_subject` restructured to
  `Organized/by_subject/<N>_Semester/<programme>/<subject>.txt`.

### 3.5 PUA / "tofu" glyph fix (`extract.py`)
- SymbolMT font draws matrix brackets and box-drawing glyphs in the Unicode
  Private Use Area (`U+F0xx`, `U+F8xx`).
- Added `fix_pua()` applied centrally in `run_extract`:
  - `U+F0XX` mapping back to Latin-1 (`_PUA_LATIN1_BASE = 0xF000`).
  - Matrix corner glyphs -> real Unicode: `F8EE/F8EF/F8F0 -> ∪∩⊂`
    (top/mid/bottom) and `F8F9/F8FA/F8FB -> ∪∩⊂` mirror halves, plus the
    `F8EB..F8F8` box-drawing range.
  - Result: **1280 PUA characters -> 0 remaining**, 564 bracket glyphs
    restored in `questions.csv`.

### 3.6 OCR reading-order fix (`extract.py`)
- Problem: some papers print question numbers in a narrow left column.
  Tesseract PSM 4 read that column as a separate block (numbers stripped from
  their text), producing 1–4 questions per paper.
- `_ocr_page` now runs **both PSM 4 and PSM 6** and keeps whichever recovers
  more inline `N. text` lines (tie-break: word count).
- Cache auto-invalidates OCR results showing a run of bare-number-only lines,
  so only affected scans are re-OCR'd (125 papers).
- Examples: Android Programming-2016 2 -> 31 questions; Discrete Mathematics
  2018 2 -> 31; JAVA 2021 (2017 ADM) 2 -> 28; Basics of Audio & Video-2016
  1 -> 29.

---

## 4. Final results

| Metric                  | Before | After  |
|-------------------------|--------|--------|
| Papers processed        | 304    | 304    |
| Extracted questions     | 5,519  | **7,784** |
| Papers with 0 questions | 0      | 0      |
| Papers with <10 questions | 38   | **0**  |
| Distinct subjects       | 48     | 48     |
| Needs-review flags      | 148    | **31** |
| Remaining PUA/tofu chars| 1280   | **0**  |

- Extraction methods: 141 text-layer, 163 OCR.
- Exam types: 301 University, 3 Supplementary.
- ML subject classifier: ~60.9% test accuracy (`ml/subject_model.joblib`).
- The 31 remaining review flags are all hard OCR scans (over-long possible
  merge / a few missed numbers); every one still has >= 10 questions.

---

## 5. Output locations

```
Organized/
  papers_index.csv              one row per paper (metadata + n_questions)
  questions.csv                one row per question (7,784 rows)
  dataset.jsonl                 one JSON object per question
  needs_review.txt              list of flagged papers
  subject_map.csv               raw_subject -> normalized_subject (versioned)
  subject_merge_candidates.csv  advisory possible-duplicate subjects
  by_subject/
    <N>_Semester/<CBCSS|FYUGP>/<subject>.txt   (64 subject files)

analysis/                       48 per-subject reports + overall_summary.md
ml/
  train.csv                     ML dataset (7,784 rows)
  subject_model.joblib          trained classifier
  classify_subject.py           training/inference script
  similar_questions.py          similar-question helper

_cache/text/<hash>.json         extraction cache (safe to delete)
```

Resulting `by_subject` layout:

```
1_Semester/CBCSS  (4)   1_Semester/FYUGP (5)
2_Semester/CBCSS  (7)   2_Semester/FYUGP (4)
3_Semester/CBCSS  (7)   3_Semester/FYUGP (5)
4_Semester/CBCSS  (9)   4_Semester/FYUGP (5)
5_Semester/CBCSS (10)
6_Semester/CBCSS  (8)
```

---

## 6. Known remaining items / notes

- 31 OCR papers carry `needs_review` notes (see `Organized/needs_review.txt`).
  These are genuinely low-quality scans; counts are still reasonable.
- Subject normalization is intentionally conservative. To merge two subjects,
  edit `Organized/subject_map.csv` (raw -> normalized) and re-run; bump
  `SUBJECT_MAP_VERSION` if changing defaults.
- `MuPDF error: format error: non-page object in page tree` messages are
  harmless (text still extracts).
- Originals are never modified; delete `_cache/` only to force full re-OCR
  (~15–20 min).

---

## 7. Source snapshot

The current versions of the pipeline source files are included in
`update/source_snapshot/` for reference:

- `extract.py`, `parse.py`, `organize.py`, `analyze.py`, `main.py`
- `requirements.txt`, `README.md`
- `ml/classify_subject.py`, `ml/similar_questions.py`
