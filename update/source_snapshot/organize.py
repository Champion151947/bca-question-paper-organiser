"""organize.py - Write organised outputs (by_subject, CSVs, JSONL, index)."""
from __future__ import annotations

import csv
import json
import os
import re
import textwrap
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import pandas as pd

from parse import MONTH_NAMES, norm_subject, subject_filename

PAPER_COLUMNS = [
    "paper_id", "programme", "semester", "subject", "subject_raw",
    "header_subject", "course_code", "year", "month", "exam_type",
    "max_marks", "marks_unit", "time", "extract_method", "n_questions",
    "needs_review", "review_notes", "source_file",
]

QUESTION_COLUMNS = [
    "paper_id", "programme", "semester", "subject", "course_code", "year",
    "month", "exam_type", "max_marks", "source_file", "section",
    "question_number", "marks", "has_or", "extract_method", "question_text",
]

_SEP = "=" * 78
_SUB = "-" * 78

# Bump when the built-in merges below change, so subject_map.csv is
# regenerated with the new defaults (hand edits are only preserved for a
# matching version).
SUBJECT_MAP_VERSION = 3

# High-confidence duplicates/typos folded into a canonical subject name.
# Keyed by the normalized subject; edit subject_map.csv for anything else.
SUBJECT_REMAP = {
    "BCA Computer Fundamentals and HTML": "Computer Fundamentals and HTML",
    "BCA Mathematical": "Mathematical Foundations for Computer Applications",
    "Comp Oriented Stat Method":
        "Computer Oriented Numerical and Statistical Methods",
    "Finacial Mgmt Accounting": "Financial and Management Accounting",
    "Financial Management Accounting": "Financial and Management Accounting",
    "Data Structure Usng C": "Data Structures Using C",
    "Principal of Software": "Principles of Software Engineering",
    "Software Testing": "Software Testing and Quality Assurance",
    "Object Oriented": "Object Oriented C++",
    "Web Programming": "Web Programming Using PHP",
    "Micro Processor": "Microprocessors",
    "Database Management System": "Database Management",
    "Computer Organization": "Computer Organization and Architecture",
    "Programming in JAVA": "JAVA Programming",
    "Database Design and RDBMS": "Database Design",
    "Numerical Methods and Optimization Techniques":
        "Numerical Analysis and Optimization Techniques",
    "Website Designing Using Contet Management System":
        "Website Designing Using Content Management System",
}


def sort_papers(papers: list[dict]) -> list[dict]:
    def key(p):
        return (p.get("programme", ""), p.get("subject", ""),
                p.get("year") or 0, p.get("month") or 0, p.get("source", ""))
    return sorted(papers, key=key)


def assign_ids(papers: list[dict]) -> None:
    for i, p in enumerate(papers, 1):
        p["paper_id"] = i


def _stem_key(normalized: str) -> str:
    """Merge key that treats simple plural variants as equal (System/Systems)."""
    toks = []
    for t in re.split(r"[^A-Za-z0-9+#]+", normalized.lower()):
        if not t:
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith(("ss", "is", "us")):
            t = t[:-1]
        toks.append(t)
    return " ".join(toks)


def build_default_subject_map(papers: list[dict]) -> dict:
    raw_norm: dict[str, str] = {}
    raw_papers: Counter = Counter()
    for p in papers:
        raw = p.get("subject_raw") or ""
        if not raw:
            continue
        raw_norm.setdefault(raw, norm_subject(raw))
        raw_papers[raw] += 1

    groups: dict[str, list[str]] = defaultdict(list)
    for raw, norm in raw_norm.items():
        groups[_stem_key(norm)].append(raw)

    mapping: dict[str, str] = {}
    for _key, raws in groups.items():
        raws_sorted = sorted(
            raws, key=lambda r: (-raw_papers[r], len(raw_norm[r]), raw_norm[r]))
        canonical = raw_norm[raws_sorted[0]]
        for raw in raws:
            mapping[raw] = canonical

    for raw, norm in list(mapping.items()):
        mapping[raw] = SUBJECT_REMAP.get(norm, norm)
    return mapping


