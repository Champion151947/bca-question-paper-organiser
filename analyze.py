"""analyze.py - Per-subject analysis and overall summary."""
from __future__ import annotations

import os
import re
import textwrap
from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parse import subject_filename

SIM_THRESHOLD = 0.75

EXTRA_STOPWORDS = {
    "answer", "question", "questions", "explain", "define", "discuss",
    "describe", "write", "short", "note", "notes", "example", "examples",
    "using", "use", "used", "various", "different", "types", "type", "give",
    "state", "list", "what", "why", "how", "with", "following", "also",
    "briefly", "detail", "details", "suitable", "brief", "illustrate",
    "marks", "mark", "carries", "ceiling", "section", "part", "unit",
    "meaning", "term", "terms", "concept", "concepts", "define", "two",
    "one", "any", "all", "each", "may", "can", "shall", "would", "could",
    "does", "differentiate", "difference", "compare", "contrast", "about",
    "mention", "their", "there", "these", "those", "into", "from", "when",
    "which", "where", "while", "been", "being", "have", "has", "had", "not",
    "are", "was", "were", "will", "your", "you", "its", "it", "and", "the",
    "for", "that", "this", "with", "without", "based",
}
STOPWORDS = set(ENGLISH_STOP_WORDS) | EXTRA_STOPWORDS


def _tokenize(text: str) -> list[str]:
    toks = re.findall(r"[A-Za-z][A-Za-z\+\#]{2,}", text.lower())
    return [t.strip("+#") for t in toks if t not in STOPWORDS and len(t) > 2]


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def cluster_questions(texts: list[str], threshold: float = SIM_THRESHOLD):
    """Return list of clusters (lists of indices) with >=2 near-duplicates."""
    n = len(texts)
    if n < 2:
        return []
    vec = TfidfVectorizer(stop_words=list(STOPWORDS), ngram_range=(1, 1),
                          sublinear_tf=True)
    try:
        X = vec.fit_transform(texts)
    except ValueError:
        return []
    sim = cosine_similarity(X)
    uf = UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= threshold:
                uf.union(i, j)
    groups = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    clusters = [g for g in groups.values() if len(g) >= 2]
    clusters.sort(key=len, reverse=True)
    return clusters


def _wrap(text, width=96, indent="    "):
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)


def _subject_records(papers, qbp):
    """subject -> list of dicts {text, year, month, marks, section, source}."""
    pmap = {p["paper_id"]: p for p in papers}
    recs = defaultdict(list)
    for pid, qs in qbp.items():
        p = pmap.get(pid)
        if not p:
            continue
        subj = p.get("subject") or "Unknown"
        for q in qs:
            recs[subj].append({
                "text": (q.get("text") or "").strip(),
                "year": p.get("year"),
                "marks": q.get("marks"),
                "section": q.get("section"),
                "has_or": q.get("has_or"),
                "source": p.get("source_file"),
                "programme": p.get("programme"),
            })
    return recs


