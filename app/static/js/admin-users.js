document.addEventListener('DOMContentLoaded', () => {
  // Attach handlers for admin user actions (activate/revoke, admin toggle)
  document.querySelectorAll('.admin-toggle-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = form.action;
      try {
        const resp = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!resp.ok) { showToast('Action failed', 'error'); return; }
        const data = await resp.json().catch(()=>null);
        showToast((data && data.message) || 'Updated', 'success');
        // Optionally update UI (simple approach: reload user list region via PJAX)
        if (window.pjaxNavigate) window.pjaxNavigate(window.location.href, false);
      } catch (err) {
        console.error(err);
        showToast('Network error', 'error');
      }
    });
  });
});