def load_subject_map(path: str) -> tuple[dict, int | None]:
    """Return (raw->normalized, version). version comes from the header line."""
    if not os.path.isfile(path):
        return {}, None
    version = None
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            for line in fh:
                s = line.strip()
                if s.startswith("#") and "subject_map_version=" in s:
                    m = re.search(r"subject_map_version=(\d+)", s)
                    if m:
                        version = int(m.group(1))
                elif not s.startswith("#"):
                    break
        df = pd.read_csv(path, dtype=str, keep_default_na=False, comment="#")
    except Exception:
        return {}, None
    out = {}
    if "raw_subject" in df.columns and "normalized_subject" in df.columns:
        for _, r in df.iterrows():
            out[str(r["raw_subject"])] = str(r["normalized_subject"])
    return out, version


def write_subject_map(path: str, papers: list[dict], existing: dict,
                      existing_version: int | None) -> dict:
    """Merge default mapping with any user edits and write subject_map.csv.

    Defaults are regenerated whenever the map version changes (e.g. new
    built-in merges); a same-version file is treated as authoritative so
    hand edits survive re-runs.
    """
    default = build_default_subject_map(papers)
    if existing and existing_version == SUBJECT_MAP_VERSION:
        merged = dict(default)
        for raw, norm in existing.items():          # user edits win
            merged[raw] = norm or default.get(raw, norm)
    else:
        merged = dict(default)

    raw_counts: dict[str, int] = {}
    q_counts: dict[str, int] = {}
    for p in papers:
        if not p.get("subject_raw"):
            continue
        raw_counts[p["subject_raw"]] = raw_counts.get(p["subject_raw"], 0) + 1
        q_counts[p["subject_raw"]] = q_counts.get(p["subject_raw"], 0) + \
            int(p.get("n_questions") or 0)

    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# subject_map_version=%d edition; edit to fix mapping." %
                    SUBJECT_MAP_VERSION])
        w.writerow(["raw_subject", "normalized_subject", "n_papers",
                    "n_questions"])
        for raw in sorted(merged, key=lambda r: (merged[r], r)):
            w.writerow([raw, merged[raw], raw_counts.get(raw, 0),
                        q_counts.get(raw, 0)])
    return merged


def write_merge_candidates(path: str, papers: list[dict]) -> None:
    """Report similar-keeping subject pairs for manual review/merging.

    Automatically-merged variants are already resolved in subject_map.csv;
    this file lists remaining pairs that look related but were kept apart,
    so a user can decide whether any should be merged in the map.
    """
    counts = Counter(p.get("subject") or ""
                     for p in papers if p.get("subject"))

    def toks(s: str):
        return set(re.findall(r"[a-z0-9]+", s.lower()))

    names = sorted(counts)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ta, tb = toks(a), toks(b)
            union = ta | tb
            if not union:
                continue
            jac = len(ta & tb) / len(union)
            srat = SequenceMatcher(None, " ".join(sorted(ta)),
                                   " ".join(sorted(tb))).ratio()
            sub = 1 if (ta <= tb or tb <= ta) else 0
            score = max(jac, srat, sub)
            if score < 0.55:
                continue
            rows.append({
                "subject_a": a, "n_papers_a": counts[a],
                "subject_b": b, "n_papers_b": counts[b],
                "similarity": round(score, 3), "one_is_subset_of_other": sub == 1,
            })
    rows.sort(key=lambda r: -r["similarity"])
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def _fmt_month(m) -> str:
    return MONTH_NAMES.get(m, "").capitalize() if m else ""


def _wrap(text: str, width: int = 92, indent: str = "    ") -> str:
    return textwrap.fill(text, width=width,
                         initial_indent=indent, subsequent_indent=indent)


