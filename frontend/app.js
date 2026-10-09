/**
 * Academic Document Retrieval Agent - Frontend Application Logic
 * Implements interactive QA, Document Ingestion, Chunk Inspection,
 * Benchmark Runner, Theme Toggle, and Markdown rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    documents: [],
    chunks: [],
    stats: {},
    settings: {
      gemini_configured: false,
      model_name: 'gemini-2.5-flash',
      semantic_weight: 0.55,
      top_k: 5
    },
    activeTab: 'tab-qa',
    theme: localStorage.getItem('agent-theme') || 'theme-dark'
  };

  // Initialize theme
  document.body.className = state.theme;
  updateThemeIcon();

  // Initialize UI & Event Listeners
  initNavigation();
  initThemeToggle();
  initQAConsole();
  initDocumentHub();
  initChunkExplorer();
  initTestSuite();
  initSettings();

  // Load initial data from API
  fetchStats();
  fetchDocuments();
  fetchChunks();
  fetchTestCases();
  fetchSettings();

  // =========================================================================
  // THEME TOGGLE
  // =========================================================================
  function initThemeToggle() {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;

    btn.addEventListener('click', () => {
      state.theme = state.theme === 'theme-dark' ? 'theme-light' : 'theme-dark';
      document.body.className = state.theme;
      localStorage.setItem('agent-theme', state.theme);
      updateThemeIcon();
    });
  }

  function updateThemeIcon() {
    const sun = document.getElementById('themeIconSun');
    const moon = document.getElementById('themeIconMoon');
    if (!sun || !moon) return;

    if (state.theme === 'theme-light') {
      sun.classList.remove('hidden');
      moon.classList.add('hidden');
    } else {
      sun.classList.add('hidden');
      moon.classList.remove('hidden');
    }
  }

  // =========================================================================
  // NAVIGATION TABS
  // =========================================================================
  function initNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.tab;
        tabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const targetPanel = document.getElementById(targetId);
        if (targetPanel) targetPanel.classList.add('active');
        state.activeTab = targetId;

        // Auto-refresh data on tab switch
        if (targetId === 'tab-chunks') renderChunksExplorer();
        if (targetId === 'tab-docs') fetchDocuments();
      });
    });
  }

  // =========================================================================
  // API CLIENT FUNCTIONS
  // =========================================================================
  async function fetchStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      state.stats = data;

      // Update header indicators
      const statusText = document.getElementById('agentStatusText');
      if (statusText) {
        statusText.textContent = data.gemini_configured ? 'Gemini 2.5 Active' : 'Local Reasoning Engine';
      }

      const docCountEl = document.getElementById('headerDocCount');
      const chunkCountEl = document.getElementById('headerChunkCount');
      if (docCountEl) docCountEl.textContent = `${data.total_documents} Docs`;
      if (chunkCountEl) chunkCountEl.textContent = `${data.total_chunks} Chunks`;
    } catch (err) {
      console.error('[API] fetchStats error:', err);
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch('/api/documents');
      const data = await res.json();
      state.documents = data.documents || [];
      renderDocumentsTable();
      updateChunkDocFilter();
    } catch (err) {
      console.error('[API] fetchDocuments error:', err);
    }
  }

  async function fetchChunks() {
    try {
      const res = await fetch('/api/chunks?limit=150');
      const data = await res.json();
      state.chunks = data.chunks || [];
      renderChunksExplorer();
    } catch (err) {
      console.error('[API] fetchChunks error:', err);
    }
  }

  async function fetchSettings() {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      state.settings = data;
      
      const slider = document.getElementById('semanticWeightSlider');
      const topKSelect = document.getElementById('settingsTopK');
      const modelSelect = document.getElementById('geminiModelSelect');

      if (slider && data.semantic_weight !== undefined) {
        slider.value = data.semantic_weight;
        updateSliderLabel(data.semantic_weight);
      }
      if (topKSelect && data.top_k) topKSelect.value = data.top_k;
      if (modelSelect && data.model_name) modelSelect.value = data.model_name;
    } catch (err) {
      console.error('[API] fetchSettings error:', err);
    }
  }

  // =========================================================================
  // TAB 1: ACADEMIC QA CONSOLE
  // =========================================================================
  function initQAConsole() {
    const qaForm = document.getElementById('qaForm');
    const queryInput = document.getElementById('queryInput');
    const clearBtn = document.getElementById('clearQueryBtn');
    const promptChips = document.querySelectorAll('.prompt-chip');
    const toggleValidationBtn = document.getElementById('toggleValidationBtn');

    // Prompt Chips click
    promptChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const q = chip.dataset.query;
        if (queryInput) {
          queryInput.value = q;
          queryInput.focus();
          submitQuery(q);
        }
      });
    });

    // Clear Button
    if (clearBtn && queryInput) {
      clearBtn.addEventListener('click', () => {
        queryInput.value = '';
        queryInput.focus();
      });
    }

    // Form submit
    if (qaForm) {
      qaForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = queryInput.value.trim();
        if (q) submitQuery(q);
      });
    }

    // Keyboard shortcut: Ctrl+Enter or Cmd+Enter to submit
    if (queryInput) {
      queryInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
          e.preventDefault();
          const q = queryInput.value.trim();
          if (q) submitQuery(q);
        }
      });
    }

    // Validation breakdown accordion toggle
    if (toggleValidationBtn) {
      toggleValidationBtn.addEventListener('click', () => {
        const content = document.getElementById('validationContent');
        if (content) {
          content.classList.toggle('hidden');
          toggleValidationBtn.classList.toggle('open');
        }
      });
    }
  }

  async function submitQuery(query) {
    const loadingState = document.getElementById('queryLoadingState');
    const resultsContainer = document.getElementById('resultsContainer');
    const docTypeFilter = document.getElementById('filterDocType')?.value || 'all';
    const topK = parseInt(document.getElementById('queryTopK')?.value || '5');
    const submitBtn = document.getElementById('askSubmitBtn');

    if (loadingState) loadingState.classList.remove('hidden');
    if (resultsContainer) resultsContainer.classList.add('hidden');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const payload = {
        query: query,
        top_k: topK,
        doc_type_filter: docTypeFilter,
        semantic_weight: state.settings.semantic_weight || 0.55
      };

      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      renderQueryResults(data);
    } catch (err) {
      console.error('[QA] Query error:', err);
      alert(`Query failed: ${err.message}`);
    } finally {
      if (loadingState) loadingState.classList.add('hidden');
      if (resultsContainer) resultsContainer.classList.remove('hidden');
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  function renderQueryResults(data) {
    // 1. Conflict & Selection Alert Banner
    const banner = document.getElementById('conflictAlertBanner');
    const bannerTitle = document.getElementById('conflictAlertTitle');
    const bannerDesc = document.getElementById('conflictAlertDesc');

    if (data.is_out_of_corpus) {
      banner.className = 'alert-banner alert-warning';
      bannerTitle.textContent = '🛡️ Safe Refusal Guardrail Triggered';
      bannerDesc.textContent = 'The query topic was verified to be outside the uploaded university documents. The agent explicitly declined to hallucinate unsupported information.';
    } else if (data.conflict_report && data.conflict_report.has_conflict) {
      banner.className = 'alert-banner alert-warning';
      const c = data.conflict_report.conflicts[0];
      bannerTitle.textContent = `🔄 Regulatory Precedence: ${c.topic}`;
      bannerDesc.innerHTML = `<strong>Conflict Detected:</strong> ${c.issue}<br/><strong>Resolution:</strong> ${c.resolution}`;
    } else {
      banner.className = 'alert-banner alert-success';
      bannerTitle.textContent = '✅ Verified Academic Source Selection';
      bannerDesc.textContent = 'All facts and rules retrieved are supported by current authoritative documents without regulatory conflict.';
    }

    // 2. Engine and Groundedness Badge
    const engineTag = document.getElementById('answerEngineTag');
    if (engineTag) engineTag.textContent = `Engine: ${data.engine_used}`;

    const scoreVal = document.getElementById('groundednessScoreVal');
    const scoreLabel = document.getElementById('groundednessScoreLabel');
    const groundednessBadge = document.getElementById('groundednessBadge');

    const score = data.validation ? data.validation.groundedness_score : 100;
    const confLevel = data.validation ? data.validation.confidence_level : 'Verified';

    if (scoreVal) scoreVal.textContent = `${score}%`;
    if (scoreLabel) scoreLabel.textContent = confLevel;

    // 3. Render Answer Markdown
    const answerContent = document.getElementById('answerContent');
    if (answerContent) {
      answerContent.innerHTML = renderMarkdown(data.answer);
    }

    // 4. Render Claim-by-Claim Validation
    const claimCountSpan = document.getElementById('claimCountSpan');
    const claimsContainer = document.getElementById('claimsListContainer');
    if (data.validation && data.validation.claim_evaluations) {
      const claims = data.validation.claim_evaluations;
      if (claimCountSpan) claimCountSpan.textContent = claims.length;
      if (claimsContainer) {
        claimsContainer.innerHTML = claims.map(c => `
          <div class="claim-item">
            <div class="claim-header">
              <strong>${escapeHtml(c.claim_text)}</strong>
              <span class="claim-badge ${c.status === 'VERIFIED' || c.status === 'VERIFIED_DECLINE' ? 'claim-verified' : (c.status === 'PARTIALLY_SUPPORTED' ? 'claim-partial' : 'claim-unverified')}">
                ${c.status} (${Math.round((c.confidence || 1) * 100)}%)
              </span>
            </div>
            <div class="claim-source-text">Source: ${escapeHtml(c.matched_source || 'Context Match')}</div>
            ${c.matched_quote ? `<div class="claim-quote">"${escapeHtml(c.matched_quote)}"</div>` : ''}
          </div>
        `).join('');
      }
    }

    // 5. Render Source Citations
    const citationCountSpan = document.getElementById('citationCountSpan');
    const citationsGrid = document.getElementById('citationsGrid');
    if (data.citations) {
      if (citationCountSpan) citationCountSpan.textContent = data.citations.length;
      if (citationsGrid) {
        citationsGrid.innerHTML = data.citations.map((c, i) => `
          <div class="citation-card">
            <div class="citation-top">
              <span class="citation-doc-name">${escapeHtml(c.document_name)}</span>
              <span class="citation-page-badge">Page ${c.page_number}</span>
            </div>
            <div class="citation-meta">
              <span>Section: ${escapeHtml(c.section_title || 'General')}</span>
              <span>Effective: ${escapeHtml(c.effective_date || 'Current')}</span>
            </div>
            <div class="citation-quote">"${escapeHtml(c.quote_snippet)}"</div>
          </div>
        `).join('');
      }
    }

    // 6. Render Retrieved Chunks & Scoring Metrics
    const chunksWrapper = document.getElementById('chunksTableWrapper');
    if (chunksWrapper && data.retrieved_chunks) {
      chunksWrapper.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Document</th>
              <th>Page</th>
              <th>Hybrid Score</th>
              <th>BM25 (Keyword)</th>
              <th>Semantic (Dense)</th>
              <th>Authority Multiplier</th>
              <th>Recency Multiplier</th>
            </tr>
          </thead>
          <tbody>
            ${data.retrieved_chunks.map((chunk, i) => {
              const rm = chunk.retrieval_metrics || {};
              const se = chunk.source_evaluation || {};
              return `
                <tr>
                  <td><strong>#${i + 1}</strong></td>
                  <td>${escapeHtml(chunk.document_name)}</td>
                  <td>Page ${chunk.page_number}</td>
                  <td><strong style="color:var(--accent-primary)">${rm.hybrid_score || 'N/A'}</strong></td>
                  <td>${rm.bm25_score || 'N/A'}</td>
                  <td>${rm.semantic_score || 'N/A'}</td>
                  <td>${se.authority_weight ? se.authority_weight + 'x' : '1.0x'}</td>
                  <td>${se.recency_multiplier ? se.recency_multiplier + 'x' : '1.0x'}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;
    }
  }

  // =========================================================================
  // TAB 2: DOCUMENT HUB & INGESTION
  // =========================================================================
  function initDocumentHub() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectedFileInfo = document.getElementById('selectedFileInfo');
    const selectedFileName = document.getElementById('selectedFileName');
    const clearFileBtn = document.getElementById('clearFileBtn');
    const uploadForm = document.getElementById('uploadForm');
    const resetSampleBtn = document.getElementById('resetSampleCorpusBtn');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileSelect(fileInput.files[0]);
      }
    });

    if (clearFileBtn) {
      clearFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        selectedFileInfo.classList.add('hidden');
      });
    }

    function handleFileSelect(file) {
      if (!file) return;
      selectedFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      selectedFileInfo.classList.remove('hidden');
    }

    // Upload Form Submit
    if (uploadForm) {
      uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files || fileInput.files.length === 0) {
          alert('Please select a file to upload.');
          return;
        }

        const formData = new FormData(uploadForm);
        const submitBtn = document.getElementById('uploadSubmitBtn');
        if (submitBtn) submitBtn.disabled = true;

        try {
          const res = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
          });
          const result = await res.json();
          if (res.ok) {
            alert(result.message);
            uploadForm.reset();
            selectedFileInfo.classList.add('hidden');
            fetchDocuments();
            fetchChunks();
            fetchStats();
          } else {
            alert(`Upload error: ${result.error || 'Failed to upload'}`);
          }
        } catch (err) {
          console.error('[Upload] Error:', err);
          alert(`Upload failed: ${err.message}`);
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      });
    }

    // Reset Sample Corpus
    if (resetSampleBtn) {
      resetSampleBtn.addEventListener('click', async () => {
        if (!confirm('Reload the 5 official sample academic documents? Custom uploads will be cleared.')) return;
        try {
          const res = await fetch('/api/documents/reset-sample', { method: 'POST' });
          const result = await res.json();
          alert(result.message);
          fetchDocuments();
          fetchChunks();
          fetchStats();
        } catch (err) {
          alert(`Reset failed: ${err.message}`);
        }
      });
    }
  }

  function renderDocumentsTable() {
    const tbody = document.getElementById('documentsTableBody');
    const totalDocsCount = document.getElementById('totalDocsCount');
    if (!tbody) return;

    if (totalDocsCount) totalDocsCount.textContent = state.documents.length;

    if (state.documents.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center p-4">No documents indexed. Upload files or click "Reload Sample Corpus".</td></tr>`;
      return;
    }

    tbody.innerHTML = state.documents.map(doc => {
      const badgeClass = doc.format === 'PDF' ? 'doc-badge-pdf' : (doc.format === 'DOCX' ? 'doc-badge-docx' : 'doc-badge-txt');
      return `
        <tr>
          <td>
            <strong>${escapeHtml(doc.document_name)}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(doc.authority || 'Academic Council')}</div>
          </td>
          <td><span class="doc-badge ${badgeClass}">${doc.doc_type || 'General'}</span></td>
          <td>${escapeHtml(doc.academic_year || 'Current')}</td>
          <td>${escapeHtml(doc.effective_date || 'N/A')}</td>
          <td>${doc.total_pages || 1}</td>
          <td><strong>${doc.total_chunks || 0}</strong></td>
          <td>
            <button class="btn-delete" data-doc-id="${doc.doc_id}" title="Remove Document">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach delete listeners
    tbody.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const docId = btn.dataset.docId;
        if (!confirm('Are you sure you want to delete this document?')) return;
        try {
          const res = await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
          if (res.ok) {
            fetchDocuments();
            fetchChunks();
            fetchStats();
          }
        } catch (err) {
          alert(`Delete failed: ${err.message}`);
        }
      });
    });
  }

  function updateChunkDocFilter() {
    const sel = document.getElementById('chunkDocFilter');
    if (!sel) return;
    sel.innerHTML = `<option value="">All Documents (${state.documents.length})</option>` +
      state.documents.map(d => `<option value="${d.doc_id}">${escapeHtml(d.document_name)}</option>`).join('');
  }

  // =========================================================================
  // TAB 3: CHUNK EXPLORER
  // =========================================================================
  function initChunkExplorer() {
    const searchInput = document.getElementById('chunkSearchInput');
    const docFilter = document.getElementById('chunkDocFilter');

    if (searchInput) {
      searchInput.addEventListener('input', () => renderChunksExplorer());
    }
    if (docFilter) {
      docFilter.addEventListener('change', () => renderChunksExplorer());
    }
  }

  function renderChunksExplorer() {
    const grid = document.getElementById('chunkExplorerGrid');
    const searchVal = document.getElementById('chunkSearchInput')?.value.toLowerCase() || '';
    const docIdFilter = document.getElementById('chunkDocFilter')?.value || '';
    if (!grid) return;

    let filtered = state.chunks;
    if (docIdFilter) {
      filtered = filtered.filter(c => c.doc_id === docIdFilter);
    }
    if (searchVal) {
      filtered = filtered.filter(c => c.text.toLowerCase().includes(searchVal) || (c.section_title || '').toLowerCase().includes(searchVal));
    }

    if (filtered.length === 0) {
      grid.innerHTML = `<div class="text-center p-4" style="grid-column: 1 / -1;">No matching chunks found.</div>`;
      return;
    }

    grid.innerHTML = filtered.map(c => `
      <div class="chunk-card">
        <div class="chunk-top-meta">
          <span>${escapeHtml(c.document_name)}</span>
          <span>Page ${c.page_number} • ${c.char_count} chars</span>
        </div>
        <div class="chunk-section-title">${escapeHtml(c.section_title || 'General Section')}</div>
        <div class="chunk-body">${escapeHtml(c.text)}</div>
      </div>
    `).join('');
  }

  // =========================================================================
  // TAB 4: AUTOMATED TEST SUITE RUNNER
  // =========================================================================
  async function fetchTestCases() {
    try {
      const res = await fetch('/api/test-cases');
      const data = await res.json();
      renderTestCasesList(data.test_cases || []);
    } catch (err) {
      console.error('[TestCases] Error:', err);
    }
  }

  function initTestSuite() {
    const runBtn = document.getElementById('runAllTestsBtn');
    if (!runBtn) return;

    runBtn.addEventListener('click', async () => {
      runBtn.disabled = true;
      runBtn.innerHTML = `<span>Running Benchmarks...</span>`;
      const summaryBar = document.getElementById('benchmarkSummaryBar');

      try {
        const res = await fetch('/api/run-test-cases', { method: 'POST' });
        const data = await res.json();
        
        if (summaryBar) {
          summaryBar.classList.remove('hidden');
          const passCount = data.results.filter(r => r.passed).length;
          document.getElementById('testPassCount').textContent = `${passCount} / ${data.results.length}`;
          document.getElementById('testAvgGroundedness').textContent = `${data.average_groundedness}%`;
        }

        renderTestResults(data.results);
      } catch (err) {
        alert(`Test execution failed: ${err.message}`);
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Run Automated Benchmark</span>`;
      }
    });
  }

  function renderTestCasesList(cases) {
    const container = document.getElementById('testCasesContainer');
    if (!container) return;

    container.innerHTML = cases.map((tc, idx) => `
      <div class="test-case-card" id="tc-card-${tc.id}">
        <div class="test-case-top">
          <div>
            <div class="test-case-category">${escapeHtml(tc.category)}</div>
            <div class="test-case-title">Test ${idx + 1}: ${escapeHtml(tc.question)}</div>
          </div>
          <span class="test-status-pill" id="tc-status-${tc.id}">Pending</span>
        </div>
        <div class="test-case-details">
          <strong>Expected Evaluation:</strong> ${escapeHtml(tc.expected_focus)}<br/>
          <strong>Target Source:</strong> <code>${escapeHtml(tc.target_document)}</code>
        </div>
      </div>
    `).join('');
  }

  function renderTestResults(results) {
    results.forEach(r => {
      const tc = r.test_case;
      const card = document.getElementById(`tc-card-${tc.id}`);
      const statusPill = document.getElementById(`tc-status-${tc.id}`);

      if (card && statusPill) {
        card.className = `test-case-card ${r.passed ? 'passed' : 'failed'}`;
        statusPill.className = `test-status-pill ${r.passed ? 'pass' : 'fail'}`;
        statusPill.textContent = r.passed ? `PASSED (${r.groundedness_score}%)` : `FAILED (${r.groundedness_score}%)`;

        // Append live answer details if not already present
        let detailsBlock = card.querySelector('.test-result-block');
        if (!detailsBlock) {
          detailsBlock = document.createElement('div');
          detailsBlock.className = 'test-result-block';
          card.appendChild(detailsBlock);
        }
        detailsBlock.innerHTML = `
          <div style="margin-top:8px; padding-top:8px; border-top:1px solid var(--border-color); font-size:0.82rem;">
            <strong>Result Preview:</strong> <em>${escapeHtml(r.answer_preview)}</em>
            <div style="margin-top:4px; color:var(--text-muted);">Notes: ${escapeHtml(r.notes.join(' • '))}</div>
          </div>
        `;
      }
    });
  }

  // =========================================================================
  // TAB 5: AGENT SETTINGS
  // =========================================================================
  function initSettings() {
    const form = document.getElementById('settingsForm');
    const slider = document.getElementById('semanticWeightSlider');
    const toggleKeyBtn = document.getElementById('toggleKeyVisibility');
    const keyInput = document.getElementById('geminiApiKey');

    if (slider) {
      slider.addEventListener('input', () => {
        updateSliderLabel(slider.value);
      });
    }

    if (toggleKeyBtn && keyInput) {
      toggleKeyBtn.addEventListener('click', () => {
        keyInput.type = keyInput.type === 'password' ? 'text' : 'password';
        toggleKeyBtn.textContent = keyInput.type === 'password' ? 'Show' : 'Hide';
      });
    }

    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const saveMsg = document.getElementById('settingsSaveMsg');
        const apiKey = document.getElementById('geminiApiKey')?.value;
        const modelName = document.getElementById('geminiModelSelect')?.value;
        const semanticWeight = parseFloat(slider?.value || '0.55');
        const topK = parseInt(document.getElementById('settingsTopK')?.value || '5');

        try {
          const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              api_key: apiKey,
              model_name: modelName,
              semantic_weight: semanticWeight,
              top_k: topK
            })
          });
          const result = await res.json();
          if (saveMsg) {
            saveMsg.textContent = 'Settings saved successfully!';
            saveMsg.style.color = 'var(--success)';
            setTimeout(() => { saveMsg.textContent = ''; }, 3000);
          }
          fetchStats();
        } catch (err) {
          if (saveMsg) {
            saveMsg.textContent = `Error: ${err.message}`;
            saveMsg.style.color = 'var(--danger)';
          }
        }
      });
    }
  }

  function updateSliderLabel(val) {
    const lbl = document.getElementById('semanticWeightVal');
    if (!lbl) return;
    const sem = Math.round(parseFloat(val) * 100);
    const bm = 100 - sem;
    lbl.textContent = `${sem}% Dense Semantic / ${bm}% BM25 Keyword`;
  }

  // =========================================================================
  // HELPER UTILITIES: Lightweight Markdown Parser & HTML Escaping
  // =========================================================================
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderMarkdown(md) {
    if (!md) return '';
    let html = escapeHtml(md);

    // Blockquotes: > quote
    html = html.replace(/^&gt;\s+(.*$)/gim, '<blockquote>$1</blockquote>');

    // Headers: ###, ##, #
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold & Italics
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Citations [Doc, Page X]
    html = html.replace(/\[([^\]]+)\]/g, '<span style="color:var(--accent-primary); font-weight:600;">[$1]</span>');

    // Unordered Lists
    html = html.replace(/^\s*[-*•]\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/gm, '<ul>$1</ul>');
    // Remove nested duplicate uls
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // Ordered Lists
    html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<li>$2</li>');

    // Line breaks to paragraphs
    const paragraphs = html.split(/\n\s*\n/);
    return paragraphs.map(p => {
      p = p.trim();
      if (!p) return '';
      if (p.startsWith('<h3>') || p.startsWith('<h2>') || p.startsWith('<h1>') || p.startsWith('<ul>') || p.startsWith('<blockquote>')) {
        return p;
      }
      return `<p>${p.replace(/\n/g, '<br/>')}</p>`;
    }).join('');
  }
});
