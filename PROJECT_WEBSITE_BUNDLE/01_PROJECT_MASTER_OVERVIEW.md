# 📘 Calicut University BCA Question Paper Pipeline — Master Project Documentation

This document provides a comprehensive, end-to-end breakdown of the entire BCA Question Paper dataset, pipeline architecture, extraction results, syllabus mapping, and analytics.

---

## 1. Project Background

The goal of this project is to organize, process, and analyze past Calicut University Bachelor of Computer Applications (BCA) question papers covering **Semester 1 to Semester 6** across both the traditional **CBCSS (2014, 2017, 2019 schemes)** and the newly introduced **FYUGP (2024 scheme)**.

### Core Metrics:
* **Total Question Paper PDFs Processed:** **304** (100% of all files)
* **Total Questions Extracted:** **7,784**
* **Total Subjects Analyzed:** **48**
* **Examination Year Span:** **2014 to 2026**
* **Extracted Text Layer Papers:** 141
* **Scanned OCR Papers Processed:** 163 (via Tesseract OCR PSM 4 & 6 with column alignment)
* **Tofu / Corrupted Character Fixes:** 1,280 SymbolMT Private Use Area glyphs restored to clean Unicode brackets and mathematical symbols.

---

## 2. Directory Layout & Pipeline Components

```
drive-download-20261009T175137Z-1-001/
├── 1.Fist/                      Semester 1 Question Papers (53 files: 43 CBCSS, 10 FYUGP)
├── 2.Second/                    Semester 2 Question Papers (58 files: 50 CBCSS, 8 FYUGP)
├── 3.Third/                     Semester 3 Question Papers (44 files: 39 CBCSS, 5 FYUGP)
├── 4.Fourth/                    Semester 4 Question Papers (41 files: 36 CBCSS, 5 FYUGP)
├── 5.Fifth/                     Semester 5 Question Papers (55 files: 55 CBCSS, 0 FYUGP)
├── 6.Sixth/                     Semester 6 Question Papers (53 files: 53 CBCSS, 0 FYUGP)
│
├── Organized/                   Main Organized Data Outputs
│   ├── papers_index.csv         Index of all 304 papers (semester, subject, year, code, marks)
│   ├── questions.csv            Master questions table (7,784 rows with marks, section, text)
│   ├── dataset.jsonl            ML-ready line-delimited JSON of all questions
│   ├── subject_map.csv          Curated mapping of raw subject strings to standardized names
│   ├── needs_review.txt         List of 31 hard OCR scans flagged for potential review
│   └── by_subject/              Directory tree organized by Semester/Programme/Subject.txt
│
├── analysis/                    Subject-by-subject TF-IDF analyses & repeated question groupings
│   ├── <Subject>_analysis.md    48 individual subject reports
│   └── overall_summary.md       Consolidated summary table
│
├── PROJECT_WEBSITE_BUNDLE/      Folder created for building the Web Application
│   ├── 00_CLAUDE_PROMPT_COPY_PASTE.md    Copy-paste master prompt for Claude
│   ├── 01_PROJECT_MASTER_OVERVIEW.md     This comprehensive reference document
│   ├── 02_ALL_SUBJECTS_REPEATED_TOPICS.md Complete catalog of repeated questions
│   ├── 03_WEBSITE_UI_UX_SPECIFICATION.md UI/UX design specifications
│   └── 04_website_data.json              Pre-aggregated website frontend JSON dataset
│
├── extract.py                   PyMuPDF extraction, Tesseract OCR fallback, PUA character fixer
├── parse.py                     Exam metadata detection, question boundaries & section parser
├── organize.py                  Normalizer, dataset exporter, and directory organizer
├── analyze.py                   TF-IDF vectorizer, cosine similarity clustering, keywords
└── main.py                      Pipeline runner orchestrating all modules
```

---

## 3. Semester & Subject Curriculum Directory

