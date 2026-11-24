/**
 * Citizen Scheme AI - Modern Single Page Application Logic
 * Integrates with FastAPI backend for deterministic eligibility, multilingual RAG, and scheme comparisons.
 */

const state = {
  currentLang: 'en',
  allSchemes: [],
  schemes: [],
  categories: [],
  ministries: [],
  translations: {},
  compareSelectedIds: [],
  lastProfile: null,
  lastAuditResults: [],
  auditStatusFilter: 'all',
  chatHistory: []
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([
    fetchTranslations(state.currentLang),
    fetchCategories(),
    fetchMinistries(),
    fetchSchemes()
  ]);

  initCompareSelections();
});

// =============================================================================
// API CALLS
// =============================================================================

async function fetchTranslations(lang) {
  try {
    const res = await fetch(`/api/translations/${lang}`);
    if (res.ok) {
      state.translations = await res.json();
      applyTranslations();
    }
  } catch (err) {
    console.error("Failed to fetch translations:", err);
  }
}

async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    if (res.ok) {
      state.categories = await res.json();
      populateCategoryFilters();
    }
  } catch (err) {
    console.error("Failed to fetch categories:", err);
  }
}

async function fetchMinistries() {
  try {
    const res = await fetch('/api/ministries');
    if (res.ok) {
      state.ministries = await res.json();
      populateMinistryFilters();
    }
  } catch (err) {
    console.error("Failed to fetch ministries:", err);
  }
}

async function fetchSchemes(params = {}) {
  try {
    const isMasterFetch = Object.keys(params).length === 0;
    const query = new URLSearchParams(params).toString();
    const url = query ? `/api/schemes?${query}` : '/api/schemes';
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      state.schemes = data;
      if (isMasterFetch || state.allSchemes.length === 0) {
        state.allSchemes = data;
      }
      renderSchemesGrid(state.schemes);
      updateSchemesCounter(state.schemes.length);
    }
  } catch (err) {
    console.error("Failed to fetch schemes:", err);
    document.getElementById('schemes-grid').innerHTML = `
      <div class="col-span-full text-center py-12 text-slate-500">
        Failed to load schemes from server. Please verify backend is running.
      </div>
    `;
  }
}

// =============================================================================
// LOCALIZATION & LANGUAGE SWITCHING
// =============================================================================

async function changeLanguage(lang) {
  state.currentLang = lang;
  await fetchTranslations(lang);

  // If eligibility was already computed, re-evaluate to translate explanation strings
  if (state.lastProfile) {
    await runEligibilityEvaluation(state.lastProfile);
  }

  // Re-render schemes to show native names if available
  renderSchemesGrid(state.schemes);
  renderCompareChips();
  if (state.compareSelectedIds.length > 0) {
    updateComparisonView();
  }
}

function applyTranslations() {
  const t = state.translations;
  if (!t) return;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) {
      el.textContent = t[key];
    }
  });

  // Dynamic placeholders
  const searchInput = document.getElementById('scheme-search-input');
  if (searchInput && t['search_placeholder']) {
    searchInput.placeholder = t['search_placeholder'];
  }

  const chatInput = document.getElementById('chat-input');
  if (chatInput && t['chat_input_placeholder']) {
    chatInput.placeholder = t['chat_input_placeholder'];
  }
}

function getI18n(key, fallback = '') {
  return (state.translations && state.translations[key]) || fallback || key;
}

// =============================================================================
// TAB NAVIGATION
// =============================================================================

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-600');
  });

  const activeContent = document.getElementById(`tab-${tabId}`);
  const activeBtn = document.getElementById(`tab-btn-${tabId}`);

  if (activeContent) activeContent.classList.remove('hidden');
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-slate-600');
  }

  if (tabId === 'compare' && state.compareSelectedIds.length > 0) {
    updateComparisonView();
  }
}

// =============================================================================
// TAB 1: SCHEME EXPLORER
// =============================================================================

function populateCategoryFilters() {
  const catFilter = document.getElementById('scheme-cat-filter');
  const pillsContainer = document.getElementById('quick-category-pills');
  if (!catFilter || !pillsContainer) return;

  catFilter.innerHTML = `<option value="">All Categories</option>`;
  pillsContainer.innerHTML = '';

  state.categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    catFilter.appendChild(opt);

    // Pill
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = 'text-xs px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap transition';
    pill.textContent = cat;
    pill.onclick = () => {
      catFilter.value = cat;
      handleSchemeSearch();
    };
    pillsContainer.appendChild(pill);
  });
}

