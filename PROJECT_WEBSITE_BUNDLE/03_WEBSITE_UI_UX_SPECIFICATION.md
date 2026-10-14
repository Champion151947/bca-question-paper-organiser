# 🎨 Website UI/UX & Technical Specification

This document defines the interface layout, components, visual aesthetics, and frontend data binding for building the **Calicut University BCA Question Paper & Important Topics Explorer** web application.

---

## 1. Visual Design & Theme Guidelines

* **Design Aesthetic**: Sleek modern dashboard with dark mode default, subtle glowing border accents, clean cards, and smooth micro-interactions.
* **Color Palette**:
  * **Background**: `#0F172A` (Slate 900) / `#090D16` (Deep Midnight)
  * **Card Surface**: `#1E293B` (Slate 800) with border `rgba(255, 255, 255, 0.08)`
  * **Primary Accent**: `#3B82F6` (Electric Blue) / `#6366F1` (Indigo)
  * **High-Priority Repeated Badges**: `#EF4444` (Coral Red) / `#F59E0B` (Amber Gold)
  * **Text**: `#F8FAFC` (Slate 50) for headings, `#94A3B8` (Slate 400) for body/subtitles.
* **Typography**:
  * Font Family: `Inter`, `Outfit`, or system sans-serif.
  * Clear hierarchy with prominent question repetition badges.

---

## 2. Page & Component Layout

```
+-----------------------------------------------------------------------------------+
|  [Logo] BCA Question Explorer      [Search questions, topics...]      [Sem 1 - 6] |
+-----------------------------------------------------------------------------------+
|  Hero Banner: "Analyze 304 Papers | 7,784 Questions | Master High-Frequency Topics" |
+-----------------------------------------------------------------------------------+
|  Semester Filter Tabs:                                                            |
|  [ All ]  [ Sem 1 ]  [ Sem 2 ]  [ Sem 3 ]  [ Sem 4 ]  [ Sem 5 ]  [ Sem 6 ]        |
+-----------------------------------------------------------------------------------+
|  Subject Cards Grid:                                                              |
|  +------------------------+  +------------------------+  +----------------------+ |
|  | Android Programming    |  | Operating Systems      |  | Software Testing     | |
|  | Sem 6 | CBCSS          |  | Sem 6 | CBCSS          |  | Sem 6 | Elective     | |
|  | 8 Papers | 201 Qs      |  | 10 Papers | 262 Qs     |  | 10 Papers | 258 Qs   | |
|  | 🔥 16 High-Repetition  |  | 🔥 8 High-Repetition   |  | 🔥 19 High-Repetition| |
|  | [Explore Subject ->]   |  | [Explore Subject ->]   |  | [Explore Subject ->] | |
|  +------------------------+  +------------------------+  +----------------------+ |
+-----------------------------------------------------------------------------------+
```

---

## 3. Subject Detail Modal / View

When a user clicks on a subject card, an interactive view opens:

1. **Header Section**:
   * Subject title, semester, course code, and total questions.
   * **Keywords Weightage Cloud**: Badges showing top scored keywords (e.g., `layout (190m)`, `intent (160m)`, `content provider (140m)`).
2. **Frequency Filter Tabs**:
   * `All Repeated Questions`
   * `🔥 Super High Priority (Asked 5+ times)`
   * `⚡ High Priority (Asked 3–4 times)`
   * `📌 Frequent (Asked 2 times)`
3. **Repeated Question Accordion Card**:
   * **Badge**: e.g., `Repeated 6 times (Years: 2016, 2021, 2022, 2023, 2024)`
   * **Main Question Text**: Clean canonical wording.
   * **Accordion Toggle**: Expands to show the exact question variations as they appeared across different exam years.
   * **Action**: "Mark as Mastered" checkmark (persists in browser `localStorage`).

---

## 4. Frontend Data Integration

All data is bundled in `04_website_data.json`.
The application loads this JSON directly:
```javascript
// Example data access in frontend:
fetch('./04_website_data.json')
  .then(res => res.json())
  .then(data => {
    // data is an object: { "Subject Name": { subject, semesters, repeated_questions, top_keywords, ... } }
    renderSubjectCards(data);
  });
```

---

## 5. Instant Search Behavior
* As the user types in the search bar (e.g., `"deadlock"`, `"normal form"`, `"stack"`):
  * Matches against **Subject names**, **Repeated question texts**, and **Top keywords**.
  * Shows instant search results dropdown or filters the view in real-time.
