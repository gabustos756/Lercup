// Tennis Tournament Organizer - Client Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Hamburger Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show');
            const expanded = navMenu.classList.contains('show');
            menuToggle.setAttribute('aria-expanded', expanded);
        });
    }

    // 2. Dismissable Alerts
    const alertCloseButtons = document.querySelectorAll('.alert .close-btn');
    alertCloseButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                alert.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                setTimeout(() => {
                    alert.remove();
                }, 200);
            }
        });
    });

    // 3. Notification Bell Dropdown
    const notificationBell = document.querySelector('.notification-bell');
    const notificationDropdown = document.querySelector('.notification-dropdown');

    if (notificationBell && notificationDropdown) {
        notificationBell.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = notificationBell.getAttribute('aria-expanded') === 'true';
            notificationBell.setAttribute('aria-expanded', !isOpen);
            notificationDropdown.hidden = isOpen;
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-menu')) {
                notificationBell.setAttribute('aria-expanded', 'false');
                notificationDropdown.hidden = true;
            }
        });
    }

    // 4. WhatsApp Match Proposal Notifications
    function formatPhoneForWhatsApp(phone) {
        return (phone || '').replace(/\D/g, '');
    }

    function parseDatetimeLocal(value) {
        if (!value) return { dateStr: '', timeStr: '', start: null };
        const [datePart, timePart] = value.split('T');
        if (!datePart || !timePart) return { dateStr: '', timeStr: '', start: null };
        const [year, month, day] = datePart.split('-').map(Number);
        const [hours, minutes] = timePart.slice(0, 5).split(':').map(Number);
        if ([year, month, day, hours, minutes].some(Number.isNaN)) {
            return { dateStr: '', timeStr: '', start: null };
        }
        return {
            dateStr: `${String(day).padStart(2, '0')}/${String(month).padStart(2, '0')}/${year}`,
            timeStr: `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`,
            start: new Date(year, month - 1, day, hours, minutes, 0),
        };
    }

    function formatGoogleCalendarUtc(date) {
        const pad = (n) => String(n).padStart(2, '0');
        return (
            `${date.getUTCFullYear()}${pad(date.getUTCMonth() + 1)}${pad(date.getUTCDate())}` +
            `T${pad(date.getUTCHours())}${pad(date.getUTCMinutes())}${pad(date.getUTCSeconds())}Z`
        );
    }

    function buildGoogleCalendarUrl({ title, start, durationMinutes, details, location, locationUrl }) {
        if (!start || Number.isNaN(start.getTime())) return '';

        const end = new Date(start.getTime() + durationMinutes * 60 * 1000);
        const params = new URLSearchParams({
            action: 'TEMPLATE',
            text: title,
            dates: `${formatGoogleCalendarUtc(start)}/${formatGoogleCalendarUtc(end)}`,
        });

        if (details) params.set('details', details);

        let locationValue = (location || '').trim();
        if (locationUrl && locationUrl.trim()) {
            locationValue = locationValue
                ? `${locationValue} (${locationUrl.trim()})`
                : locationUrl.trim();
        }
        if (locationValue) params.set('location', locationValue);

        return `https://calendar.google.com/calendar/render?${params.toString()}`;
    }

    function googleMapsSearchUrl(label) {
        return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(label.trim())}`;
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

    function resolveMapsUrl(location, locationUrl) {
        const url = (locationUrl || '').trim();
        if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
            return url;
        }
        if (location && location.trim()) {
            return googleMapsSearchUrl(location);
        }
        return '';
    }

    function buildWhatsAppMessage({
        opponentName,
        myName,
        tournamentName,
        dateStr,
        timeStr,
        location,
        locationUrl,
        calendarUrl,
    }) {
        let msg = `Hola ${opponentName}, soy ${myName}. Te propongo que juguemos nuestro partido del torneo ${tournamentName} el ${dateStr} a las ${timeStr}`;
        if (location && location.trim()) {
            msg += ` en ${location.trim()}`;
        }
        msg += '. ¿Te viene bien?';

        const mapsUrl = resolveMapsUrl(location, locationUrl);
        if (mapsUrl) {
            msg += `\n\n📍 Google Maps:\n${mapsUrl}`;
        }
        if (calendarUrl) {
            msg += `\n\n📅 Agregar a Google Calendar:\n${calendarUrl}`;
        }
        return msg;
    }

    document.querySelectorAll('.whatsapp-notify-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.upcoming-match-card, .tournament-match-card');
            if (!card) return;

            const phone = formatPhoneForWhatsApp(card.dataset.opponentPhone);
            if (!phone) return;

            let datetimeValue = btn.dataset.fixedDatetime || '';
            let location = btn.dataset.fixedLocation || '';
            let locationUrl = btn.dataset.fixedLocationUrl || '';

            if (!datetimeValue) {
                const form = card.querySelector('.match-proposal-form');
                if (form) {
                    const dtInput = form.querySelector('.proposal-datetime-input');
                    const locInput = form.querySelector('.proposal-location-input');
                    const locUrlInput = form.querySelector('.location-picker-url-input, input[name="location_url"]');
                    if (!dtInput || !dtInput.value) {
                        dtInput?.reportValidity?.();
                        return;
                    }
                    datetimeValue = dtInput.value;
                    location = locInput ? locInput.value : '';
                    locationUrl = locUrlInput ? locUrlInput.value : '';
                    if (!locationUrl && location) {
                        locationUrl = googleMapsSearchUrl(location);
                    }
                }
            } else if (!locationUrl && location) {
                locationUrl = googleMapsSearchUrl(location);
            }

            const { dateStr, timeStr, start } = parseDatetimeLocal(datetimeValue);
            if (!dateStr || !timeStr || !start) return;

            const opponentName = card.dataset.opponentName || 'oponente';
            const myName = card.dataset.myName || '';
            const tournamentName = card.dataset.tournamentName || 'torneo';

            const calendarUrl = buildGoogleCalendarUrl({
                title: `Partido ${tournamentName}: ${myName} vs ${opponentName}`,
                start,
                durationMinutes: 120,
                details: `Partido de tenis — torneo ${tournamentName}.\n${myName} vs ${opponentName}.`,
                location,
                locationUrl,
            });

            const message = buildWhatsAppMessage({
                opponentName,
                myName,
                tournamentName,
                dateStr,
                timeStr,
                location,
                locationUrl,
                calendarUrl,
            });

            const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
            window.open(url, '_blank', 'noopener,noreferrer');
        });
    });

    // 5. Tournament match panel toggles
    document.querySelectorAll('.match-panel-toggle').forEach((btn) => {
        btn.addEventListener('click', () => {
            const panelId = btn.dataset.panelTarget;
            const panel = panelId ? document.getElementById(panelId) : null;
            if (!panel) return;

            const jornadaKey = btn.dataset.jornadaKey;
            const isOpen = panel.classList.contains('is-open');

            if (jornadaKey) {
                document.querySelectorAll(`.match-panel-body[data-jornada-key="${jornadaKey}"].is-open`).forEach((openPanel) => {
                    openPanel.classList.remove('is-open');
                    const toggle = openPanel.closest('.tournament-match-card')?.querySelector('.match-panel-toggle');
                    if (toggle) toggle.setAttribute('aria-expanded', 'false');
                });
            }

            if (!isOpen) {
                panel.classList.add('is-open');
                btn.setAttribute('aria-expanded', 'true');
            } else {
                panel.classList.remove('is-open');
                btn.setAttribute('aria-expanded', 'false');
            }
        });
    });

    // 6. Action / Delete Confirmation Prompts
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const message = button.getAttribute('data-confirm-message') || '¿Estás seguro de que deseas eliminar este elemento?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});
