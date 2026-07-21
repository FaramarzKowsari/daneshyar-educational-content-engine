(() => {
  const bookId = window.DANESHYAR_BOOK_ID;
  if (!bookId) return;
  const chapterSelect = document.querySelector('#chapter-select');
  const output = document.querySelector('#generated-output');
  const mode = document.querySelector('#generation-mode');
  const slidesChapter = document.querySelector('#slides-chapter');

  chapterSelect?.addEventListener('change', () => { if (slidesChapter) slidesChapter.value = chapterSelect.value; });

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  function renderContent(content) {
    if (typeof content === 'string') return `<div>${escapeHtml(content).replace(/\n/g, '<br>')}</div>`;
    return `<pre>${escapeHtml(JSON.stringify(content, null, 2))}</pre>`;
  }

  document.querySelectorAll('[data-generate]').forEach(button => {
    button.addEventListener('click', async () => {
      const type = button.dataset.generate;
      button.disabled = true;
      output.textContent = 'در حال تولید...';
      mode.textContent = '';
      try {
        const response = await fetch(`/api/books/${bookId}/generate/${type}`, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({chapter: chapterSelect.value || null, count: 8})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'خطا در تولید محتوا');
        output.innerHTML = `<h3>${escapeHtml(data.title)}</h3>${renderContent(data.content)}`;
        mode.textContent = `ذخیره شد · ${data.status}`;
      } catch (error) {
        output.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  });

  const chatForm = document.querySelector('#chat-form');
  const chatOutput = document.querySelector('#chat-output');
  chatForm?.addEventListener('submit', async event => {
    event.preventDefault();
    const questionEl = document.querySelector('#question');
    const question = questionEl.value.trim();
    if (!question) return;
    chatOutput.insertAdjacentHTML('beforeend', `<div class="user-message">${escapeHtml(question)}</div>`);
    questionEl.value = '';
    const waiting = document.createElement('div');
    waiting.className = 'assistant-message';
    waiting.textContent = 'در حال جست‌وجو در کتاب...';
    chatOutput.appendChild(waiting);
    chatOutput.scrollTop = chatOutput.scrollHeight;
    try {
      const response = await fetch(`/api/books/${bookId}/chat`, {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({question})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'خطا در پاسخ‌گویی');
      const citations = data.citations.map(c => `<div class="citation"><b>صفحه ${c.page_start}</b> · ${escapeHtml(c.chapter)}<br>${escapeHtml(c.excerpt)}…</div>`).join('');
      waiting.innerHTML = `<div>${escapeHtml(data.answer).replace(/\n/g,'<br>')}</div><div class="citation-list">${citations}</div><small>حالت: ${escapeHtml(data.mode)}</small>`;
    } catch (error) {
      waiting.textContent = error.message;
    }
  });

  document.addEventListener('click', async event => {
    const view = event.target.closest('.view-asset');
    if (view) {
      const response = await fetch(`/api/assets/${view.dataset.id}`);
      const data = await response.json();
      output.innerHTML = `<h3>${escapeHtml(data.title)}</h3>${renderContent(data.content)}`;
      output.scrollIntoView({behavior:'smooth'});
    }
    const approve = event.target.closest('.approve-asset');
    if (approve) {
      const response = await fetch(`/api/assets/${approve.dataset.id}/approve`, {method:'POST'});
      if (response.ok) {
        const row = approve.closest('.asset-row');
        const status = row.querySelector('.status');
        status.textContent = 'approved';
        status.classList.remove('draft');
        status.classList.add('approved');
        approve.remove();
      }
    }
  });
})();