def write_by_subject(out_dir: str, papers: list[dict],
                     questions_by_paper: dict) -> None:
    groups: dict[tuple, list[dict]] = {}
    for p in papers:
        sem = p.get("semester")
        key = (sem, p.get("programme", "CBCSS"), p.get("subject") or "Unknown")
        groups.setdefault(key, []).append(p)

    for (sem, programme, subject), plist in groups.items():
        sem_dir = "%s_Semester" % (sem if sem else "NA")
        fname = "%s.txt" % (subject_filename(subject) or "Unknown")
        sub_dir = os.path.join(out_dir, "by_subject", sem_dir, programme)
        os.makedirs(sub_dir, exist_ok=True)
        fpath = os.path.join(sub_dir, fname)

        plist = sorted(plist, key=lambda p: (p.get("year") or 0,
                                             p.get("month") or 0,
                                             p.get("source", "")))
        lines = []
        lines.append(_SEP)
        lines.append("SUBJECT: %s" % subject)
        lines.append("PROGRAMME: %s      SEMESTER: %s      PAPERS: %d" %
                     (programme, sem if sem else "?", len(plist)))
        lines.append(_SEP)
        lines.append("")

        for p in plist:
            lines.append(_SEP)
            lines.append("YEAR %s  |  %s  |  %s" % (
                p.get("year") or "?", _fmt_month(p.get("month")) or "?",
                p.get("exam_type") or "University"))
            lines.append("Programme: %s    Semester: %s    Course code: %s" % (
                p.get("programme"), p.get("semester"),
                p.get("course_code") or "-"))
            mm = p.get("max_marks")
            lines.append("Maximum: %s %s    Time: %s    Source: %s" % (
                mm if mm is not None else "-", p.get("marks_unit") or "",
                p.get("time") or "-", p.get("source_file")))
            lines.append(_SUB)

            qs = questions_by_paper.get(p["paper_id"], [])
            if not qs:
                lines.append("    (no questions extracted)")
            last_section = None
            for q in qs:
                if q.get("section") and q["section"] != last_section:
                    lines.append("")
                    lines.append("Section %s" % q["section"])
                    last_section = q["section"]
                mk = q.get("marks")
                tag = "[%s mark%s]" % (mk, "" if mk == 1 else "s") \
                    if mk is not None else "[? marks]"
                or_tag = "  (OR choice)" if q.get("has_or") else ""
                lines.append("Q%s. %s%s" % (q["number"], tag, or_tag))
                lines.append(_wrap(q.get("text", "")))
            lines.append("")
            lines.append("")

        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))


