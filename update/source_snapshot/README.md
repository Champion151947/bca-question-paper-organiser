# BCA Question Paper Organiser

Organises BCA (Calicut-style CBCSS / FYUGP) university question papers by
subject, splits them into individual questions, produces analysis and ML-ready
datasets. **Original PDFs are never modified or deleted.**

## What it does

1. **Extract** text from every PDF with PyMuPDF; if a PDF has no text layer it
   is rendered and OCR'd with Tesseract (marked `ocr`).
2. **Parse** the header (programme, semester, subject, course code, year, month,
   exam type, max marks, time) and split the paper into questions
   (number, section, marks, text, "or" choice).
3. **Organise** the results into readable text files and CSV/JSONL datasets.
4. **Analyse** each subject: repeated questions, top keywords by marks,
   important questions, most-asked topics.
5. **Prepare ML** data and baseline scripts.

## Requirements

- Python 3.10+ (tested on 3.14)
- Tesseract OCR engine (only needed for scanned papers), e.g.:
  ```
  winget install --id UB-Mannheim.TesseractOCR -e
  ```

Install Python packages:

```
py -m pip install -r requirements.txt
```

## How to run

```
# 1. Preview the parser on 3 sample papers
py main.py --test

# 2. Full pipeline (extract -> parse -> organise -> analyse -> ML)
py main.py

# Options
py main.py --limit 20     # only the first 20 PDFs (quick test)
py main.py --no-ocr       # skip OCR of scanned PDFs
py main.py --skip-analyze --skip-ml
```

The first full run OCRs the scanned PDFs and can take a while. Text results are
cached in `_cache/text/`, so re-runs are fast. Delete `_cache/` to force a full
re-OCR.

## Output layout

```
Organized/
  by_subject/<Programme>/<Semester>_<Subject>.txt   readable per-subject papers
  questions.csv      one row per question (opens in Excel)
  dataset.jsonl      one record per question (ML-ready)
  papers_index.csv   one row per paper
  subject_map.csv    raw_subject -> normalized_subject (EDITABLE)
  needs_review.txt   papers with low-confidence fields
analysis/
  <Subject>_analysis.md
  overall_summary.md
ml/
  train.csv          text, subject, marks, section, year, programme
  classify_subject.py
  similar_questions.py
errors.log
_cache/text/         cached extracted text (safe to delete)
```

## Editing subjects

Open `Organized/subject_map.csv` and change the `normalized_subject` column to
merge or rename subjects. Re-run `py main.py` and the new names are applied
everywhere (your edits are preserved). By default subjects are only merged when
they differ merely by case, punctuation or `&`/`and`, so distinct subjects such
as *Data Structures Using C++* and *Datastructures & Algorithms* stay separate
until you decide to merge them.

## Modules

| File | Purpose |
|---|---|
| `extract.py` | find PDFs, extract text, optional OCR, cache, progress |
| `parse.py` | header metadata + question splitting + subject normalisation |
| `organize.py` | write by_subject files, CSVs, JSONL, index, needs_review |
| `analyze.py` | per-subject TF-IDF analysis + overall summary |
| `main.py` | runs everything end to end |

## ML scripts

```
py ml/classify_subject.py     # train TF-IDF + Logistic Regression, save model
py ml/similar_questions.py    # type a question, get 5 most similar past ones
```

## Notes

- Text extraction handles the two common paper layouts: new
  `Section A/B/C`, and old `Part A/B/C/D` / Roman-numeral sections.
- If a PDF fails, the error is written to `errors.log` and the run continues.
- OCR quality depends on scan quality; obviously rotated/watermarked scans may
  produce imperfect questions and are listed in `needs_review.txt`.
