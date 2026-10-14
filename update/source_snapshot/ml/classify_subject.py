"""classify_subject.py - Baseline TF-IDF + Logistic Regression subject classifier.

Run:  python classify_subject.py
Reads ml/train.csv (text, subject, marks, section, year, programme),
prints accuracy and a classification report, and saves the model to
ml/subject_model.joblib.
"""
from __future__ import annotations

import os
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_CSV = os.path.join(HERE, "train.csv")
MODEL_PATH = os.path.join(HERE, "subject_model.joblib")


def main() -> int:
    if not os.path.isfile(TRAIN_CSV):
        print("train.csv not found at %s" % TRAIN_CSV)
        print("Run 'python main.py' first to generate it.")
        return 1

    df = pd.read_csv(TRAIN_CSV, keep_default_na=False)
    df = df[df["text"].astype(str).str.strip().str.len() > 0]
    df = df[df["subject"].astype(str).str.strip().str.len() > 0]
    if df.empty:
        print("No usable rows in train.csv")
        return 1

    print("Loaded %d questions across %d subjects" %
          (len(df), df["subject"].nunique()))
    if df["subject"].nunique() < 2:
        print("Need at least 2 subjects to train a classifier.")
        return 1

    X = df["text"].astype(str).tolist()
    y = df["subject"].astype(str).tolist()

    counts = pd.Series(y).value_counts()
    stratify = y if counts.min() >= 2 and len(df) >= 10 else None
    test_size = 0.2 if len(df) >= 10 else 0.34
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify)

    model = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                  sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(max_iter=2000, C=5.0,
                                   class_weight="balanced")),
    ])
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print("\nTest accuracy: %.4f" % acc)
    print("\nClassification report:\n")
    print(classification_report(y_test, pred, zero_division=0))

    joblib.dump(model, MODEL_PATH)
    print("Saved model to %s" % MODEL_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