def write_questions_csv(path: str, papers: list[dict],
                        questions_by_paper: dict) -> None:
    pmap = {p["paper_id"]: p for p in papers}
    rows = []
    for pid in sorted(questions_by_paper):
        p = pmap.get(pid)
        if not p:
            continue
        for q in questions_by_paper[pid]:
            rows.append({
                "paper_id": pid,
                "programme": p.get("programme"),
                "semester": p.get("semester"),
                "subject": p.get("subject"),
                "course_code": p.get("course_code"),
                "year": p.get("year"),
                "month": _fmt_month(p.get("month")),
                "exam_type": p.get("exam_type"),
                "max_marks": p.get("max_marks"),
                "source_file": p.get("source_file"),
                "section": q.get("section"),
                "question_number": q.get("number"),
                "marks": q.get("marks"),
                "has_or": q.get("has_or"),
                "extract_method": p.get("extract_method"),
                "question_text": q.get("text"),
            })
    df = pd.DataFrame(rows, columns=QUESTION_COLUMNS)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_papers_index(path: str, papers: list[dict]) -> None:
    rows = []
    for p in papers:
        rows.append({
            "paper_id": p["paper_id"],
            "programme": p.get("programme"),
            "semester": p.get("semester"),
            "subject": p.get("subject"),
            "subject_raw": p.get("subject_raw"),
            "header_subject": p.get("header_subject"),
            "course_code": p.get("course_code"),
            "year": p.get("year"),
            "month": _fmt_month(p.get("month")),
            "exam_type": p.get("exam_type"),
            "max_marks": p.get("max_marks"),
            "marks_unit": p.get("marks_unit"),
            "time": p.get("time"),
            "extract_method": p.get("extract_method"),
            "n_questions": p.get("n_questions"),
            "needs_review": p.get("needs_review"),
            "review_notes": p.get("review_notes"),
            "source_file": p.get("source_file"),
        })
    df = pd.DataFrame(rows, columns=PAPER_COLUMNS)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_dataset_jsonl(path: str, papers: list[dict],
                        questions_by_paper: dict) -> None:
    pmap = {p["paper_id"]: p for p in papers}
    with open(path, "w", encoding="utf-8") as fh:
        for pid in sorted(questions_by_paper):
            p = pmap.get(pid)
            if not p:
                continue
            for q in questions_by_paper[pid]:
                rec = {
                    "text": q.get("text"),
                    "subject": p.get("subject"),
                    "programme": p.get("programme"),
                    "semester": p.get("semester"),
                    "marks": q.get("marks"),
                    "section": q.get("section"),
                    "question_number": q.get("number"),
                    "year": p.get("year"),
                    "month": _fmt_month(p.get("month")),
                    "exam_type": p.get("exam_type"),
                    "course_code": p.get("course_code"),
                    "has_or": q.get("has_or"),
                    "source_file": p.get("source_file"),
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_needs_review(path: str, papers: list[dict]) -> None:
    flagged = [p for p in papers if p.get("needs_review")]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("Papers needing review: %d of %d\n" % (len(flagged), len(papers)))
        fh.write(_SEP + "\n\n")
        for p in sorted(flagged, key=lambda x: x.get("source", "")):
            fh.write("SOURCE : %s\n" % p.get("source"))
            fh.write("  subject=%s  semester=%s  year=%s  exam=%s  "
                     "questions=%s  method=%s\n" % (
                         p.get("subject"), p.get("semester"), p.get("year"),
                         p.get("exam_type"), p.get("n_questions"),
                         p.get("extract_method")))
            fh.write("  reasons: %s\n\n" % p.get("review_notes"))


def build_questions_by_paper(parsed: list[dict]) -> tuple[list[dict], dict]:
    papers = [p["paper"] for p in parsed]
    papers = sort_papers(papers)
    assign_ids(papers)
    # map old paper object to id by source
    by_source = {p["source"]: p["paper_id"] for p in papers}
    qbp = {}
    for p in parsed:
        src = p["paper"]["source"]
        pid = by_source.get(src)
        if pid is None:
            continue
        qbp[pid] = p["questions"]
    return papers, qbp


def organize(parsed: list[dict], out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    papers, qbp = build_questions_by_paper(parsed)

    map_path = os.path.join(out_dir, "subject_map.csv")
    existing, existing_version = load_subject_map(map_path)
    mapping = write_subject_map(map_path, papers, existing, existing_version)

    # apply (possibly user-edited) mapping
    for p in papers:
        raw = p.get("subject_raw") or ""
        if raw in mapping and mapping[raw]:
            p["subject"] = mapping[raw]
        else:
            p["subject"] = norm_subject(raw)
    for pid, qs in qbp.items():
        pass

    write_by_subject(out_dir, papers, qbp)
    write_merge_candidates(os.path.join(out_dir,
                                        "subject_merge_candidates.csv"),
                           papers)
    write_questions_csv(os.path.join(out_dir, "questions.csv"), papers, qbp)
    write_papers_index(os.path.join(out_dir, "papers_index.csv"), papers)
    write_dataset_jsonl(os.path.join(out_dir, "dataset.jsonl"), papers, qbp)
    write_needs_review(os.path.join(out_dir, "needs_review.txt"), papers)

    return {"papers": papers, "questions_by_paper": qbp, "mapping": mapping}
