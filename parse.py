"""parse.py - Parse header metadata and split papers into questions."""
from __future__ import annotations

import os
import re

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
MONTH_NAMES = {v: k for k, v in MONTHS.items()}

SEMESTER_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8,
}

ACRONYMS = {
    "bca", "bcs", "ba", "bsc", "ca", "html", "php", "c", "java", "rdbms",
    "dbms", "sql", "xml", "uml", "css", "js", "ai", "os", "api", "sdk", "jdk",
    "mvc", "www", "iot", "gui", "cli", "url", "http", "json", "erp", "cad",
    "c++", "asp", "cms", "ads", "dccn", "oop", "oopc",
}

# Words kept lowercase in the middle of a normalised subject name.
SMALL_WORDS = {
    "of", "and", "for", "the", "in", "on", "to", "with", "a", "an", "at",
    "by", "from", "into", "over", "under", "or", "as", "vs",
}

EXAM_TYPES = [
    ("supplementary", "Supplementary"),
    ("improvement", "Improvement"),
    ("christmas", "Christmas"),
    ("onam", "Onam"),
    ("model", "Model"),
    ("internal", "Internal"),
    ("regular", "University"),
]

_SUBJECT_NORM_SPECIAL = {
    "&": " and ",
}


def normalize_text(text: str) -> str:
    """Normalise unicode, whitespace; keep line structure."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    repl = {
        "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2018": "'",
        "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u00ad": "",
        "\ufb01": "fi", "\ufb02": "fl", "\u00a0": " ", "\u200b": "",
        "\u2022": " ", "\t": " ",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    lines = [re.sub(r"[ ]{2,}", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Header / metadata
# ---------------------------------------------------------------------------

def programme_from_path(rel: str) -> str:
    upper = rel.upper().replace("\\", "/")
    if "FYUGP" in upper:
        return "FYUGP"
    return "CBCSS"


def semester_from_path(rel: str) -> int | None:
    parts = re.split(r"[\\/]+", rel)
    dirs = parts[:-1] if len(parts) > 1 else parts
    for p in dirs:
        m = re.match(r"\s*([1-8])[\.\s]", p)
        if m:
            return int(m.group(1))
    for p in dirs:
        low = p.lower()
        for word, n in SEMESTER_WORDS.items():
            if word in low:
                return n
    return None


def semester_from_header(text: str) -> int | None:
    m = re.search(
        r"\b(" + "|".join(SEMESTER_WORDS) + r")\s+semester\b", text, re.I)
    if m:
        return SEMESTER_WORDS[m.group(1).lower()]
    return None


_EXAM_CUT = re.compile(
    r"(?i)\b(?:answer\s+(?:all|any|at\s*least|atleast|the)|"
    r"(?:section|part)\s+[a-d]\b)")


def detect_exam_type(text: str, rel: str) -> str:
    # Trim everything from the first "Answer all/any ..." or Section/Part A
    # marker onward, so words inside questions ("OSI model", "internal CSS",
    # "process improvement") are not mistaken for the exam type.
    m = _EXAM_CUT.search(text)
    header = text[: m.start()] if m else text[:1200]
    hay = (os.path.basename(rel) + "\n" + header).upper()
    for key, label in EXAM_TYPES:
        if re.search(r"\b" + key.upper() + r"\b", hay):
            return label
    return "University"


def parse_header(text: str, rel: str) -> dict:
    """Extract paper-level metadata from the text of a paper."""
    method = "header"
    head = text[:2500]
    upper = head.upper()

    # Year + month
    year = None
    month = None
    m = re.search(
        r"\b(" + "|".join(MONTHS) + r")\s*,?\s*((?:19|20)\d{2})\b",
        text, re.I)
    if m:
        month = MONTHS[m.group(1).lower()]
        year = int(m.group(2))
    else:
        m = re.search(r"\b(?:19|20)\d{2}\b", text)
        if m:
            year = int(m.group(0))
    if year is None:
        years = re.findall(r"\b((?:19|20)\d{2})\b", os.path.basename(rel))
        if years:
            year = int(years[-1])

    # Semester
    semester = semester_from_path(rel)
    if semester is None:
        semester = semester_from_header(text)

    # Course code + subject from header line  "CODE-SUBJECT"
    course_code = None
    header_subject = None
    mcode = re.search(
        r"([A-Z]{2,6}(?:\s*/\s*[A-Z]{2,6})?\s*\d{1,2}[A-Z]{0,3}\s*\d{2,3}"
        r"\s*(?:\([A-Z]\))?)\s*[-\u2013\u2014:]\s*"
        r"([A-Z][A-Z0-9 ,\.\-\&\'\+\(\)/]{3,90})", upper)
    if mcode:
        course_code = re.sub(r"\s+", " ", mcode.group(1)).strip()
        header_subject = mcode.group(2).strip()

    # Maximum marks
    max_marks = None
    marks_unit = "Marks"
    mmk = re.search(r"maximum\s*[:\.]?\s*([0-9]{1,3})\s*([a-zA-Z]*)", text, re.I)
    if mmk:
        max_marks = int(mmk.group(1))
        unit = (mmk.group(2) or "").strip().lower()
        marks_unit = "Weightage" if "weight" in unit else "Marks"

    # Time
    time_str = None
    mt = re.search(r"time\s*[:\.]?\s*([A-Za-z][A-Za-z ]{2,20}?hour[s]?)", text, re.I)
    if mt:
        time_str = re.sub(r"\s+", " ", mt.group(1)).strip()

    exam_type = detect_exam_type(text, rel)

    return {
        "programme": programme_from_path(rel),
        "semester": semester,
        "course_code": course_code,
        "header_subject": header_subject,
        "year": year,
        "month": month,
        "exam_type": exam_type,
        "max_marks": max_marks,
        "marks_unit": marks_unit,
        "time": time_str,
        "method": method,
    }


# ---------------------------------------------------------------------------
# Subject naming
# ---------------------------------------------------------------------------

def raw_subject_from_filename(path: str) -> str:
    name = os.path.basename(path)
    name = re.sub(r"\.pdf$", "", name, flags=re.I)
    name = re.sub(r"\.pdf$", "", name, flags=re.I)
    name = re.sub(r"\([^)]*\)", " ", name)          # (2017 admission) etc.
    name = re.sub(r"\b(?:19|20)\d{2}\b", " ", name)  # years
    name = re.sub(r"(?i)\b(adm|admission|admn)\b", " ", name)
    name = name.replace("_", " ").replace("-", " ").replace(".", " ")
    name = re.sub(r"\s+", " ", name).strip(" -_.")
    return name or os.path.splitext(os.path.basename(path))[0]


def norm_subject(raw: str) -> str:
    if not raw:
        return ""
    s = raw
    s = s.replace("&", " and ")
    s = re.sub(r"[^A-Za-z0-9+#]+", " ", s)
    tokens = s.split()
    out = []
    for idx, tok in enumerate(tokens):
        low = tok.lower()
        if low == "c++":
            out.append("C++")
        elif low in ACRONYMS:
            out.append(low.upper())
        elif idx > 0 and low in SMALL_WORDS:
            out.append(low)
        else:
            out.append(tok.capitalize())
    return " ".join(out).strip()


def subject_filename(normalized: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "-", normalized).strip()


# ---------------------------------------------------------------------------
# Question splitting
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(
    r"^\s*(?:section|part)\s*[-\u2013\u2014:\.]?\s*([A-Da-d])\b(.*)$", re.I)
ROMAN_RE = re.compile(r"^\s*(V?I{0,3}|IV)\s*[\.\)]\s*(.*)$", re.I)
ROMAN_MAP = {"I": "A", "II": "B", "III": "C", "IV": "D", "V": "E"}


_SECTION_TAIL = re.compile(
    r"(?:section|part)\s*[-\u2013\u2014:\.]?\s*([A-Da-d])\s*$", re.I)
_SECTION_ROMAN_TAIL = re.compile(r"(?:section|part)\s+([IVXivx]+)\s*$", re.I)


def section_letter_from_header(line: str) -> str | None:
    s = line.strip()
    m = SECTION_RE.match(s)
    if m:
        return m.group(1).upper()
    # Junk-prefixed section markers such as "He). Part B" or ". Part C".
    # Only when the marker ends the line and the line is not itself a question.
    if len(s) < 40 and not re.match(r"^\d", s):
        m = _SECTION_TAIL.search(s)
        if m:
            return m.group(1).upper()
        m = _SECTION_ROMAN_TAIL.search(s)
        if m:
            return ROMAN_MAP.get(m.group(1).upper())
    if len(s) < 70:
        m = ROMAN_RE.match(s)
        if m and re.search(
                r"(?i)\b(answer|question|essay|short|long|paragraph|type)\b",
                s):
            return ROMAN_MAP.get(m.group(1).upper())
    return None


_DOC_CODE = re.compile(r"^[A-Z]\s*\d{3,}\b")

_INSTRUCTION_RE = re.compile(
    r"(?i)^(answer\s+(?:all|any|attempt|at ?least|the\s+following)"
    r"|each\s+(?:question|correct)|attempt\s+(?:all|any)"
    r"|write\s+short\s+answers?)")


def match_qnum(line: str):
    s = line.strip()
    # Drop stray layout junk (pipes, bullets, dashes) printed before the number.
    s = re.sub(r"^[^A-Za-z0-9(]+", "", s)
    m = re.match(r"^\(?(\d{1,2})\s*[\.\)]\s*(.*)$", s)
    if m:
        return int(m.group(1)), m.group(2).strip()
    m = re.match(r"^\(?(\d{1,2})\)?$", s)
    if m:
        return int(m.group(1)), ""
    # Old scanned papers: "1 ISP stands for" (no dot after the number).
    m = re.match(r"^\(?(\d{1,2})\s+([A-Z(\-<\"'\u2018\u2019\u201c].*)$", s)
    if m:
        rest = m.group(2).strip()
        if not _DOC_CODE.match(rest) and not re.match(r"^[A-Z]\s*\d", rest):
            return int(m.group(1)), rest
    # OCR of option-style items: "2 a we ectangles." (letter lost its parens).
    m = re.match(r"^\(?(\d{1,2})\)?\s+([a-d])[\.\)]?\s+(.*)$", s, re.I)
    if m:
        return int(m.group(1)), ("%s %s" % (m.group(2), m.group(3))).strip()
    return None


_MARKS_FORMULA = re.compile(
    r"\(\s*(\d{1,2})\s*[x×]\s*(\d{1,2})\s*=\s*\d*\s*(?:marks?|weightage)?\s*\)",
    re.I)


def _marks_from_formula(line: str) -> int | None:
    m = _MARKS_FORMULA.search(line)
    if m:
        return int(m.group(2))
    return None


def lookahead_marks(lines: list[str], idx: int) -> int | None:
    """Look ahead after a section header for 'each question carries N marks'."""
    for ln in lines[idx + 1: idx + 9]:
        m = re.search(
            r"(?:each\s+(?:question|correct\s+answer|answer))\s*"
            r"(?:carries\s+)?(?:a\s+maximum\s+of\s+)?(\d{1,2})"
            r"\s*(?:marks?|weightage)", ln, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"carries\s+(?:a\s+maximum\s+of\s+)?(\d{1,2})\s*marks?",
                      ln, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"\(?\s*(\d{1,2})\s*marks?\s+each", ln, re.I)
        if m:
            return int(m.group(1))
        f = _marks_from_formula(ln)
        if f:
            return f
    return None


def is_boilerplate(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if re.fullmatch(r"[\d\s\.\-]+", s):        # page numbers / serial numbers
        return True
    if re.fullmatch(r"D\s*\d{4,}", s, re.I):
        return True
    if re.fullmatch(r"\d{0,3}\s*[\.\-]?\s*D\s*\d{4,}", s, re.I):
        return True
    if re.match(r"^(turn over|name\s*\.{2,}|name\s*:|reg\.?\s*no|pages?\s*:|"
                r"ceiling|overall ceiling)", s, re.I):
        return True
    if re.match(r"^(answer\b.*questions?|all questions|all questions can be|"
                r"each question|each correct answer|the question carries|"
                r"section\s+[a-d]\b|part\s+[a-d]\b|time\s*:|maximum\s*:)", s, re.I):
        return True
    if _MARKS_FORMULA.fullmatch(s):
        return True
    if re.fullmatch(r"\(?\s*\d+\s*(?:x|×)\s*\d+\s*(?:marks?)?\s*\)?", s, re.I):
        return True
    if re.match(r"^(answer\s+(?:all|any|atleast|atleast|at least)\b.*)$", s, re.I):
        return True
    return False


def _is_or_line(line: str) -> bool:
    return bool(re.fullmatch(r"\(?\s*or\s*\)?[\.:]?", line.strip(), re.I))


def split_questions(text: str, fuzzy: bool = False) -> list[dict]:
    """Split normalised paper text into individual questions.

    ``fuzzy`` allows the question counter to skip one or two numbers, which
    recovers questions from imperfect OCR where a number is dropped. Text
    papers have clean numbering, so it stays off to avoid false splits caused
    by matrix cells / equation fragments split onto their own lines.
    """
    lines = normalize_text(text).split("\n")
    questions: list[dict] = []
    cur = None
    cur_section = None
    last_q_section = None
    cur_marks = None
    expected = None

    # Stray serial/page numbers ("18)", "22 .") are sometimes printed just
    # before the instructions. Accepting one as the first question poisons
    # `expected` and then every real question is rejected, so ignore anything
    # before the first section/instruction marker in the opening block.
    start = 0
    for i, ln in enumerate(lines[:30]):
        if section_letter_from_header(ln) or _INSTRUCTION_RE.match(ln.strip()):
            start = i
            break

    def flush():
        nonlocal cur
        if cur is None:
            return
        qtext = " ".join(t for t in cur["text_lines"] if t).strip()
        qtext = re.sub(r"\s{2,}", " ", qtext).strip(" .;:-")
        marks = cur["marks"]
        if marks is None:
            marks = cur.get("_formula_marks")
        cur["text"] = qtext
        cur["marks"] = marks
        if qtext:
            questions.append(cur)
        cur = None

    for i, line in enumerate(lines):
        if i < start:
            continue
        letter = section_letter_from_header(line)
        if letter:
            cur_section = letter
            cur_marks = lookahead_marks(lines, i)
            expected = None
            continue

        qm = match_qnum(line)
        accept = False
        if qm is not None:
            num, rest = qm
            if expected is None:
                # A bare serial/page artefact ("22 .") that opens the paper
                # would poison `expected`. Only distrust such numbers before
                # any question has been accepted - after a section header a
                # bare "13." is a perfectly real question.
                stray = (not questions and cur is None and num > 3
                         and not re.search(r"[A-Za-z]", rest))
                if not stray:
                    accept = True
            elif num == expected:
                accept = True
            elif fuzzy and expected < num <= expected + 2:
                accept = True  # tolerate one or two OCR-dropped numbers
            elif num == 1 and expected > 3 and cur_section != last_q_section:
                accept = True  # numbering restarts in a new part/section
        if accept:
            flush()
            cur = {"number": num, "section": cur_section, "marks": cur_marks,
                   "text_lines": [rest] if rest else [], "has_or": False,
                   "_formula_marks": None}
            expected = num + 1
            last_q_section = cur_section
            continue

        if cur is not None:
            if _is_or_line(line):
                cur["has_or"] = True
            elif is_boilerplate(line):
                continue
            else:
                fm = _marks_from_formula(line)
                if fm and cur.get("_formula_marks") is None:
                    cur["_formula_marks"] = fm
                    continue
                cur["text_lines"].append(line)

    flush()
    return questions


def parse_paper(path: str, rel: str, text: str, extract_method: str) -> dict:
    """Combine header + questions into a paper record."""
    header = parse_header(text, rel)
    questions = split_questions(text, fuzzy=(extract_method == "ocr"))
    raw_subject = raw_subject_from_filename(path)
    header_subject = header.get("header_subject")
    if not raw_subject and header_subject:
        raw_subject = header_subject
    normalized = norm_subject(raw_subject)

    notes = []
    if extract_method in ("error", "no_text", "no_tesseract", "ocr_empty"):
        notes.append("extract=%s" % extract_method)
    if header["year"] is None:
        notes.append("no year")
    if header["semester"] is None:
        notes.append("no semester")
    if not normalized:
        notes.append("no subject")
    if not questions:
        notes.append("no questions")
    else:
        # A long question only suggests an OCR merge on scanned papers;
        # text papers legitimately contain long essay questions.
        long_threshold = 500 if extract_method == "ocr" else 1500
        long_q = sum(1 for q in questions
                     if len(q.get("text", "")) > long_threshold)
        if long_q and extract_method == "ocr":
            notes.append("%d over-long question(s) - possible OCR merge" %
                         long_q)
        maxnum = max(q["number"] for q in questions)
        missing = maxnum - len(questions)
        if missing >= 3:
            notes.append("%d possible missed question(s) up to Q%d" %
                         (missing, maxnum))

    paper = {
        "source": rel,
        "source_file": rel,
        "programme": header["programme"],
        "semester": header["semester"],
        "subject": normalized,
        "subject_raw": raw_subject,
        "header_subject": header_subject,
        "course_code": header["course_code"],
        "year": header["year"],
        "month": header["month"],
        "exam_type": header["exam_type"],
        "max_marks": header["max_marks"],
        "marks_unit": header["marks_unit"],
        "time": header["time"],
        "extract_method": extract_method,
        "n_questions": len(questions),
        "needs_review": bool(notes),
        "review_notes": "; ".join(notes),
    }
    return {"paper": paper, "questions": questions}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    from extract import extract_pdf
    for rel in sys.argv[1:]:
        res = extract_pdf(rel, use_cache=False)
        out = parse_paper(rel, rel, res["text"], res["method"])
        print(out["paper"])
        for q in out["questions"]:
            print("  ", q["section"], q["number"], q["marks"], q["text"][:70])
