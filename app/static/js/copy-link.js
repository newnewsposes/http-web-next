// Global copyShareLink function with small tooltip animation
function createTooltip(text, target) {
  const tip = document.createElement('div');
  tip.className = 'copy-tooltip';
  tip.textContent = text;
  document.body.appendChild(tip);

  // Position near target (fallback to bottom-right)
  requestAnimationFrame(() => {
    if (target) {
      const rect = target.getBoundingClientRect();
      tip.style.left = `${Math.max(8, rect.left + rect.width/2 - tip.offsetWidth/2)}px`;
      tip.style.top = `${Math.max(8, rect.top - 10 - tip.offsetHeight)}px`;
    } else {
      tip.style.right = '2rem';
      tip.style.bottom = '6rem';
    }
    tip.classList.add('visible');
  });

  // remove after timeout
  setTimeout(() => {
    tip.classList.remove('visible');
    setTimeout(() => tip.remove(), 300);
  }, 1600);
}

window.copyShareLink = function(url, el) {
  // el is optional element to anchor tooltip
  const target = (typeof el === 'object' && el) ? el : null;

  if (!navigator.clipboard) {
    // Fallback: create textarea
    const ta = document.createElement('textarea');
    ta.value = url;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      if (typeof showToast === 'function') showToast('Share link copied to clipboard!', 'success');
      createTooltip('Copied!', target);
    } catch (e) {
      if (typeof showToast === 'function') showToast('Failed to copy link', 'error');
    }
    ta.remove();
    return;
  }

  navigator.clipboard.writeText(url).then(() => {
    if (typeof showToast === 'function') showToast('Share link copied to clipboard!', 'success');
    createTooltip('Copied!', target);
  }).catch(() => {
    if (typeof showToast === 'function') showToast('Failed to copy link', 'error');
  });
};
