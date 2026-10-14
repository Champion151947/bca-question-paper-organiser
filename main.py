"""main.py - End-to-end pipeline for organising BCA question papers.

Usage:
    python main.py                 # run everything
    python main.py --limit 20      # only first 20 PDFs
    python main.py --no-ocr        # skip OCR of scanned PDFs
    python main.py --test          # preview parsing of 3 sample papers
    python main.py --skip-analyze --skip-ml

Outputs:
    Organized/    by_subject/*.txt, questions.csv, dataset.jsonl,
                  papers_index.csv, subject_map.csv, needs_review.txt
    analysis/     <Subject>_analysis.md, overall_summary.md
    ml/           train.csv, classify_subject.py, similar_questions.py
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from extract import extract_pdf, find_pdfs, run_extract, find_tesseract  # noqa: E402
from parse import parse_paper, MONTH_NAMES  # noqa: E402
import organize as organize_mod  # noqa: E402


def make_logger(path: str):
    def log(source: str, message: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s :: %s\n" % (ts, source, message))
    return log


def write_train_csv(path: str, papers, qbp) -> int:
    pmap = {p["paper_id"]: p for p in papers}
    rows = []
    for pid, qs in qbp.items():
        p = pmap.get(pid)
        if not p:
            continue
        for q in qs:
            text = (q.get("text") or "").strip()
            if not text:
                continue
            rows.append({
                "text": text,
                "subject": p.get("subject"),
                "marks": q.get("marks"),
                "section": q.get("section"),
                "year": p.get("year"),
                "programme": p.get("programme"),
            })
    df = pd.DataFrame(rows, columns=["text", "subject", "marks", "section",
                                     "year", "programme"])
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return len(df)


def run_test(root: str, cache_dir: str) -> None:
    samples = [
        r"3.Third\CBCSS\THEORY OF COMPUTATION 2021.pdf",
        r"3.Third\CBCSS\Data Structures using C++-2015.pdf",
        r"1.Fist\FYUGP\Fundamentals of Computers & Computational Thinking 2024.pdf",
    ]
    for rel in samples:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            print("missing:", rel)
            continue
        res = extract_pdf(path, use_cache=True, cache_dir=cache_dir)
        out = parse_paper(path, rel, res["text"], res["method"])
        p = out["paper"]
        print("=" * 96)
        print("FILE :", rel, " [%s]" % res["method"])
        print("META : %s | sem %s | %s | code %s | %s %s | %s | max %s %s" % (
            p["programme"], p["semester"], p["subject"], p["course_code"],
            MONTH_NAMES.get(p["month"], "?"), p["year"], p["exam_type"],
            p["max_marks"], p["marks_unit"]))
        print("-" * 96)
        for q in out["questions"]:
            print("  [%s] Q%-3s m=%-4s or=%-5s %s" % (
                q["section"], q["number"], q["marks"], q["has_or"],
                q["text"][:88]))
        print("  TOTAL:", len(out["questions"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="BCA question paper pipeline")
    ap.add_argument("--root", default=HERE, help="workspace root folder")
    ap.add_argument("--limit", type=int, default=None, help="limit #PDFs")
    ap.add_argument("--no-ocr", action="store_true", help="skip OCR")
    ap.add_argument("--test", action="store_true", help="preview 3 samples")
    ap.add_argument("--skip-analyze", action="store_true")
    ap.add_argument("--skip-ml", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    out_dir = os.path.join(root, "Organized")
    analysis_dir = os.path.join(root, "analysis")
    ml_dir = os.path.join(root, "ml")
    cache_dir = os.path.join(root, "_cache", "text")
    log_path = os.path.join(root, "errors.log")

    if args.test:
        run_test(root, cache_dir)
        return 0

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    os.makedirs(ml_dir, exist_ok=True)

    pdfs = find_pdfs(root)
    # never process our own outputs / cache
    pdfs = [p for p in pdfs if "_cache" not in p and "Organized" not in p]
    print("Found %d PDFs under %s" % (len(pdfs), root))
    print("Tesseract engine:", find_tesseract() or "NOT FOUND")
    if args.limit:
        pdfs = pdfs[: args.limit]

    log = make_logger(log_path)

    print("\n[1/5] Extracting text%s ..." %
          ("" if not args.no_ocr else " (OCR disabled)"))
    t0 = time.time()
    extracted = run_extract(pdfs, root, cache_dir, ocr=not args.no_ocr,
                            logger=log)
    print("      done in %.1fs" % (time.time() - t0))

    print("\n[2/5] Parsing %d papers ..." % len(extracted))
    parsed = []
    for i, rec in enumerate(extracted, 1):
        try:
            out = parse_paper(rec["path"], rec["rel"], rec["text"],
                              rec["method"])
            parsed.append(out)
        except Exception as exc:
            log(rec["rel"], "parse %s: %s" % (type(exc).__name__, exc))
        sys.stdout.write("\r      parsed [%d/%d] %-55.55s" % (
            i, len(extracted), rec["rel"]))
        sys.stdout.flush()
    sys.stdout.write("\n")

    print("\n[3/5] Organising outputs ...")
    result = organize_mod.organize(parsed, out_dir)
    papers = result["papers"]
    qbp = result["questions_by_paper"]

    total_questions = sum(len(v) for v in qbp.values())
    n_review = sum(1 for p in papers if p.get("needs_review"))
    subjects = sorted({p.get("subject") for p in papers if p.get("subject")})

    if not args.skip_ml:
        print("\n[4/5] Writing ML data ...")
        n = write_train_csv(os.path.join(ml_dir, "train.csv"), papers, qbp)
        print("      train.csv rows: %d" % n)
    else:
        print("\n[4/5] ML export skipped.")

    if not args.skip_analyze:
        print("\n[5/5] Analysing subjects ...")
        import analyze as analyze_mod
        analyze_mod.analyze(papers, qbp, analysis_dir)
    else:
        print("\n[5/5] Analysis skipped.")

    # ---- final report ----
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    print("Papers processed : %d" % len(papers))
    print("Questions        : %d" % total_questions)
    print("Subjects detected: %d" % len(subjects))
    print("Needs review     : %d" % n_review)
    print("Outputs:")
    print("  Organized/  ->", out_dir)
    print("  analysis/   ->", analysis_dir)
    print("  ml/         ->", ml_dir)
    print("  errors.log  ->", log_path)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
