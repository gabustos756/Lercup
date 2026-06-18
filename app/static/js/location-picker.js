// Location picker — Google Maps search (free links, no API key)

(function () {
    function googleMapsSearchUrl(label) {
        const q = encodeURIComponent(label.trim());
        return `https://www.google.com/maps/search/?api=1&query=${q}`;
    }

    function isGoogleMapsUrl(url) {
        if (!url) return false;
        const lower = url.toLowerCase();
        return (
            lower.includes('google.com/maps')
            || lower.includes('maps.google.com')
            || lower.includes('goo.gl/maps')
        );
    }

    function initLocationPicker(root) {
        const labelInput = root.querySelector('.location-picker-label');
        const urlInput = root.querySelector('.location-picker-url-input');
        const preview = root.querySelector('.location-picker-preview');
        const openBtn = root.querySelector('.location-picker-open-maps');
        if (!labelInput || !urlInput) return;

        let urlEditedManually = Boolean(urlInput.value.trim() && isGoogleMapsUrl(urlInput.value));

        function updatePreview(url) {
            if (!preview) return;
            if (url && isGoogleMapsUrl(url)) {
                preview.href = url;
                preview.hidden = false;
            } else {
                preview.href = '#';
                preview.hidden = true;
            }
        }

        function syncUrlFromLabel() {
            const label = labelInput.value.trim();
            if (!label) {
                if (!urlEditedManually) {
                    urlInput.value = '';
                    updatePreview('');
                }
                return;
            }
            if (!urlEditedManually || !isGoogleMapsUrl(urlInput.value)) {
                urlInput.value = googleMapsSearchUrl(label);
                urlEditedManually = false;
                updatePreview(urlInput.value);
            }
        }

        labelInput.addEventListener('blur', syncUrlFromLabel);

        urlInput.addEventListener('input', () => {
            const val = urlInput.value.trim();
            urlEditedManually = Boolean(val && isGoogleMapsUrl(val));
            updatePreview(val);
        });

        if (openBtn) {
            openBtn.addEventListener('click', () => {
                const label = labelInput.value.trim();
                if (!label) {
                    labelInput.focus();
                    return;
                }
                syncUrlFromLabel();
                window.open(googleMapsSearchUrl(label), '_blank', 'noopener,noreferrer');
            });
        }

        const form = root.closest('form');
        if (form) {
            form.addEventListener('submit', syncUrlFromLabel);
        }

        updatePreview(urlInput.value.trim());
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-location-picker]').forEach(initLocationPicker);
    });
})();
