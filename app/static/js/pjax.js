// Simple PJAX implementation: intercept link clicks and fetch HTML, replace main.container
// Keeps history in sync and calls window.onPageLoad after replacement

(function(){
    async function fetchPage(url) {
        const resp = await fetch(url, { headers: { 'X-PJAX': 'true' } });
        if (!resp.ok) throw new Error('Failed to fetch');
        const text = await resp.text();
        return text;
    }

    function parseAndExtract(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newContent = doc.querySelector('main.container');
        const title = doc.querySelector('title');
        return { newContent: newContent ? newContent.innerHTML : null, title: title ? title.textContent : null, scripts: Array.from(doc.scripts) };
    }

    async function navigate(url, push=true) {
        try {
            const html = await fetchPage(url);
            const { newContent, title, scripts } = parseAndExtract(html);
            if (!newContent) {
                window.location.href = url;
                return;
            }
            const container = document.querySelector('main.container');
            // Optional fade out
            container.style.opacity = 0;
            setTimeout(() => {
                container.innerHTML = newContent;
                if (title) document.title = title;

                // Scroll to top
                window.scrollTo(0,0);

                // Run any inline scripts from the new page (deferred)
                // Execute external initialization via global hook
                setTimeout(() => {
                    if (window.onPageLoad) {
                        window.onPageLoad();
                    }
                }, 30);

                container.style.opacity = 1;
            }, 180);

            if (push) history.pushState({ pjax: true }, '', url);
        } catch (err) {
            console.error('PJAX navigation failed', err);
            window.location.href = url; // fallback
        }
    }

    function handleLinkClick(e) {
        const a = e.target.closest('a');
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href) return;
        // Only same-origin and internal links
        if (a.target === '_blank' || a.hasAttribute('download')) return;
        const origin = window.location.origin;
        if (href.startsWith('http') && !href.startsWith(origin)) return;
        // Skip anchors and JS links
        if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;

        e.preventDefault();
        const url = new URL(href, window.location.href).toString();
        if (url === window.location.href) return;
        navigate(url, true);
    }

    document.addEventListener('click', (e) => {
        const a = e.target.closest('a');
        if (!a) return;
        handleLinkClick(e);
    });

    window.addEventListener('popstate', (e) => {
        navigate(window.location.href, false);
    });

    // Expose navigate for other scripts
    window.pjaxNavigate = navigate;
})();