function populateMinistryFilters() {
  const minFilter = document.getElementById('scheme-min-filter');
  if (!minFilter) return;

  minFilter.innerHTML = `<option value="">All Ministries</option>`;
  state.ministries.forEach(min => {
    const opt = document.createElement('option');
    opt.value = min;
    opt.textContent = min;
    minFilter.appendChild(opt);
  });
}

let searchDebounceTimeout = null;
function handleSchemeSearch() {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    const searchVal = document.getElementById('scheme-search-input').value.trim();
    const catVal = document.getElementById('scheme-cat-filter').value;
    const minVal = document.getElementById('scheme-min-filter').value;

    const params = {};
    if (searchVal) params.search = searchVal;
    if (catVal) params.category = catVal;
    if (minVal) params.ministry = minVal;

    fetchSchemes(params);
  }, 200);
}

function updateSchemesCounter(count) {
  const el = document.getElementById('schemes-counter-text');
  if (el) {
    el.textContent = `Found ${count} Welfare Scheme${count === 1 ? '' : 's'}`;
  }
}

function renderSchemesGrid(schemesList) {
  const grid = document.getElementById('schemes-grid');
  if (!grid) return;

  if (schemesList.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12 bg-white rounded-xl border border-slate-200">
        <span class="text-4xl block mb-2">🔍</span>
        <h3 class="font-bold text-slate-800">No schemes found matching criteria</h3>
        <p class="text-xs text-slate-500 mt-1">Try clearing search terms or changing category filters.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = schemesList.map(scheme => {
    const title = (state.currentLang in (scheme.native_names || {})) 
      ? scheme.native_names[state.currentLang] 
      : scheme.name;

    const benefitBadge = scheme.financial_benefit_amount > 0 
      ? `<span class="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-200">₹${scheme.financial_benefit_amount.toLocaleString('en-IN')}/yr</span>`
      : `<span class="text-xs font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded-full">Subsidy / Aid</span>`;

    return `
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:shadow-md transition flex flex-col justify-between">
        <div>
          <div class="flex items-start justify-between gap-2 mb-2">
            <span class="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-md">${escapeHtml(scheme.category)}</span>
            ${benefitBadge}
          </div>

          <h3 class="font-bold text-slate-900 text-base leading-snug hover:text-blue-600 transition cursor-pointer" onclick="openSchemeModal('${scheme.id}')">
            ${escapeHtml(title)}
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">${escapeHtml(scheme.ministry)}</p>

          <p class="text-xs text-slate-600 mt-3 line-clamp-3 leading-relaxed">
            ${escapeHtml(scheme.description)}
          </p>

          <div class="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
            <span class="font-semibold text-slate-700">Documents needed:</span> ${scheme.required_documents.length} verified docs
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <button
            onclick="openSchemeModal('${scheme.id}')"
            class="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2.5 py-1.5 rounded-lg transition"
          >
            View Details & Rules
          </button>
          <a
            href="${scheme.official_portal_url}"
            target="_blank"
            rel="noopener noreferrer"
            class="text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 px-2.5 py-1.5 rounded-lg border border-slate-200 transition flex items-center space-x-1"
          >
            <span>Portal</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
          </a>
        </div>
      </div>
    `;
  }).join('');
}

// =============================================================================
// SCHEME DETAIL MODAL
// =============================================================================

function openSchemeModal(schemeId) {
  const scheme = (state.allSchemes && state.allSchemes.find(s => s.id === schemeId)) ||
                 state.schemes.find(s => s.id === schemeId);
  if (!scheme) return;

  const title = (state.currentLang in (scheme.native_names || {})) 
    ? scheme.native_names[state.currentLang] 
    : scheme.name;

  document.getElementById('modal-scheme-category').textContent = scheme.category;
  document.getElementById('modal-scheme-name').textContent = title;
  document.getElementById('modal-scheme-ministry').textContent = scheme.ministry;
  document.getElementById('modal-scheme-portal-link').href = scheme.official_portal_url;

  const helplineEl = document.getElementById('modal-scheme-helpline');
  helplineEl.textContent = scheme.helpline ? `📞 Helpline: ${scheme.helpline}` : '';

  const bodyEl = document.getElementById('modal-scheme-body');
  
  const docsList = scheme.required_documents.map(d => `<li class="flex items-start space-x-2"><span class="text-blue-500 font-bold">•</span><span>${escapeHtml(d)}</span></li>`).join('');

  const faqsHtml = (scheme.faqs && scheme.faqs.length > 0)
    ? `
      <div class="mt-4 pt-4 border-t border-slate-100">
        <h4 class="font-bold text-slate-800 mb-2">Frequently Asked Questions</h4>
        <div class="space-y-2">
          ${scheme.faqs.map(f => `
            <div class="p-3 bg-slate-50 rounded-lg border border-slate-200/60 text-xs">
              <p class="font-semibold text-slate-800">Q: ${escapeHtml(f.question)}</p>
              <p class="text-slate-600 mt-1">A: ${escapeHtml(f.answer)}</p>
            </div>
          `).join('')}
        </div>
      </div>
    `
    : '';

  bodyEl.innerHTML = `
    <div>
      <h4 class="font-bold text-slate-800 mb-1">Detailed Description</h4>
      <p class="text-slate-600 leading-relaxed text-xs sm:text-sm">${escapeHtml(scheme.description)}</p>
    </div>

    <div class="p-3 bg-blue-50/70 border border-blue-200/60 rounded-xl">
      <h4 class="font-bold text-blue-900 text-xs uppercase tracking-wider mb-1">Key Benefits & Financial Assistance</h4>
      <p class="text-blue-950 font-medium text-xs sm:text-sm">${escapeHtml(scheme.benefits)}</p>
      ${scheme.financial_benefit_amount > 0 ? `<p class="text-xs text-blue-700 font-bold mt-1">Estimated Direct Annual Benefit: ₹${scheme.financial_benefit_amount.toLocaleString('en-IN')}</p>` : ''}
    </div>

    <div>
      <h4 class="font-bold text-slate-800 mb-1">Target Beneficiary Demographic</h4>
      <p class="text-slate-600 text-xs">${escapeHtml(scheme.rules.target_beneficiaries || 'All eligible citizens fulfilling guidelines.')}</p>
    </div>

    <div>
      <h4 class="font-bold text-slate-800 mb-2">Mandatory Documents Checklist</h4>
      <ul class="text-xs space-y-1 text-slate-600">
        ${docsList}
      </ul>
    </div>

    ${faqsHtml}
  `;

  document.getElementById('scheme-modal').classList.remove('hidden');
}

function closeSchemeModal() {
  document.getElementById('scheme-modal').classList.add('hidden');
}

// =============================================================================
// TAB 2: ELIGIBILITY WIZARD
// =============================================================================

async function submitEligibility(event) {
  event.preventDefault();

  const profile = {
    age: parseInt(document.getElementById('p-age').value) || 0,
    gender: document.getElementById('p-gender').value,
    state: document.getElementById('p-state').value,
    annual_income: parseFloat(document.getElementById('p-income').value) || 0.0,
    occupation: document.getElementById('p-occupation').value,
    category: document.getElementById('p-category').value,
    is_student: document.getElementById('p-student').checked,
    is_differently_abled: document.getElementById('p-pwd').checked,
    landholding_hectares: parseFloat(document.getElementById('p-land').value) || 0.0,
    marital_status: "Single",
    has_bpl_card: document.getElementById('p-bpl').checked
  };

  state.lastProfile = profile;
  await runEligibilityEvaluation(profile);
}

async function runEligibilityEvaluation(profile) {
  const btn = document.getElementById('btn-evaluate-eligibility');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Evaluating rules deterministically...</span>`;

  try {
    const res = await fetch(`/api/eligibility/evaluate?lang=${state.currentLang}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });

    if (res.ok) {
      const data = await res.json();
      state.lastAuditResults = data.results;

      // Update KPI counters
      document.getElementById('kpi-total').textContent = data.stats.total_evaluated;
      document.getElementById('kpi-eligible').textContent = data.stats.eligible;
      document.getElementById('kpi-potential').textContent = data.stats.potentially_eligible;
      document.getElementById('kpi-ineligible').textContent = data.stats.ineligible;

      renderAuditResultsList(data.results);
      document.getElementById('eligibility-results-container').classList.remove('hidden');

      // Scroll smoothly to results
      document.getElementById('eligibility-results-container').scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    console.error("Evaluation error:", err);
    alert("Error evaluating eligibility. Please check backend connection.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function filterAuditStatus(statusFilter) {
  state.auditStatusFilter = statusFilter;
  
  ['all', 'eligible', 'potential'].forEach(id => {
    const el = document.getElementById(`audit-filter-${id}`);
    if (el) {
      el.className = 'px-2.5 py-1 rounded-md text-slate-600 hover:text-slate-900';
    }
  });

  const activeId = statusFilter === 'all' ? 'all' : (statusFilter === 'Eligible' ? 'eligible' : 'potential');
  const activeBtn = document.getElementById(`audit-filter-${activeId}`);
  if (activeBtn) {
    activeBtn.className = 'px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-xs font-semibold';
  }

  renderAuditResultsList(state.lastAuditResults);
}

function renderAuditResultsList(results) {
  const container = document.getElementById('audit-results-list');
  if (!container) return;

  let filtered = results;
  if (state.auditStatusFilter !== 'all') {
    filtered = results.filter(r => r.status === state.auditStatusFilter);
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
        No schemes match filter '${state.auditStatusFilter}'.
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map((res, idx) => {
    let badgeClass = 'badge-ineligible';
    let badgeText = getI18n('status_ineligible', 'Ineligible');

    if (res.status === 'Eligible') {
      badgeClass = 'badge-eligible';
      badgeText = getI18n('status_eligible', 'Eligible');
    } else if (res.status === 'Potentially Eligible') {
      badgeClass = 'badge-potential';
      badgeText = getI18n('status_potential', 'Conditional / Potential');
    }

    const metHtml = res.met_criteria.length > 0 
      ? res.met_criteria.map(m => `<li class="flex items-start space-x-1.5"><span class="text-emerald-600 font-bold">✓</span><span>${escapeHtml(m)}</span></li>`).join('')
      : '<li class="text-slate-400 italic">No specific rules passed.</li>';

    const condHtml = res.conditional_criteria.length > 0
      ? `
        <div class="mt-2">
          <span class="font-bold text-amber-800 text-xs block mb-1">⚠️ Verification Needed:</span>
          <ul class="space-y-1 text-amber-900 text-xs">
            ${res.conditional_criteria.map(c => `<li class="flex items-start space-x-1.5"><span class="text-amber-500 font-bold">•</span><span>${escapeHtml(c)}</span></li>`).join('')}
          </ul>
        </div>
      `
      : '';

    const unmetHtml = res.unmet_criteria.length > 0
      ? res.unmet_criteria.map(u => `<li class="flex items-start space-x-1.5"><span class="text-rose-600 font-bold">✗</span><span>${escapeHtml(u)}</span></li>`).join('')
      : '<li class="text-emerald-600 italic">None — all tested criteria satisfied.</li>';

    const docsHtml = res.required_documents.map(d => `<span class="inline-block bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs mr-1 mb-1">${escapeHtml(d)}</span>`).join('');

    return `
      <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-xs transition space-y-3">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h4 class="font-bold text-slate-900 text-base">${escapeHtml(res.scheme_name)}</h4>
            <p class="text-xs text-blue-700 font-semibold mt-0.5">${escapeHtml(res.estimated_benefit)}</p>
          </div>
          <span class="text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ${badgeClass}">
            ${escapeHtml(badgeText)} (${res.confidence_score}%)
          </span>
        </div>

        <p class="text-xs sm:text-sm text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
          ${escapeHtml(res.explanation)}
        </p>

        <!-- Collapsible Audit Breakdown -->
        <details class="text-xs group">
          <summary class="cursor-pointer font-semibold text-blue-600 hover:text-blue-800 select-none py-1 flex items-center space-x-1">
            <span>🔎 View Deterministic Audit Trail & Criteria</span>
          </summary>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pt-3 border-t border-slate-100">
            <!-- Left: Met & Conditional -->
            <div>
              <span class="font-bold text-emerald-800 text-xs block mb-1.5">✅ Satisfied Rules:</span>
              <ul class="space-y-1 text-slate-700 text-xs">
                ${metHtml}
              </ul>
              ${condHtml}
            </div>

            <!-- Right: Unmet & Documents -->
            <div>
              <span class="font-bold text-rose-800 text-xs block mb-1.5">❌ Roadblocks / Unmet Rules:</span>
              <ul class="space-y-1 text-slate-700 text-xs">
                ${unmetHtml}
              </ul>

              <div class="mt-3">
                <span class="font-bold text-slate-700 text-xs block mb-1">📄 Documents Required:</span>
                <div class="flex flex-wrap">
                  ${docsHtml}
                </div>
              </div>
            </div>
          </div>
        </details>

        <div class="flex items-center justify-end pt-2 border-t border-slate-100">
          <a
            href="${res.official_portal_url}"
            target="_blank"
            rel="noopener noreferrer"
            class="text-xs font-semibold text-blue-600 hover:underline flex items-center space-x-1"
          >
            <span>Apply on Official Portal</span>
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
          </a>
        </div>
      </div>
    `;
  }).join('');
}

async function downloadRoadmap() {
  if (!state.lastProfile) {
    alert("Please evaluate your eligibility first.");
    return;
  }

  const btn = document.getElementById('btn-download-roadmap');
  btn.disabled = true;
  btn.textContent = "Generating...";

  try {
    const res = await fetch('/api/eligibility/roadmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profile: state.lastProfile,
        lang: state.currentLang
      })
    });

    if (res.ok) {
      const data = await res.json();
      const blob = new Blob([data.content], { type: 'text/markdown;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename || 'CitizenSchemeAI_Action_Roadmap.md';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  } catch (err) {
    console.error("Roadmap generation failed:", err);
    alert("Failed to generate roadmap.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>📥</span><span>Download Action Roadmap (.md)</span>`;
  }
}

// =============================================================================
// TAB 3: AI CITIZEN ASSISTANT (RAG)
// =============================================================================

function askPresetQuery(queryText) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = queryText;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
  }
}

async function submitChatMessage(event) {
  event.preventDefault();
  const input = document.getElementById('chat-input');
  const query = input.value.trim();
  if (!query) return;

  // Clear input
  input.value = '';

  // Append user bubble
  appendChatBubble('user', query);

  // Show typing loader
  const loaderId = appendTypingLoader();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        lang: state.currentLang
      })
    });

    removeTypingLoader(loaderId);

    if (res.ok) {
      const data = await res.json();
      appendChatBubble('assistant', data.answer, data.citations);
    } else {
      appendChatBubble('assistant', "⚠️ System error while querying scheme knowledge base.");
    }
  } catch (err) {
    removeTypingLoader(loaderId);
    appendChatBubble('assistant', "⚠️ Failed to connect to server. Please ensure FastAPI server is running.");
  }
}