### Semester 1
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Mathematical Foundations for Computer Applications** | BCA 1C 01, BCA 1CJ 102, BCA1MN101 | CBCSS / FYUGP | 21 | 518 | 2014 – 2025 |
| **Discrete Mathematics** | BCA 1C 02 | CBCSS | 12 | 309 | 2014 – 2024 |
| **Computer Fundamentals & HTML** | BCA 1B 01 | CBCSS | 9 | 198 | 2017 – 2024 |
| **Problem Solving** | BCA 1B 01 | CBCSS (2014) | 3 | 90 | 2014 – 2016 |
| **Fundamentals of Computers & Computational Thinking** | BCA 1CJ 101 | FYUGP | 2 | 40 | 2024 – 2025 |
| **Discrete Structures for Computer Applications** | BCA 1CJ 103 | FYUGP | 2 | 40 | 2024 – 2025 |
| **Digital Marketing** | BCA 1FM 105 | FYUGP | 2 | 34 | 2024 – 2025 |
| **Introduction to Computer & Office Automation** | BCA 1FS 111 | FYUGP | 2 | 34 | 2024 – 2025 |

### Semester 2
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Operations Research** | BCA 2C 04 | CBCSS (2019) | 10 | 260 | 2018 – 2025 |
| **Financial & Management Accounting** | BCA 2C 03 | CBCSS (2019) | 10 | 245 | 2018 – 2025 |
| **Problem Solving Using C** | BCA 2B 02 | CBCSS (2019) | 10 | 225 | 2018 – 2025 |
| **Computer Oriented Numerical & Statistical Methods** | BCA 2C 03, CA 2C 03 | CBCSS (2014) | 7 | 213 | 2014 – 2020 |
| **Numerical Methods** | BCA 2C 04, CA 2C 04 | CBCSS (2014) | 7 | 210 | 2014 – 2020 |
| **Object Oriented C++** | BCA 2B 02 | CBCSS (2014/17) | 6 | 168 | 2015 – 2020 |
| **Fundamentals of Programming (C Language)** | BCA 2CJ 101 | FYUGP | 2 | 40 | 2025 – 2026 |
| **Statistical Foundations for Computer Applications** | BCA 2MN 101 | FYUGP | 2 | 40 | 2025 – 2026 |
| **Numerical Analysis & Optimization Techniques** | BCA 2MN 102, BCA 2CJ 103 | FYUGP | 2 | 40 | 2025 – 2026 |
| **Data Analysis Using Spreadsheet** | Skill Course | FYUGP | 2 | 34 | 2025 – 2026 |

### Semester 3
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Data Structures Using C** | BCA 3B 04 | CBCSS (2019) | 7 | 177 | 2018 – 2024 |
| **Theory of Computation** | BCA 3C 06 | CBCSS (2019) | 7 | 169 | 2018 – 2025 |
| **Computer Oriented Numerical & Statistical Methods** | BCA 3C 05 | CBCSS (2019) | 6 | 148 | 2018 – 2024 |
| **Operations Research** | BCA 3C 06, CA 3C 06 | CBCSS (2014) | 6 | 160 | 2014 – 2019 |
| **Financial & Management Accounting** | BCA 3C 05, CA 3C 05 | CBCSS (2014) | 5 | 148 | 2014 – 2018 |
| **Database Design** | BCA 3B 03 | CBCSS (2014) | 4 | 124 | 2015 – 2018 |
| **Data Structures Using C++** | BCA 3B 04 | CBCSS (2014) | 4 | 120 | 2015 – 2018 |
| **Foundations of Artificial Intelligence** | Major Course | FYUGP | 1 | 20 | 2025 |
| **Datastructures & Algorithms** | Major Course | FYUGP | 1 | 20 | 2025 |
| **Introduction to Data Science** | Minor Course | FYUGP | 1 | 20 | 2025 |
| **Computer Networks** | Core Course | FYUGP | 1 | 20 | 2025 |
| **Website Designing Using CMS** | Skill Course | FYUGP | 1 | 17 | 2025 |

