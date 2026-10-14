/**
 * Calicut University BCA Question Paper & Important Topics Explorer
 * Core Application Engine & Data Controller
 */

(function () {
  'use strict';

  // State Management
  const state = {
    data: {},
    subjectsList: [],
    currentSemester: 'all',
    currentScheme: 'all',
    searchQuery: '',
    sortBy: 'repeats', // 'repeats' | 'questions' | 'name'
    activeSubject: null,
    modalFreqFilter: 'all', // 'all' | 'super' (5+) | 'high' (3-4) | 'frequent' (2)
    modalKeywordFilter: null,
    masteredQuestions: new Set(),
  };

  // LocalStorage Key
  const STORAGE_KEY = 'cu_bca_mastered_v1';

  // DOM Elements Cache
  const elements = {
    heroTotalPapers: document.getElementById('statTotalPapers'),
    heroTotalQuestions: document.getElementById('statTotalQuestions'),
    heroTotalSubjects: document.getElementById('statTotalSubjects'),
    heroTotalRepeats: document.getElementById('statTotalRepeats'),
    subjectsGrid: document.getElementById('subjectsGrid'),
    resultsCount: document.getElementById('resultsCount'),
    activeFilterText: document.getElementById('activeFilterText'),
    searchInput: document.getElementById('globalSearchInput'),
    searchClearBtn: document.getElementById('searchClearBtn'),
    semTabsContainer: document.getElementById('semesterTabs'),
    schemeSelect: document.getElementById('schemeFilter'),
    sortSelect: document.getElementById('sortBySelect'),
    // Modals
    subjectModal: document.getElementById('subjectModal'),
    modalCloseBtn: document.getElementById('modalCloseBtn'),
    modalSubjectTitle: document.getElementById('modalSubjectTitle'),
    modalSubjectCodes: document.getElementById('modalSubjectCodes'),
    modalSubjectMeta: document.getElementById('modalSubjectMeta'),
    modalKeywordsCloud: document.getElementById('modalKeywordsCloud'),
    modalFreqTabs: document.getElementById('modalFreqTabs'),
    modalQuestionsList: document.getElementById('modalQuestionsList'),
    modalProgressTrack: document.getElementById('modalProgressTrack'),
    modalProgressText: document.getElementById('modalProgressText'),
    // Revision Modal
    revisionModal: document.getElementById('revisionModal'),
    revisionModalCloseBtn: document.getElementById('revisionModalCloseBtn'),
    btnOpenRevision: document.getElementById('btnOpenRevision'),
    revisionQuestionsList: document.getElementById('revisionQuestionsList'),
    revStatTotal: document.getElementById('revStatTotal'),
    revStatHigh: document.getElementById('revStatHigh'),
    revStatPercent: document.getElementById('revStatPercent'),
    btnPrintRevision: document.getElementById('btnPrintRevision'),
    btnClearMastered: document.getElementById('btnClearMastered'),
    // Guide Modal
    guideModal: document.getElementById('guideModal'),
    guideModalCloseBtn: document.getElementById('guideModalCloseBtn'),
    btnOpenGuide: document.getElementById('btnOpenGuide'),
    // Nav Counter
    navMasteredCount: document.getElementById('navMasteredCount'),
    // Toast
    toastContainer: document.getElementById('toastContainer'),
  };

  /**
   * Initialize Application
   */
  async function init() {
    loadMasteredState();
    setupEventListeners();
    await loadData();
    renderHeroStats();
    applyFiltersAndRender();
    checkUrlHash();
    updateGlobalMasteredCounter();
  }

  /**
   * Load Data with fallback
   */
  async function loadData() {
    try {
      if (window.BCA_WEBSITE_DATA && Object.keys(window.BCA_WEBSITE_DATA).length > 0) {
        state.data = window.BCA_WEBSITE_DATA;
      } else {
        const response = await fetch('./04_website_data.json');
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        state.data = await response.json();
      }
    } catch (err) {
      console.warn('Direct fetch failed, falling back to window.BCA_WEBSITE_DATA:', err);
      if (window.BCA_WEBSITE_DATA) {
        state.data = window.BCA_WEBSITE_DATA;
      } else {
        showToast('Error loading dataset. Please check your network or browser settings.', 'error');
        return;
      }
    }

    state.subjectsList = Object.values(state.data);
  }

  /**
   * Mastered / Study Checklist Persistence
   */
  function loadMasteredState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        state.masteredQuestions = new Set(JSON.parse(saved));
      }
    } catch (e) {
      console.error('Failed to parse mastered state from localStorage', e);
      state.masteredQuestions = new Set();
    }
  }

  function saveMasteredState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(state.masteredQuestions)));
      updateGlobalMasteredCounter();
    } catch (e) {
      console.error('Failed to save mastered state to localStorage', e);
    }
  }

  function toggleMastered(questionId) {
    if (state.masteredQuestions.has(questionId)) {
      state.masteredQuestions.delete(questionId);
      showToast('Marked as to revise');
    } else {
      state.masteredQuestions.add(questionId);
      showToast('Marked as mastered! 🎉');
    }
    saveMasteredState();
  }

  function updateGlobalMasteredCounter() {
    if (elements.navMasteredCount) {
      elements.navMasteredCount.textContent = state.masteredQuestions.size;
    }
  }

  /**
   * Hero Stats
   */
  function renderHeroStats() {
    let totalPapers = 0;
    let totalQuestions = 0;
    let totalRepeatedGroups = 0;

    state.subjectsList.forEach((sub) => {
      totalPapers += sub.total_papers || 0;
      totalQuestions += sub.total_questions || 0;
      totalRepeatedGroups += sub.repeated_groups_count || 0;
    });

    if (elements.heroTotalPapers) elements.heroTotalPapers.textContent = totalPapers || 304;
    if (elements.heroTotalQuestions) elements.heroTotalQuestions.textContent = (totalQuestions || 7784).toLocaleString();
    if (elements.heroTotalSubjects) elements.heroTotalSubjects.textContent = state.subjectsList.length || 48;
    if (elements.heroTotalRepeats) elements.heroTotalRepeats.textContent = totalRepeatedGroups.toLocaleString();
  }

  /**
   * Filter & Sort Subjects
   */
  function getFilteredSubjects() {
    const q = state.searchQuery.trim().toLowerCase();

    return state.subjectsList.filter((sub) => {
      // Semester filter
      if (state.currentSemester !== 'all') {
        const targetSem = parseInt(state.currentSemester, 10);
        if (!sub.semesters || !sub.semesters.includes(targetSem)) {
          return false;
        }
      }

      // Scheme filter
      if (state.currentScheme !== 'all') {
        if (!sub.programmes || !sub.programmes.some((p) => p.toUpperCase().includes(state.currentScheme))) {
          return false;
        }
      }

      // Search query filter
      if (q) {
        const matchesName = sub.subject.toLowerCase().includes(q);
        const matchesCode = sub.course_codes && sub.course_codes.some((c) => c.toLowerCase().includes(q));
        const matchesKeywords = sub.top_keywords && sub.top_keywords.some((k) => k.keyword.toLowerCase().includes(q));
        const matchesRepeated =
          sub.repeated_questions &&
          sub.repeated_questions.some(
            (rq) =>
              rq.main_question.toLowerCase().includes(q) ||
              (rq.variants && rq.variants.some((v) => v.toLowerCase().includes(q)))
          );

        if (!matchesName && !matchesCode && !matchesKeywords && !matchesRepeated) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      if (state.sortBy === 'name') {
        return a.subject.localeCompare(b.subject);
      } else if (state.sortBy === 'questions') {
        return (b.total_questions || 0) - (a.total_questions || 0);
      } else {
        // default: high frequency / repeated groups count
        return (b.high_frequency_groups_count || 0) - (a.high_frequency_groups_count || 0);
      }
    });
  }

  /**
   * Render Subject Cards Grid
   */
  function applyFiltersAndRender() {
    const filtered = getFilteredSubjects();

    if (elements.resultsCount) {
      elements.resultsCount.textContent = `Showing ${filtered.length} of ${state.subjectsList.length} subjects`;
    }

    if (elements.activeFilterText) {
      const semLabel = state.currentSemester === 'all' ? 'All Semesters' : `Semester ${state.currentSemester}`;
      const schemeLabel = state.currentScheme === 'all' ? 'All Schemes' : state.currentScheme;
      const searchLabel = state.searchQuery ? ` • Search: "${state.searchQuery}"` : '';
      elements.activeFilterText.textContent = `${semLabel} • ${schemeLabel}${searchLabel}`;
    }

    if (!elements.subjectsGrid) return;

    if (filtered.length === 0) {
      elements.subjectsGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3>No matching subjects found</h3>
          <p>Try clearing your search query or switching semester and scheme filters.</p>
        </div>
      `;
      return;
    }

    elements.subjectsGrid.innerHTML = filtered.map((sub) => createSubjectCardHtml(sub)).join('');

    // Attach click listeners to cards
    const cards = elements.subjectsGrid.querySelectorAll('.subject-card');
    cards.forEach((card) => {
      card.addEventListener('click', (e) => {
        const subjectName = card.getAttribute('data-subject');
        if (subjectName && state.data[subjectName]) {
          openSubjectModal(state.data[subjectName]);
        }
      });
    });
  }

  /**
   * Generate HTML for Subject Card
   */
  function createSubjectCardHtml(sub) {
    const semestersHtml = (sub.semesters || [])
      .map((s) => `<span class="badge-sem">Sem ${s}</span>`)
      .join('');

    const schemeHtml = (sub.programmes || ['CBCSS'])
      .map((p) => `<span class="badge-scheme">${p}</span>`)
      .join('');

    const courseCodes = (sub.course_codes || []).slice(0, 2).join(' • ');

    const minYear = sub.years && sub.years.length ? Math.min(...sub.years) : 2016;
    const maxYear = sub.years && sub.years.length ? Math.max(...sub.years) : 2026;
    const yearSpan = `${minYear} – ${maxYear}`;

    const highRepCount = sub.high_frequency_groups_count || 0;
    const repGroupsCount = sub.repeated_groups_count || 0;

    // Top 3 keywords
    const topKeywords = (sub.top_keywords || []).slice(0, 3);
    const keywordsHtml = topKeywords
      .map((k) => `<span class="keyword-pill">${escapeHtml(k.keyword)}<strong>${Math.round(k.marks)}m</strong></span>`)
      .join('');

    const isSuperPriority = highRepCount >= 10;

    return `
      <div class="subject-card" data-subject="${escapeHtml(sub.subject)}">
        <div class="subject-card-top">
          <div class="subject-sem-badges">
            ${semestersHtml}
            ${schemeHtml}
          </div>
          <h3 class="subject-title" title="${escapeHtml(sub.subject)}">${escapeHtml(sub.subject)}</h3>
          ${courseCodes ? `<div class="subject-code-tag">${escapeHtml(courseCodes)}</div>` : ''}

          <div class="subject-meta-grid">
            <div class="meta-item">
              <span class="meta-item-label">Papers</span>
              <span class="meta-item-val">${sub.total_papers || 0}</span>
            </div>
            <div class="meta-item">
              <span class="meta-item-label">Questions</span>
              <span class="meta-item-val">${sub.total_questions || 0}</span>
            </div>
            <div class="meta-item">
              <span class="meta-item-label">Years Analyzed</span>
              <span class="meta-item-val" style="font-size:0.85rem">${yearSpan}</span>
            </div>
            <div class="meta-item">
              <span class="meta-item-label">Repeated Sets</span>
              <span class="meta-item-val">${repGroupsCount}</span>
            </div>
          </div>

          <div class="high-rep-banner ${isSuperPriority ? 'super' : ''}">
            <div class="high-rep-text">
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.527.82-1.173 2.062-1.874 3.498A33.25 33.25 0 016.14 10.3c-.63.95-1.14 1.83-1.47 2.65-.33.82-.47 1.62-.47 2.45a5.8 5.8 0 001.7 4.1 5.8 5.8 0 004.1 1.7c1.55 0 3.03-.62 4.1-1.7a5.8 5.8 0 001.7-4.1c0-.83-.14-1.63-.47-2.45-.33-.82-.84-1.7-1.47-2.65a33.25 33.25 0 01-2.11-3.75 42.4 42.4 0 01-1.87-3.5zM10 18.2a4 4 0 01-2.83-1.17 4 4 0 01-1.17-2.83c0-.6.1-1.2.34-1.8.25-.6.64-1.28 1.15-2.05.51-.78 1.14-1.67 1.8-2.67.24-.37.49-.74.71-1.1.22.36.47.73.71 1.1.66 1 1.29 1.89 1.8 2.67.51.77.9 1.45 1.15 2.05.24.6.34 1.2.34 1.8a4 4 0 01-1.17 2.83A4 4 0 0110 18.2z" clip-rule="evenodd"/>
              </svg>
              <span>${highRepCount} High-Frequency Qs</span>
            </div>
            <span class="rep-count-badge">${sub.repeated_questions ? sub.repeated_questions.length : 0} Qs</span>
          </div>

          ${keywordsHtml ? `<div class="subject-keywords-preview">${keywordsHtml}</div>` : ''}
        </div>

        <button class="btn-card-explore" type="button" aria-label="Explore ${escapeHtml(sub.subject)}">
          <span>Explore Questions & Topics</span>
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
          </svg>
        </button>
      </div>
    `;
  }

  /**
   * Subject Deep-Dive Modal View
   */
  function openSubjectModal(sub) {
    state.activeSubject = sub;
    state.modalFreqFilter = 'all';
    state.modalKeywordFilter = null;

    // Update URL hash for direct bookmarking/sharing
    window.location.hash = `subject=${encodeURIComponent(sub.subject)}`;

    // Populate Headers
    elements.modalSubjectTitle.textContent = sub.subject;
    elements.modalSubjectCodes.textContent = (sub.course_codes || []).join(' • ') || 'Calicut University BCA';

    const minYear = sub.years && sub.years.length ? Math.min(...sub.years) : 2016;
    const maxYear = sub.years && sub.years.length ? Math.max(...sub.years) : 2026;
    elements.modalSubjectMeta.innerHTML = `
      <span>📅 ${minYear} – ${maxYear}</span>
      <span>📄 ${sub.total_papers || 0} Exam Papers</span>
      <span>❓ ${sub.total_questions || 0} Questions Total</span>
      <span>🔥 ${sub.high_frequency_groups_count || 0} High-Frequency</span>
    `;

    // Render Keywords Cloud
    renderModalKeywordsCloud(sub);

    // Render Questions & Frequency Tabs
    renderModalQuestions();

    // Show Modal
    elements.subjectModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSubjectModal() {
    state.activeSubject = null;
    elements.subjectModal.classList.remove('active');
    document.body.style.overflow = '';
    history.replaceState(null, '', window.location.pathname);
  }

  /**
   * Render Modal Keywords Cloud
   */
  function renderModalKeywordsCloud(sub) {
    const keywords = (sub.top_keywords || []).slice(0, 14);

    if (keywords.length === 0) {
      elements.modalKeywordsCloud.innerHTML = '<span style="color:var(--text-dim);font-size:0.8rem">No keyword data available</span>';
      return;
    }

    elements.modalKeywordsCloud.innerHTML = keywords
      .map((k) => {
        const isActive = state.modalKeywordFilter === k.keyword;
        return `
          <button class="keyword-cloud-pill ${isActive ? 'active' : ''}" data-keyword="${escapeHtml(k.keyword)}" type="button">
            <span>${escapeHtml(k.keyword)}</span>
            <span class="keyword-marks-tag">${Math.round(k.marks)}m</span>
          </button>
        `;
      })
      .join('');

    elements.modalKeywordsCloud.querySelectorAll('.keyword-cloud-pill').forEach((pill) => {
      pill.addEventListener('click', () => {
        const kw = pill.getAttribute('data-keyword');
        if (state.modalKeywordFilter === kw) {
          state.modalKeywordFilter = null; // deselect
        } else {
          state.modalKeywordFilter = kw;
        }
        renderModalKeywordsCloud(sub);
        renderModalQuestions();
      });
    });
  }

  /**
   * Render Filtered Questions inside Modal
   */
  function renderModalQuestions() {
    if (!state.activeSubject) return;

    const questions = state.activeSubject.repeated_questions || [];

    // Filter by frequency
    let filtered = questions.filter((q) => {
      if (state.modalFreqFilter === 'super') return q.repeat_count >= 5;
      if (state.modalFreqFilter === 'high') return q.repeat_count >= 3 && q.repeat_count < 5;
      if (state.modalFreqFilter === 'frequent') return q.repeat_count === 2;
      return true;
    });

    // Filter by keyword if selected
    if (state.modalKeywordFilter) {
      const kw = state.modalKeywordFilter.toLowerCase();
      filtered = filtered.filter((q) => {
        const matchesMain = q.main_question.toLowerCase().includes(kw);
        const matchesVar = q.variants && q.variants.some((v) => v.toLowerCase().includes(kw));
        return matchesMain || matchesVar;
      });
    }

    // Update Progress Bar
    const totalSubjectQuestions = questions.length;
    let masteredCount = 0;
    questions.forEach((q) => {
      const qId = getQuestionId(state.activeSubject.subject, q.main_question);
      if (state.masteredQuestions.has(qId)) {
        masteredCount++;
      }
    });

    const percent = totalSubjectQuestions > 0 ? Math.round((masteredCount / totalSubjectQuestions) * 100) : 0;
    if (elements.modalProgressTrack) elements.modalProgressTrack.style.width = `${percent}%`;
    if (elements.modalProgressText) elements.modalProgressText.textContent = `${masteredCount} / ${totalSubjectQuestions} Mastered (${percent}%)`;

    // Render Frequency Filter Tabs
    renderModalFreqTabs(questions);

    // Render Accordion
    if (filtered.length === 0) {
      elements.modalQuestionsList.innerHTML = `
        <div class="empty-state">
          <p>No questions match the current filter.</p>
        </div>
      `;
      return;
    }

    elements.modalQuestionsList.innerHTML = filtered
      .map((q, idx) => createQuestionAccordionHtml(q, state.activeSubject.subject, idx))
      .join('');

    // Attach Accordion & Checkbox listeners
    attachAccordionListeners(elements.modalQuestionsList);
  }

  /**
   * Render Frequency Tabs inside Modal
   */
  function renderModalFreqTabs(allQuestions) {
    const totalAll = allQuestions.length;
    const totalSuper = allQuestions.filter((q) => q.repeat_count >= 5).length;
    const totalHigh = allQuestions.filter((q) => q.repeat_count >= 3 && q.repeat_count < 5).length;
    const totalFreq = allQuestions.filter((q) => q.repeat_count === 2).length;

    elements.modalFreqTabs.innerHTML = `
      <button class="freq-tab-btn ${state.modalFreqFilter === 'all' ? 'active' : ''}" data-filter="all">
        All Questions (${totalAll})
      </button>
      <button class="freq-tab-btn flame ${state.modalFreqFilter === 'super' ? 'active' : ''}" data-filter="super">
        🔥 Super High (5+ times: ${totalSuper})
      </button>
      <button class="freq-tab-btn ${state.modalFreqFilter === 'high' ? 'active' : ''}" data-filter="high">
        ⚡ High Priority (3-4 times: ${totalHigh})
      </button>
      <button class="freq-tab-btn ${state.modalFreqFilter === 'frequent' ? 'active' : ''}" data-filter="frequent">
        📌 Frequent (2 times: ${totalFreq})
      </button>
    `;

    elements.modalFreqTabs.querySelectorAll('.freq-tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.modalFreqFilter = btn.getAttribute('data-filter');
        renderModalQuestions();
      });
    });
  }

  /**
   * Create Accordion Question Item HTML
   */
  function createQuestionAccordionHtml(q, subjectName, index) {
    const qId = getQuestionId(subjectName, q.main_question);
    const isMastered = state.masteredQuestions.has(qId);

    let repTagClass = 'repeat-2';
    if (q.repeat_count >= 5) repTagClass = 'repeat-5';
    else if (q.repeat_count >= 3) repTagClass = 'repeat-3';

    const variants = q.variants || [];

    return `
      <div class="question-accordion-card ${isMastered ? 'mastered' : ''}" id="card-${qId}">
        <div class="question-card-header" data-id="${qId}">
          <input type="checkbox" class="question-checkbox" ${isMastered ? 'checked' : ''} data-id="${qId}" title="Mark as mastered" aria-label="Mark as mastered" />
          <div class="question-header-content">
            <div class="question-badges-row">
              <span class="rep-tag ${repTagClass}">${q.repeat_count}x Repeated</span>
              <span class="years-tag">Years: ${escapeHtml(q.years || 'Past Exams')}</span>
            </div>
            <div class="main-question-text">${escapeHtml(q.main_question)}</div>
          </div>
          <svg class="accordion-chevron-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        <div class="question-accordion-body">
          <div class="accordion-inner-content">
            <div class="variants-section-title">
              <span>Past Exam Variations (${variants.length})</span>
              <button class="btn-copy-question" data-text="${escapeHtml(q.main_question)}" type="button">
                <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy Question
              </button>
            </div>
            <ul class="variants-list">
              ${variants.map((v) => `<li class="variant-item">${escapeHtml(v)}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Attach listeners to question accordions and checkboxes
   */
  function attachAccordionListeners(container) {
    // Accordion Toggle
    const headers = container.querySelectorAll('.question-card-header');
    headers.forEach((hdr) => {
      hdr.addEventListener('click', (e) => {
        // If clicking directly on checkbox or copy button, do not toggle accordion
        if (e.target.closest('.question-checkbox') || e.target.closest('.btn-copy-question')) return;

        const card = hdr.closest('.question-accordion-card');
        card.classList.toggle('open');
      });
    });

    // Checkbox Mastered Toggle
    const checkboxes = container.querySelectorAll('.question-checkbox');
    checkboxes.forEach((cb) => {
      cb.addEventListener('change', (e) => {
        const qId = cb.getAttribute('data-id');
        toggleMastered(qId);
        const card = cb.closest('.question-accordion-card');
        if (card) {
          card.classList.toggle('mastered', cb.checked);
        }
        // Recalculate modal progress bar if in subject modal
        if (state.activeSubject) {
          updateModalProgressBar();
        }
      });
    });

    // Copy Question Text
    const copyBtns = container.querySelectorAll('.btn-copy-question');
    copyBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = btn.getAttribute('data-text');
        if (navigator.clipboard && text) {
          navigator.clipboard.writeText(text).then(() => {
            showToast('Question copied to clipboard! 📋');
          });
        }
      });
    });
  }

  function updateModalProgressBar() {
    if (!state.activeSubject) return;
    const questions = state.activeSubject.repeated_questions || [];
    let count = 0;
    questions.forEach((q) => {
      const qId = getQuestionId(state.activeSubject.subject, q.main_question);
      if (state.masteredQuestions.has(qId)) count++;
    });
    const percent = questions.length > 0 ? Math.round((count / questions.length) * 100) : 0;
    if (elements.modalProgressTrack) elements.modalProgressTrack.style.width = `${percent}%`;
    if (elements.modalProgressText) elements.modalProgressText.textContent = `${count} / ${questions.length} Mastered (${percent}%)`;
  }

  /**
   * Revision Mode / Mastered Checklist Modal View
   */
  function openRevisionModal() {
    const masteredIds = state.masteredQuestions;
    const allMasteredQuestions = [];

    // Search across all subjects for matching questions
    state.subjectsList.forEach((sub) => {
      if (!sub.repeated_questions) return;
      sub.repeated_questions.forEach((q) => {
        const qId = getQuestionId(sub.subject, q.main_question);
        if (masteredIds.has(qId)) {
          allMasteredQuestions.push({
            subject: sub.subject,
            question: q,
            id: qId,
          });
        }
      });
    });

    // Stats
    const totalMastered = allMasteredQuestions.length;
    const highFreqMastered = allMasteredQuestions.filter((item) => item.question.repeat_count >= 3).length;
    let totalAllRepeated = 0;
    state.subjectsList.forEach((sub) => {
      totalAllRepeated += (sub.repeated_questions || []).length;
    });
    const completionPercent = totalAllRepeated > 0 ? ((totalMastered / totalAllRepeated) * 100).toFixed(1) : 0;

    if (elements.revStatTotal) elements.revStatTotal.textContent = totalMastered;
    if (elements.revStatHigh) elements.revStatHigh.textContent = highFreqMastered;
    if (elements.revStatPercent) elements.revStatPercent.textContent = `${completionPercent}%`;

    // Render list
    if (totalMastered === 0) {
      elements.revisionQuestionsList.innerHTML = `
        <div class="empty-state">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3>No Mastered Questions Yet</h3>
          <p>Explore any subject and click the checkmark next to a question to add it to your revision checklist.</p>
        </div>
      `;
    } else {
      elements.revisionQuestionsList.innerHTML = allMasteredQuestions
        .map((item, idx) => {
          return `
            <div style="margin-bottom:0.75rem;">
              <span class="badge-sem" style="font-size:0.75rem">${escapeHtml(item.subject)}</span>
              ${createQuestionAccordionHtml(item.question, item.subject, idx)}
            </div>
          `;
        })
        .join('');

      attachAccordionListeners(elements.revisionQuestionsList);
    }

    elements.revisionModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeRevisionModal() {
    elements.revisionModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  /**
   * Guide Modal
   */
  function openGuideModal() {
    elements.guideModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeGuideModal() {
    elements.guideModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  /**
   * Event Listeners Registration
   */
  function setupEventListeners() {
    // Semester Tabs
    if (elements.semTabsContainer) {
      elements.semTabsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.sem-tab-btn');
        if (!btn) return;
        elements.semTabsContainer.querySelectorAll('.sem-tab-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        state.currentSemester = btn.getAttribute('data-sem');
        applyFiltersAndRender();
      });
    }

    // Scheme Filter
    if (elements.schemeSelect) {
      elements.schemeSelect.addEventListener('change', (e) => {
        state.currentScheme = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Sort By
    if (elements.sortSelect) {
      elements.sortSelect.addEventListener('change', (e) => {
        state.sortBy = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Search Input with Debounce
    let searchTimeout = null;
    if (elements.searchInput) {
      elements.searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          state.searchQuery = e.target.value;
          applyFiltersAndRender();
        }, 200);
      });
    }

    // Clear Search
    if (elements.searchClearBtn) {
      elements.searchClearBtn.addEventListener('click', () => {
        if (elements.searchInput) {
          elements.searchInput.value = '';
          state.searchQuery = '';
          applyFiltersAndRender();
        }
      });
    }

    // Modals Close handlers
    if (elements.modalCloseBtn) elements.modalCloseBtn.addEventListener('click', closeSubjectModal);
    if (elements.subjectModal) {
      elements.subjectModal.addEventListener('click', (e) => {
        if (e.target === elements.subjectModal) closeSubjectModal();
      });
    }

    if (elements.revisionModalCloseBtn) elements.revisionModalCloseBtn.addEventListener('click', closeRevisionModal);
    if (elements.revisionModal) {
      elements.revisionModal.addEventListener('click', (e) => {
        if (e.target === elements.revisionModal) closeRevisionModal();
      });
    }

    if (elements.guideModalCloseBtn) elements.guideModalCloseBtn.addEventListener('click', closeGuideModal);
    if (elements.guideModal) {
      elements.guideModal.addEventListener('click', (e) => {
        if (e.target === elements.guideModal) closeGuideModal();
      });
    }

    // Open Modals Nav
    if (elements.btnOpenRevision) elements.btnOpenRevision.addEventListener('click', openRevisionModal);
    if (elements.btnOpenGuide) elements.btnOpenGuide.addEventListener('click', openGuideModal);

    // Print Revision
    if (elements.btnPrintRevision) {
      elements.btnPrintRevision.addEventListener('click', () => {
        window.print();
      });
    }

    // Clear All Mastered
    if (elements.btnClearMastered) {
      elements.btnClearMastered.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your study progress checklist?')) {
          state.masteredQuestions.clear();
          saveMasteredState();
          openRevisionModal();
          showToast('Mastered questions cleared');
        }
      });
    }

    // Global ESC key listener to close active modal
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (elements.subjectModal.classList.contains('active')) closeSubjectModal();
        if (elements.revisionModal.classList.contains('active')) closeRevisionModal();
        if (elements.guideModal.classList.contains('active')) closeGuideModal();
      }
    });

    // Hash change listener
    window.addEventListener('hashchange', checkUrlHash);
  }

  /**
   * Check URL hash to open specific subject directly
   */
  function checkUrlHash() {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#subject=')) {
      const subjectName = decodeURIComponent(hash.replace('#subject=', ''));
      if (state.data[subjectName]) {
        openSubjectModal(state.data[subjectName]);
      }
    }
  }

  /**
   * Utilities
   */
  function getQuestionId(subject, questionText) {
    // Generate stable alphanumeric hash key
    const str = `${subject}_${questionText}`.toLowerCase().replace(/[^a-z0-9]/g, '');
    return str.slice(0, 48);
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showToast(message, type = 'info') {
    if (!elements.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast show ${type}`;
    toast.innerHTML = `
      <span>${escapeHtml(message)}</span>
    `;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }

  // Start application on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
