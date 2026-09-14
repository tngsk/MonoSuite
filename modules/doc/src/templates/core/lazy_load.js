document.addEventListener('DOMContentLoaded', () => {
    const storeEl = document.getElementById('mono-asset-store');

    const isValidUrl = (url) => {
        if (!url || typeof url !== 'string') return false;
        try {
            const parsed = new URL(url, window.location.href);
            const protocol = parsed.protocol.toLowerCase();
            return ['http:', 'https:', 'data:'].includes(protocol);
        } catch (e) {
            // If URL parsing fails, it might be a relative path which is fine,
            // but to be safe against complex protocol bypasses, we ensure it doesn't contain forbidden protocols
            // Actually, `new URL(url, window.location.href)` handles relative URLs perfectly.
            // If it still throws, it's malformed.
            return false;
        }
    };

    if (storeEl) {
        try {
            const assets = JSON.parse(storeEl.textContent);
            const elements = document.querySelectorAll('[data-lazy-src], [data-lazy-src-a], [data-lazy-src-b]');
            elements.forEach(el => {
                const src = el.getAttribute('data-lazy-src');
                if (src && assets[src] && isValidUrl(assets[src])) {
                    el.setAttribute('src', assets[src]);
                    el.removeAttribute('data-lazy-src');
                }

                const srcA = el.getAttribute('data-lazy-src-a');
                if (srcA && assets[srcA] && isValidUrl(assets[srcA])) {
                    el.setAttribute('src-a', assets[srcA]);
                    el.removeAttribute('data-lazy-src-a');
                }

                const srcB = el.getAttribute('data-lazy-src-b');
                if (srcB && assets[srcB] && isValidUrl(assets[srcB])) {
                    el.setAttribute('src-b', assets[srcB]);
                    el.removeAttribute('data-lazy-src-b');
                }
            });
        } catch (e) {
            console.error('Failed to load lazy assets', e);
        }
    }
});

// Capture image load failures globally and display a user-friendly error banner
window.addEventListener('error', (event) => {
    const target = event.target;
    if (!target || target.tagName !== 'IMG') return;
    if (target.classList.contains('mono-image-error-processed')) return;
    target.classList.add('mono-image-error-processed');

    const src = target.getAttribute('src') || target.getAttribute('data-lazy-src') || target.currentSrc || '';
    console.error('[Mono] 画像の読み込みに失敗しました:', {
        url: src,
        alt: target.getAttribute('alt') || '',
        element: target
    });

    const errorContainer = document.createElement('div');
    errorContainer.className = 'mono-image-error';
    errorContainer.setAttribute('role', 'alert');
    errorContainer.setAttribute('aria-label', '画像読み込みエラー');

    const errorHeader = document.createElement('div');
    errorHeader.className = 'mono-image-error-header';

    const errorIcon = document.createElement('span');
    errorIcon.className = 'mono-image-error-icon';
    errorIcon.setAttribute('aria-hidden', 'true');
    errorIcon.textContent = '⚠️';

    const errorTitle = document.createElement('span');
    errorTitle.className = 'mono-image-error-title';
    errorTitle.textContent = '画像読み込みエラー';

    errorHeader.appendChild(errorIcon);
    errorHeader.appendChild(errorTitle);

    const errorDetails = document.createElement('div');
    errorDetails.className = 'mono-image-error-details';

    if (src) {
        const errorUrl = document.createElement('code');
        errorUrl.className = 'mono-image-error-url';
        errorUrl.textContent = src;
        errorDetails.appendChild(errorUrl);
    }

    const errorHint = document.createElement('div');
    errorHint.className = 'mono-image-error-hint';
    errorHint.textContent = '指定されたURLが存在しないか、Webページ（HTML）など画像以外の形式である可能性があります。Content-Security-Policy (CSP) の設定も確認してください。';
    errorDetails.appendChild(errorHint);

    errorContainer.appendChild(errorHeader);
    errorContainer.appendChild(errorDetails);

    target.style.display = 'none';
    if (target.parentNode) {
        target.parentNode.insertBefore(errorContainer, target);
    }
}, true);