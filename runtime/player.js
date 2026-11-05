(() => {
  const pages = [...document.querySelectorAll('.deck-page')];
  const jump = document.querySelector('#jump');
  const previous = document.querySelector('#previous');
  const next = document.querySelector('#next');
  const status = document.querySelector('#status');
  const message = document.querySelector('#message');
  const overview = document.querySelector('#overview');
  let current = 0;
  let touchStart = null;

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
    window.deckPlayer.current = current;
  }

  function toggleOverview(force) {
    const isOpen = typeof force === 'boolean' ? force : !document.body.classList.contains('overview');
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
    if (event.target.closest('input, select, button, textarea, video, [contenteditable="true"]')) return;
    if (event.key === 'Escape') { toggleOverview(false); return; }
    if (event.key.toLowerCase() === 'o') { toggleOverview(); return; }
    if (event.key.toLowerCase() === 'f') { toggleFullscreen(); return; }
    const forward = ['ArrowRight', 'ArrowDown', 'PageDown', ' '];
    const backward = ['ArrowLeft', 'ArrowUp', 'PageUp'];
    if (![...forward, ...backward, 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') go(0);
    else if (event.key === 'End') go(pages.length - 1);
    else go(current + (forward.includes(event.key) ? 1 : -1));
  }

  pages.forEach((page, index) => {
    const option = new Option(`${index + 1} · ${page.querySelector('h1,h2')?.textContent || '幻灯片'}`, index);
    jump.add(option);
    page.addEventListener('click', () => {
      if (!document.body.classList.contains('overview')) return;
      go(index);
      toggleOverview(false);
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
  document.querySelector('#fullscreen').addEventListener('click', toggleFullscreen);
  document.addEventListener('keydown', handleKey);
  document.querySelector('.deck').addEventListener('touchstart', event => {
    if (event.target.closest('video') || event.touches.length !== 1) return;
    touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
  }, { passive: true });
  document.querySelector('.deck').addEventListener('touchend', event => {
    if (!touchStart || document.body.classList.contains('overview')) { touchStart = null; return; }
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) go(current + (dx < 0 ? 1 : -1));
  }, { passive: true });
  window.deckPlayer = { go, current, toggleOverview };
  go(0);
})();
