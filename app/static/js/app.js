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

    // 3. Action / Delete Confirmation Prompts
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