### Semester 4
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **E-Commerce** | BCA 4C 07, CA 4C 07 | CBCSS | 9 | 235 | 2015 – 2025 |
| **Database Management (DBMS & RDBMS)** | BCA 4B 05, BCS 4B 05 | CBCSS | 7 | 169 | 2020 – 2026 |
| **Computer Graphics** | BCA 4C 08 | CBCSS | 6 | 150 | 2020 – 2026 |
| **Management Information System (MIS)** | BCA 4C 08, CA 4C 08 | CBCSS (2014) | 4 | 122 | 2015 – 2018 |
| **Visual Programming** | BCA 4B 05 | CBCSS (2014) | 3 | 87 | 2016 – 2018 |
| **Basics of Audio and Video** | General A14 | CBCSS (2014) | 3 | 86 | 2016 – 2018 |
| **Java Programming** | CA 4B 05 | CBCSS (2014) | 2 | 57 | 2014 – 2015 |
| **Microprocessors** | General A13 | CBCSS | 1 | 27 | 2023 |
| **Data Communication** | Complementary | CBCSS | 1 | 27 | 2023 |
| **Software Engineering** | Core | FYUGP | 1 | 20 | 2026 |
| **Python Programming** | Core | FYUGP | 1 | 20 | 2026 |
| **Database Management System** | Core | FYUGP | 1 | 20 | 2026 |
| **Automation & Robotics** | MDC | FYUGP | 1 | 20 | 2026 |
| **Introduction to Cyber Laws** | Value Added | FYUGP | 1 | 17 | 2026 |

### Semester 5
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Computer Organization and Architecture** | BCA 5B 07, BCA 5B 08, BCA 5B 11 | CBCSS | 11 | 275 | 2016 – 2025 |
| **JAVA Programming** | BCA 5B 08, BCA 5B 07, BCA 5B 09 | CBCSS | 11 | 278 | 2016 – 2025 |
| **Principles of Software Engineering** | BCA 5B 10 | CBCSS (2019) | 8 | 201 | 2019 – 2025 |
| **Web Programming Using PHP** | BCA 5B 09 | CBCSS (2019) | 7 | 169 | 2019 – 2025 |
| **Microprocessors** | BCA 5B 12, CA 5B 08 | CBCSS (2014) | 5 | 144 | 2014 – 2018 |
| **Computer Networks** | BCA 5B 10, CA 5B 09 | CBCSS (2014) | 4 | 116 | 2014 – 2018 |
| **Android Programming** | BCA 5B 08 | CBCSS (2014) | 3 | 92 | 2016 – 2018 |
| **Visual Programming** | CA 5B 11 | CBCSS (2014) | 2 | 60 | 2014 – 2015 |
| **Software Engineering** | CA 5B 10 | CBCSS (2014) | 2 | 57 | 2014 – 2015 |
| **Data Communication** | CA 5B 07 | CBCSS (2014) | 2 | 62 | 2014 – 2015 |

### Semester 6
| Subject | Course Codes | Scheme | Papers | Questions | Year Range |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Operating System** | BCA 6B 12, BCA 6B 15 | CBCSS | 10 | 262 | 2017 – 2026 |
| **Software Testing & Quality Assurance** | BCA 6B 16 (C) (Elective) | CBCSS | 10 | 258 | 2018 – 2026 |
| **Android Programming** | BCA 6B 11 | CBCSS (2019) | 8 | 201 | 2020 – 2026 |
| **Computer Networks** | BCA 6B 13 | CBCSS (2019) | 8 | 220 | 2020 – 2026 |
| **Web Programming Using PHP** | BCA 6B 13, CA 6B 13 | CBCSS (2014) | 6 | 183 | 2015 – 2020 |
| **Software Engineering** | BCA 6B 14 | CBCSS (2014) | 4 | 125 | 2017 – 2020 |
| **System Software** | BCA 6B 16 (A) (Elective) | CBCSS | 4 | 84 | 2022 – 2026 |
| **Computer Graphics** | CA 6B 14 | CBCSS (2014) | 3 | 79 | 2015 – 2017 |

---

## 4. Key Takeaways for Building the Web Application

1. **Focus on Repeated Questions:** The biggest student value proposition is seeing which questions were repeated 4 to 6 times. For instance, in *Android Programming*, the "Application Life Cycle" question appeared in 6 distinct exam sessions (2016, 2021, 2022, 2023, 2024).
2. **Marks Weightage Cloud:** Displaying top keywords weighted by marks (e.g., `matrix` 450m, `transportation problem` 380m) gives students an immediate cheat sheet for high-scoring topics.
3. **Clean Filter by Semester:** The website should allow students to pick their current semester (e.g., Semester 6) and immediately see all subjects, their repeated questions, and exam patterns.
