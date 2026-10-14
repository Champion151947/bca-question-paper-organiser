"""similar_questions.py - Find the 5 most similar past questions.

Run:  python similar_questions.py
Type a question and it returns the most similar past questions with their
year and subject. Type 'quit' to exit.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_CSV = os.path.join(HERE, "train.csv")


def load():
    if not os.path.isfile(TRAIN_CSV):
        print("train.csv not found at %s" % TRAIN_CSV)
        print("Run 'python main.py' first to generate it.")
        sys.exit(1)
    df = pd.read_csv(TRAIN_CSV, keep_default_na=False)
    df = df[df["text"].astype(str).str.strip().str.len() > 0].reset_index(drop=True)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                          sublinear_tf=True, min_df=1)
    matrix = vec.fit_transform(df["text"].astype(str))
    return df, vec, matrix


def find_similar(query, df, vec, matrix, k=5):
    qv = vec.transform([query])
    sims = cosine_similarity(qv, matrix).ravel()
    idx = np.argsort(-sims)[:k]
    out = []
    for i in idx:
        row = df.iloc[int(i)]
        out.append({
            "score": float(sims[i]),
            "text": row["text"],
            "year": row.get("year", ""),
            "subject": row.get("subject", ""),
            "section": row.get("section", ""),
            "marks": row.get("marks", ""),
        })
    return out


def main() -> int:
    df, vec, matrix = load()
    print("Loaded %d past questions. Type a question (or 'quit')." % len(df))
    while True:
        try:
            q = input("\nQuestion> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q or q.lower() in ("quit", "exit", "q"):
            break
        print("\nTop %d similar past questions:" % 5)
        for rank, r in enumerate(find_similar(q, df, vec, matrix, 5), 1):
            print("  %d. (score %.2f) [%s | %s | %s marks] %s" % (
                rank, r["score"], r["year"] or "?", r["subject"] or "?",
                r["marks"] if r["marks"] != "" else "?", r["text"][:110]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