def analyse_subject(subject, recs, dirpath) -> dict:
    recs = [r for r in recs if r["text"]]
    texts = [r["text"] for r in recs]
    papers = sorted({(r["programme"], r["source"]) for r in recs})
    years = sorted({r["year"] for r in recs if r["year"]})
    lines = []
    lines.append("# %s - Question Paper Analysis" % subject)
    lines.append("")
    lines.append("- Papers found: **%d**" % len(papers))
    lines.append("- Questions extracted: **%d**" % len(recs))
    lines.append("- Years covered: %s" % (
        ", ".join(str(y) for y in years) if years else "unknown"))
    progs = sorted({r["programme"] for r in recs if r["programme"]})
    lines.append("- Programmes: %s" % (", ".join(progs) or "unknown"))
    lines.append("")

    # ---- Repeated questions ----
    clusters = cluster_questions(texts)
    lines.append("## Most repeated questions (TF-IDF cosine >= %.2f)" %
                 SIM_THRESHOLD)
    lines.append("")
    if not clusters:
        lines.append("_No near-duplicate question groups found above the "
                     "threshold._")
    else:
        for k, grp in enumerate(clusters, 1):
            years_g = sorted({recs[i]["year"] for i in grp if recs[i]["year"]})
            lines.append("**Group %d - repeated %d time(s)** (years: %s)" % (
                k, len(grp), ", ".join(str(y) for y in years_g) or "?"))
            lines.append(_wrap(recs[grp[0]]["text"]))
            if len(grp) > 1:
                lines.append("    Variants:")
                for i in grp[1:6]:
                    lines.append("      - (%s) %s" % (
                        recs[i]["year"] or "?", recs[i]["text"][:110]))
            lines.append("")

    # ---- Keywords by marks ----
    lines.append("## Top topics / keywords by marks")
    lines.append("")
    by_marks = defaultdict(list)
    for r in recs:
        mk = r["marks"]
        if mk is None:
            by_marks["unknown"].append(r["text"])
        else:
            by_marks[mk].append(r["text"])
    def sort_key(k):
        return (0, k) if isinstance(k, int) else (1, str(k))
    for mk in sorted(by_marks, key=sort_key):
        cnt: Counter = Counter()
        for t in by_marks[mk]:
            cnt.update(set(_tokenize(t)))
        top = cnt.most_common(12)
        label = "%s-mark" % mk if isinstance(mk, int) else "unknown-mark"
        lines.append("### %s questions (%d questions)" % (label, len(by_marks[mk])))
        if top:
            lines.append(", ".join("%s (%d)" % (w, c) for w, c in top))
        else:
            lines.append("_none_")
        lines.append("")

    # ---- Most likely important questions ----
    lines.append("## Most likely important questions (repeated 3+ times)")
    lines.append("")
    important = [c for c in clusters if len(c) >= 3]
    if important:
        for k, grp in enumerate(important, 1):
            years_g = sorted({recs[i]["year"] for i in grp if recs[i]["year"]})
            lines.append("%d. (%d times, years %s) %s" % (
                k, len(grp), ", ".join(str(y) for y in years_g) or "?",
                recs[grp[0]]["text"]))
    else:
        lines.append("_No question repeated 3 or more times._")
    lines.append("")

    # ---- Units / topics most asked ----
    overall = Counter()
    for t in texts:
        overall.update(set(_tokenize(t)))
    lines.append("## Units / topics asked most")
    lines.append("")
    lines.append(", ".join("%s (%d)" % (w, c) for w, c in overall.most_common(25)))
    lines.append("")

    out = os.path.join(dirpath, "%s_analysis.md" % subject_filename(subject))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return {
        "subject": subject,
        "papers": len(papers),
        "questions": len(recs),
        "years": years,
        "clusters": len(clusters),
        "important": len(important),
        "top_topics": overall.most_common(8),
    }


def write_overall_summary(summaries: list[dict], dirpath: str) -> None:
    lines = ["# Overall Summary - BCA Question Papers", ""]
    tc = sum(s["questions"] for s in summaries)
    tp = sum(s["papers"] for s in summaries)
    lines.append("- Subjects analysed: **%d**" % len(summaries))
    lines.append("- Total papers: **%d**" % tp)
    lines.append("- Total questions: **%d**" % tc)
    lines.append("")
    lines.append("| Subject | Papers | Questions | Years | Repeated groups | "
                 "Groups 3+ | Top topics |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in sorted(summaries, key=lambda x: -x["questions"]):
        yrs = "%s-%s" % (s["years"][0], s["years"][-1]) if s["years"] else "?"
        topics = ", ".join(w for w, _ in s["top_topics"][:5])
        lines.append("| %s | %d | %d | %s | %d | %d | %s |" % (
            s["subject"], s["papers"], s["questions"], yrs,
            s["clusters"], s["important"], topics))
    lines.append("")
    with open(os.path.join(dirpath, "overall_summary.md"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def analyze(papers, qbp, out_dir: str) -> list[dict]:
    dirpath = out_dir
    os.makedirs(dirpath, exist_ok=True)
    recs_by_subject = _subject_records(papers, qbp)
    summaries = []
    total = len(recs_by_subject)
    for i, (subject, recs) in enumerate(sorted(recs_by_subject.items()), 1):
        print("  analysing [%d/%d] %s" % (i, total, subject))
        summaries.append(analyse_subject(subject, recs, dirpath))
    write_overall_summary(summaries, dirpath)
    return summaries
