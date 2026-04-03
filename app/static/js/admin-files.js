document.addEventListener('DOMContentLoaded', () => {
  // Attach delete handlers for admin file management
  document.querySelectorAll('.delete-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!confirm('Delete this file?')) return;

      const url = form.action;
      try {
        const resp = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!resp.ok) {
          const text = await resp.text();
          showToast('Delete failed', 'error');
          console.error('Delete failed', resp.status, text);
          return;
        }
        // On success remove row from DOM
        const row = form.closest('tr');
        if (row) row.remove();
        showToast('File deleted', 'success');
      } catch (err) {
        console.error(err);
        showToast('Network error', 'error');
      }
    });
  });
});
