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
        if (!value) return { dateStr: '', timeStr: '' };
        const [datePart, timePart] = value.split('T');
        if (!datePart || !timePart) return { dateStr: '', timeStr: '' };
        const [year, month, day] = datePart.split('-');
        return {
            dateStr: `${day}/${month}/${year}`,
            timeStr: timePart.slice(0, 5),
        };
    }

    function buildWhatsAppMessage({ opponentName, myName, tournamentName, dateStr, timeStr, location }) {
        let msg = `Hola ${opponentName}, soy ${myName}. Te propongo que juguemos nuestro partido del torneo ${tournamentName} el ${dateStr} a las ${timeStr}`;
        if (location && location.trim()) {
            msg += ` en ${location.trim()}`;
        }
        msg += '. ¿Te viene bien?';
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

            if (!datetimeValue) {
                const form = card.querySelector('.match-proposal-form');
                if (form) {
                    const dtInput = form.querySelector('.proposal-datetime-input');
                    const locInput = form.querySelector('.proposal-location-input');
                    if (!dtInput || !dtInput.value) {
                        dtInput?.reportValidity?.();
                        return;
                    }
                    datetimeValue = dtInput.value;
                    location = locInput ? locInput.value : '';
                }
            }

            const { dateStr, timeStr } = parseDatetimeLocal(datetimeValue);
            if (!dateStr || !timeStr) return;

            const message = buildWhatsAppMessage({
                opponentName: card.dataset.opponentName,
                myName: card.dataset.myName,
                tournamentName: card.dataset.tournamentName,
                dateStr,
                timeStr,
                location,
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
