(() => {
  const pages = [...document.querySelectorAll('.deck-page')];
  const jump = document.querySelector('#jump');
  const previous = document.querySelector('#previous');
  const next = document.querySelector('#next');
  const status = document.querySelector('#status');
  const message = document.querySelector('#message');
  const overview = document.querySelector('#overview');
  const edit = document.querySelector('#edit');
  const notes = document.querySelector('#notes');
  const notePanel = document.querySelector('#notes-panel');
  const noteText = document.querySelector('#note-text');
  const blockSelector = 'h1,h2,h3,h4,h5,h6,p,li,dt,dd,figcaption,td,th,[data-editable]';
  const textSelector = `${blockSelector},span,small`;
  let current = 0;
  let touchStart = null;
  let editing = false;
  let presenter = null;
  let dirty = false;

  function titleOf(page) {
    return page?.querySelector('h1,h2')?.textContent.trim() || '幻灯片';
  }

  function updateTitles() {
    pages.forEach((page, index) => {
      jump.options[index].textContent = `${index + 1} · ${titleOf(page)}`;
    });
  }

  function syncPresenter() {
    if (!presenter || presenter.closed) return;
    const doc = presenter.document;
    doc.querySelector('#presenter-status').textContent = `${current + 1} / ${pages.length}`;
    doc.querySelector('#presenter-title').textContent = titleOf(pages[current]);
    doc.querySelector('#presenter-note').textContent = pages[current].dataset.note || '本页暂无备注';
    doc.querySelector('#presenter-next').textContent = current + 1 < pages.length
      ? `下一页：${titleOf(pages[current + 1])}` : '已到最后一页';
    doc.querySelector('#presenter-previous').disabled = current === 0;
    doc.querySelector('#presenter-forward').disabled = current === pages.length - 1;
  }

  function go(index) {
    if (!Number.isFinite(Number(index))) return;
    current = Math.max(0, Math.min(pages.length - 1, Math.trunc(Number(index))));
    const isOverview = document.body.classList.contains('overview');
    document.querySelectorAll('video').forEach(video => video.pause());
    pages.forEach((page, position) => {
      page.classList.toggle('active', position === current);
      page.setAttribute('aria-hidden', String(!isOverview && position !== current));
      page.inert = !isOverview && position !== current;
    });
    jump.value = String(current);
    previous.disabled = current === 0;
    next.disabled = current === pages.length - 1;
    status.textContent = `${current + 1} / ${pages.length}`;
    noteText.value = pages[current].dataset.note || '';
    window.deckPlayer.current = current;
    syncPresenter();
  }

  function toggleEditing(force) {
    editing = typeof force === 'boolean' ? force : !editing;
    if (editing && document.body.classList.contains('overview')) toggleOverview(false);
    document.body.classList.toggle('editing', editing);
    edit.setAttribute('aria-pressed', String(editing));
    edit.textContent = editing ? '结束改字' : '改字';
    pages.forEach(page => {
      page.querySelectorAll('[data-player-editable]').forEach(node => {
        node.removeAttribute('contenteditable');
        node.removeAttribute('data-player-editable');
      });
      if (!editing) return;
      page.querySelectorAll(`.slide :is(${textSelector})`).forEach(node => {
        if (!node.textContent.trim() || node.querySelector(blockSelector)) return;
        if (node.closest('svg,math,[data-no-edit],a,button,[contenteditable="false"],[data-player-editable]')) return;
        if (node.querySelector('svg,img,video,a,input,button,textarea')) return;
        node.setAttribute('contenteditable', 'plaintext-only');
        node.setAttribute('data-player-editable', '');
      });
    });
    if (!editing) document.activeElement?.blur();
    touchStart = null;
  }

  function toggleOverview(force) {
    const isOpen = typeof force === 'boolean' ? force : !document.body.classList.contains('overview');
    if (isOpen) toggleEditing(false);
    document.body.classList.toggle('overview', isOpen);
    overview.setAttribute('aria-pressed', String(isOpen));
    overview.textContent = isOpen ? '返回' : '总览';
    pages.forEach(page => {
      page.tabIndex = isOpen ? 0 : -1;
      if (isOpen) page.setAttribute('role', 'button');
      else page.removeAttribute('role');
    });
    go(current);
    if (!isOpen) window.scrollTo(0, 0);
  }

  function toggleNotes(force) {
    const isOpen = typeof force === 'boolean' ? force : notePanel.hidden;
    notePanel.hidden = !isOpen;
    notes.setAttribute('aria-expanded', String(isOpen));
    if (isOpen) noteText.focus();
    else notes.focus();
  }

  function openPresenter() {
    if (presenter && !presenter.closed) { presenter.focus(); return; }
    presenter = window.open('', '_blank', 'width=780,height=620');
    if (!presenter) {
      message.textContent = '演讲者窗口被拦截，请允许此页面弹出窗口。';
      return;
    }
    presenter.document.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
      <title>演讲备注</title><style>
      body{background:#11161d;color:#e7e9ed;font:18px/1.6 system-ui;padding:28px}
      pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;min-height:180px}
      button{font:inherit;padding:8px 18px;margin-right:12px}
      </style></head><body><p id="presenter-status"></p><h1 id="presenter-title"></h1>
      <pre id="presenter-note"></pre><p id="presenter-next"></p>
      <button id="presenter-previous">上一页</button><button id="presenter-forward">下一页</button>
      </body></html>`);
    presenter.document.close();
    presenter.document.querySelector('#presenter-previous').onclick = () => go(current - 1);
    presenter.document.querySelector('#presenter-forward').onclick = () => go(current + 1);
    syncPresenter();
  }

  function saveVersion() {
    try {
      const copy = document.documentElement.cloneNode(true);
      copy.querySelector('body').classList.remove('overview', 'editing');
      copy.querySelectorAll('[data-player-editable]').forEach(node => {
        node.removeAttribute('contenteditable');
        node.removeAttribute('data-player-editable');
      });
      copy.querySelectorAll('.deck-page').forEach((page, index) => {
        page.classList.toggle('active', index === 0);
        page.setAttribute('aria-hidden', String(index !== 0));
        page.toggleAttribute('inert', index !== 0);
        page.tabIndex = -1;
        page.removeAttribute('role');
      });
      copy.querySelector('#jump').replaceChildren();
      copy.querySelector('#note-text').value = '';
      copy.querySelector('#note-text').textContent = '';
      copy.querySelector('#notes-panel').hidden = true;
      copy.querySelector('#notes').setAttribute('aria-expanded', 'false');
      copy.querySelector('#edit').setAttribute('aria-pressed', 'false');
      copy.querySelector('#edit').textContent = '改字';
      copy.querySelector('#overview').setAttribute('aria-pressed', 'false');
      copy.querySelector('#overview').textContent = '总览';
      copy.querySelector('#message').textContent = '';
      const blob = new Blob(['<!doctype html>\n', copy.outerHTML], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const name = (document.title || '幻灯片').replace(/[\\/:*?"<>|\u0000-\u001f]/g, '-').slice(0, 80);
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      link.href = url;
      link.download = `${name}-${stamp}.html`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      dirty = false;
      message.textContent = '已发起下载，请确认新 HTML 已保存；原文件不会被覆盖。';
    } catch (error) {
      message.textContent = `保存失败：${error.message}`;
    }
  }

  async function toggleFullscreen() {
    try {
      if (!document.fullscreenEnabled) throw new Error('当前环境不支持全屏，请在浏览器打开 HTML。');
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
      message.textContent = '';
    } catch (error) {
      message.textContent = error.message || '无法进入全屏，请使用浏览器的全屏功能。';
    }
  }

  function handleKey(event) {
    const key = event.key.toLowerCase();
    if ((event.ctrlKey || event.metaKey) && key === 's') {
      event.preventDefault();
      saveVersion();
      return;
    }
    if (event.key === 'Escape') {
      if (!notePanel.hidden) toggleNotes(false);
      toggleEditing(false);
      toggleOverview(false);
      return;
    }
    if (event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.target.closest('input,select,button,textarea,video,[contenteditable]:not([contenteditable="false"])')) return;
    if (key === 'o') { toggleOverview(); return; }
    if (key === 'f') { toggleFullscreen(); return; }
    if (key === 'e') { toggleEditing(); return; }
    if (key === 'n') { toggleNotes(); return; }
    if (key === 's') { openPresenter(); return; }
    const forward = ['ArrowRight', 'ArrowDown', 'PageDown', ' '];
    const backward = ['ArrowLeft', 'ArrowUp', 'PageUp'];
    if (![...forward, ...backward, 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') go(0);
    else if (event.key === 'End') go(pages.length - 1);
    else go(current + (forward.includes(event.key) ? 1 : -1));
  }

  jump.replaceChildren();
  pages.forEach((page, index) => {
    jump.add(new Option(`${index + 1} · ${titleOf(page)}`, index));
    page.addEventListener('click', () => {
      if (!document.body.classList.contains('overview')) return;
      go(index);
      toggleOverview(false);
    });
    page.addEventListener('input', event => {
      if (!event.target.closest('[data-player-editable]')) return;
      dirty = true;
      updateTitles();
      syncPresenter();
    });
    page.addEventListener('keydown', event => {
      if (!document.body.classList.contains('overview') || !['Enter', ' '].includes(event.key)) return;
      event.preventDefault();
      event.stopPropagation();
      go(index);
      toggleOverview(false);
      overview.focus();
    });
  });

  previous.addEventListener('click', () => go(current - 1));
  next.addEventListener('click', () => go(current + 1));
  jump.addEventListener('change', () => go(jump.value));
  overview.addEventListener('click', () => toggleOverview());
  edit.addEventListener('click', () => toggleEditing());
  notes.addEventListener('click', () => toggleNotes());
  document.querySelector('#close-notes').addEventListener('click', () => toggleNotes(false));
  document.querySelector('#presenter').addEventListener('click', openPresenter);
  document.querySelector('#save').addEventListener('click', saveVersion);
  document.querySelector('#fullscreen').addEventListener('click', toggleFullscreen);
  noteText.addEventListener('input', () => {
    pages[current].dataset.note = noteText.value;
    dirty = true;
    syncPresenter();
  });
  document.addEventListener('keydown', handleKey);
  window.addEventListener('beforeunload', event => {
    if (!dirty) return;
    event.preventDefault();
    event.returnValue = '';
  });
  const deck = document.querySelector('.deck');
  deck.addEventListener('touchstart', event => {
    touchStart = null;
    if (editing || event.target.closest('video') || event.touches.length !== 1) return;
    touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
  }, { passive: true });
  deck.addEventListener('touchcancel', () => { touchStart = null; });
  deck.addEventListener('touchend', event => {
    if (!touchStart || !event.changedTouches.length || document.body.classList.contains('overview')) {
      touchStart = null;
      return;
    }
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) go(current + (dx < 0 ? 1 : -1));
  }, { passive: true });
  window.deckPlayer = { go, current, toggleOverview, toggleEditing, toggleNotes, saveVersion };
  toggleEditing(false);
  notePanel.hidden = true;
  notes.setAttribute('aria-expanded', 'false');
  toggleOverview(false);
})();
