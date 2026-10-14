# 📋 MASTER PROMPT FOR CLAUDE (COPY & PASTE READY)

> **Instructions for the User:**
> Copy everything below the line and paste it directly into Claude. Claude will read the requirements and write the complete website code for you!

---

```markdown
# TASK: Build a Modern Interactive Web Application for "Calicut University BCA Question Paper & Important Topics Explorer"

## 1. Project Background & Objective
I have processed and analyzed 304 Calicut University BCA question papers covering Semester 1 to Semester 6 (spanning 2014 to 2026 across CBCSS and FYUGP schemes), extracting 7,784 individual questions.
I need a modern, beautiful, fast, and responsive web application that helps students instantly find:
1. **Most Repeated & High-Frequency Questions** (questions asked 6x, 5x, 4x, 3x across past university exams).
2. **High-Weightage Topics & Keywords by Marks** for every subject.
3. **Semester & Subject Explorer** (Semesters 1 to 6, covering CBCSS and FYUGP).
4. **Instant Question Search**: Real-time search across topics, question texts, marks, and years.
5. **Exam Revision & Topic Priority Checklist**: Helping students prioritize what to study first for maximum marks.

---

## 2. Dataset Structure
I have an aggregated JSON dataset `04_website_data.json` with 48 subjects. Each subject entry contains:
```json
{
  "subject": "Android Programming",
  "semesters": [5, 6],
  "programmes": ["CBCSS"],
  "years": [2016, 2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
  "course_codes": ["BCA 5B 08", "BCA 6B 11"],
  "total_papers": 11,
  "total_questions": 293,
  "repeated_groups_count": 30,
  "high_frequency_groups_count": 16,
  "repeated_questions": [
    {
      "repeat_count": 6,
      "years": "2016, 2021, 2022, 2023, 2024",
      "main_question": "Explain the structure of android application and its life-cycle",
      "variants": [
        "List the structure of android application (2021)",
        "Explain in detail about android application life cycle (2021)",
        "Define the structure of Android application (2022)",
        "Write a short note on Structure of android application and Application life cycle (2023)"
      ]
    }
  ],
  "top_keywords": [
    {"keyword": "android", "marks": 520.0},
    {"keyword": "application", "marks": 240.0},
    {"keyword": "layout", "marks": 190.0},
    {"keyword": "intent", "marks": 160.0}
  ]
}
```

---

## 3. Key Website Features & Requirements

### A. Navigation & Semester Filter
- **Semester Tabs**: Quick toggle between **Semester 1, 2, 3, 4, 5, 6**, and **All Semesters**.
- **Scheme Badge**: Filter/tag subjects by **CBCSS (2014-2024)** or **FYUGP (2024+)**.

### B. Subject Dashboard & Cards
- Display cards for each subject with:
  - Subject Name & Course Code (e.g., `BCA 6B 11`).
  - Total Papers & Questions count.
  - Exam Year span (e.g., 2016 – 2026).
  - High-priority badge (e.g., "16 High-Frequency Questions").
  - Click to open the **Subject Deep-Dive Modal or Page**.

### C. Repeated Questions & Important Topics View (The Core Feature)
When viewing a subject:
- **Repetition Frequency Filter**: Tabs/pills to filter questions:
  - 🔥 **Super High Priority (Asked 5+ or 6+ times)**
  - ⚡ **High Priority (Asked 3–4 times)**
  - 📌 **Frequent (Asked 2 times)**
- **Interactive Question Accordion**:
  - Displays the canonical question with repetition count badge and years asked.
  - Expands to reveal all past year wording variations and exam years.
- **Top Keywords & Mark Weightage Cloud**:
  - Visual pills/tags showing the most rewarded topics (e.g., `intent (160m)`, `layout (190m)`).

### D. Global Instant Search
- Search bar at the top: live filter questions and topics across all subjects or within the selected semester.
- Highlight matched terms.

### E. Study Checklist / Bookmark Feature
- LocalStorage bookmarking so students can mark questions as "Mastered" or "To Revise".

---

## 4. Design & UI Aesthetics
- **Theme**: Premium modern dark/light mode interface (Tailwind CSS, sleek glassmorphism, smooth animations).
- **Typography**: Inter or Outfit font family, clean hierarchy.
- **Mobile First**: Completely responsive on smartphones, tablets, and desktops.

---

## 5. Output Desired
Please provide the complete, clean, modular frontend code:
1. `index.html` (or React/Next.js component structure).
2. `app.js` (including embedded data loader for `04_website_data.json`, search, filters, state management).
3. `styles.css` (or Tailwind styling instructions).
4. Step-by-step instructions on how to run or deploy it (e.g. GitHub Pages, Vercel, or locally).
```