function appendChatBubble(role, text, citations = []) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;

  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'flex items-start space-x-3';

  if (role === 'user') {
    bubbleDiv.className = 'flex items-start justify-end space-x-3';
    bubbleDiv.innerHTML = `
      <div class="chat-bubble-user p-3.5 rounded-xl max-w-lg text-sm leading-relaxed shadow-xs">
        <p class="font-medium">${escapeHtml(text)}</p>
      </div>
      <div class="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shrink-0">
        You
      </div>
    `;
  } else {
    // Assistant formatting
    const formattedHtml = formatMarkdownResponse(text);

    let citationsHtml = '';
    if (citations && citations.length > 0) {
      citationsHtml = `
        <div class="mt-3 pt-3 border-t border-slate-200">
          <span class="text-xs font-bold text-slate-700 block mb-1.5">📚 Verified Source Citations:</span>
          <div class="space-y-1.5">
            ${citations.map(c => `
              <div class="p-2 bg-white rounded-lg border border-slate-200 text-xs flex items-center justify-between">
                <div>
                  <span class="font-semibold text-slate-800">${escapeHtml(c.scheme_name)}</span>
                  <span class="text-slate-400 mx-1">|</span>
                  <span class="text-slate-500">${escapeHtml(c.source)}</span>
                </div>
                <span class="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">${escapeHtml(c.relevance_score)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    bubbleDiv.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
        AI
      </div>
      <div class="chat-bubble-assistant p-4 rounded-xl max-w-2xl text-sm leading-relaxed shadow-xs">
        <div class="markdown-body">${formattedHtml}</div>
        ${citationsHtml}
      </div>
    `;
  }

  chatMessages.appendChild(bubbleDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingLoader() {
  const chatMessages = document.getElementById('chat-messages');
  const loaderId = 'loader-' + Date.now();
  const loaderDiv = document.createElement('div');
  loaderDiv.id = loaderId;
  loaderDiv.className = 'flex items-start space-x-3';
  loaderDiv.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
      AI
    </div>
    <div class="chat-bubble-assistant p-4 rounded-xl text-xs text-slate-500 flex items-center space-x-2">
      <span>Retrieving verified government scheme data</span>
      <div class="flex space-x-1">
        <div class="w-1.5 h-1.5 bg-blue-600 rounded-full loading-dot"></div>
        <div class="w-1.5 h-1.5 bg-blue-600 rounded-full loading-dot"></div>
        <div class="w-1.5 h-1.5 bg-blue-600 rounded-full loading-dot"></div>
      </div>
    </div>
  `;
  chatMessages.appendChild(loaderDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return loaderId;
}

function removeTypingLoader(loaderId) {
  const el = document.getElementById(loaderId);
  if (el) el.remove();
}

function clearChat() {
  const chatMessages = document.getElementById('chat-messages');
  if (chatMessages) {
    chatMessages.innerHTML = `
      <div class="flex items-start space-x-3">
        <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
          AI
        </div>
        <div class="chat-bubble-assistant p-4 rounded-xl max-w-2xl text-sm leading-relaxed">
          <p class="font-semibold text-slate-900 mb-1">Conversation cleared. How can I help you today?</p>
        </div>
      </div>
    `;
  }
}

// Simple fast markdown formatter for assistant answers
function formatMarkdownResponse(raw) {
  let text = escapeHtml(raw);

  // Headers: ### Header
  text = text.replace(/^### (.*$)/gim, '<h3 class="font-bold text-slate-900 text-base mt-2 mb-1">$1</h3>');
  
  // Bold: **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Bullet items: - item
  text = text.replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc text-xs sm:text-sm">$1</li>');

  // Links: [text](url)
  text = text.replace(/\[(.*?)\]\((https?:\/\/.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">$1</a>');

  // Line breaks
  text = text.replace(/\n\n/g, '<div class="h-2"></div>');
  text = text.replace(/\n/g, '<br/>');

  return text;
}

// =============================================================================
// TAB 4: SCHEME COMPARISON & BENEFIT ESTIMATOR
// =============================================================================

function initCompareSelections() {
  const container = document.getElementById('compare-selection-chips');
  if (!container) return;

  const schemePool = state.allSchemes.length > 0 ? state.allSchemes : state.schemes;
  if (state.compareSelectedIds.length === 0 && schemePool.length > 0) {
    state.compareSelectedIds = schemePool.slice(0, 2).map(s => s.id);
  }
  renderCompareChips();
  updateComparisonView();
}

function renderCompareChips() {
  const container = document.getElementById('compare-selection-chips');
  if (!container) return;

  const schemePool = state.allSchemes.length > 0 ? state.allSchemes : state.schemes;
  container.innerHTML = schemePool.map(s => {
    const isSelected = state.compareSelectedIds.includes(s.id);
    const badgeClass = isSelected 
      ? 'bg-blue-600 text-white border-blue-600 shadow-xs' 
      : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border-slate-200';

    const displayName = (state.currentLang in (s.native_names || {}))
      ? s.native_names[state.currentLang]
      : s.name;

    return `
      <button
        type="button"
        onclick="toggleCompareScheme('${s.id}')"
        class="text-xs px-3 py-1.5 rounded-full border transition font-medium flex items-center space-x-1.5 ${badgeClass}"
      >
        <span>${isSelected ? '✓' : '+'}</span>
        <span>${escapeHtml(displayName)}</span>
      </button>
    `;
  }).join('');
}

function toggleCompareScheme(schemeId) {
  if (state.compareSelectedIds.includes(schemeId)) {
    if (state.compareSelectedIds.length <= 1) {
      alert("Please keep at least 1 scheme selected for comparison.");
      return;
    }
    state.compareSelectedIds = state.compareSelectedIds.filter(id => id !== schemeId);
  } else {
    state.compareSelectedIds.push(schemeId);
  }

  renderCompareChips();
  updateComparisonView();
}

async function updateComparisonView() {
  if (state.compareSelectedIds.length === 0) return;

  try {
    const res = await fetch('/api/schemes/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheme_ids: state.compareSelectedIds })
    });

    if (res.ok) {
      const data = await res.json();
      
      // Update Benefit counter
      const benefitEl = document.getElementById('total-annual-benefit-display');
      if (benefitEl) {
        benefitEl.textContent = `₹${data.total_annual_benefit.toLocaleString('en-IN')} / year`;
      }

      // Render Matrix Table
      const tableBody = document.getElementById('compare-table-body');
      if (tableBody) {
        tableBody.innerHTML = data.schemes.map(s => {
          const displayName = (state.currentLang in (s.native_names || {}))
            ? s.native_names[state.currentLang]
            : s.name;

          return `
          <tr class="hover:bg-slate-50 transition">
            <td class="py-3 px-4 font-bold text-slate-900">${escapeHtml(displayName)}</td>
            <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-xs bg-slate-100 font-medium">${escapeHtml(s.category)}</span></td>
            <td class="py-3 px-4 text-xs text-slate-600">${escapeHtml(s.ministry)}</td>
            <td class="py-3 px-4 font-semibold text-emerald-700">₹${s.financial_benefit_amount.toLocaleString('en-IN')}</td>
            <td class="py-3 px-4 text-xs text-slate-600 max-w-xs">${escapeHtml(s.target_beneficiaries)}</td>
            <td class="py-3 px-4 text-xs font-medium text-slate-700">${s.max_annual_income ? '₹' + s.max_annual_income.toLocaleString('en-IN') : 'No Cap'}</td>
            <td class="py-3 px-4 text-xs font-semibold text-blue-700">${s.required_documents_count} documents</td>
            <td class="py-3 px-4">
              <a href="${s.official_portal_url}" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 hover:underline">Apply</a>
            </td>
          </tr>
        `;
        }).join('');
      }
    }
  } catch (err) {
    console.error("Comparison update failed:", err);
  }
}

// =============================================================================
// TAB 6: ADMIN SCHEME REGISTRATION
// =============================================================================

async function submitNewScheme(event) {
  event.preventDefault();
  const feedback = document.getElementById('adm-feedback');
  feedback.className = 'hidden';

  const docList = document.getElementById('adm-docs').value
    .split(',')
    .map(d => d.trim())
    .filter(Boolean);

  const payload = {
    id: document.getElementById('adm-id').value.trim(),
    name: document.getElementById('adm-name').value.trim(),
    category: document.getElementById('adm-category').value,
    ministry: document.getElementById('adm-ministry').value.trim(),
    description: document.getElementById('adm-desc').value.trim(),
    benefits: document.getElementById('adm-benefits').value.trim(),
    financial_benefit_amount: parseFloat(document.getElementById('adm-amount').value) || 0.0,
    official_portal_url: document.getElementById('adm-portal').value.trim(),
    required_documents: docList,
    rules: {
      target_beneficiaries: document.getElementById('adm-target').value.trim()
    }
  };

  const btn = document.getElementById('adm-submit-btn');
  btn.disabled = true;
  btn.textContent = "Registering...";

  try {
    const res = await fetch('/api/schemes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.success) {
      feedback.className = 'p-3 rounded-lg text-sm bg-emerald-50 text-emerald-800 border border-emerald-200 block';
      feedback.textContent = `🎉 ${data.message}`;
      
      // Reset form
      document.getElementById('admin-add-scheme-form').reset();
      
      // Refresh schemes and filters
      await fetchSchemes();
      await fetchCategories();
      await fetchMinistries();
      renderCompareChips();
    } else {
      feedback.className = 'p-3 rounded-lg text-sm bg-rose-50 text-rose-800 border border-rose-200 block';
      feedback.textContent = `Failed to add scheme: ${data.detail || data.message || 'Unknown error'}`;
    }
  } catch (err) {
    feedback.className = 'p-3 rounded-lg text-sm bg-rose-50 text-rose-800 border border-rose-200 block';
    feedback.textContent = "Network error registering scheme.";
  } finally {
    btn.disabled = false;
    btn.textContent = "Register & Re-index Scheme";
  }
}

// =============================================================================
// UTILITIES
// =============================================================================

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
