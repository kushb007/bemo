// Minimal Bootstrap JS replacement for dropdowns and collapsible navbar
document.addEventListener('DOMContentLoaded', function() {
    // Handle navbar toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            const isExpanded = navbarCollapse.classList.contains('show');
            navbarCollapse.classList.toggle('show');
            // Update ARIA attribute for accessibility
            this.setAttribute('aria-expanded', !isExpanded);
        });
    }
    
    // Handle dropdown toggles
    const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const menu = this.nextElementSibling;
            if (menu && menu.classList.contains('dropdown-menu')) {
                // Close other dropdowns
                document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                    if (m !== menu) m.classList.remove('show');
                });
                menu.classList.toggle('show');
            }
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('[data-bs-toggle="dropdown"]')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(function(menu) {
                menu.classList.remove('show');
            });
        }
    });
    
    // Handle alert dismissals
    const alertCloses = document.querySelectorAll('[data-bs-dismiss="alert"]');
    alertCloses.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert) {
                alert.style.display = 'none';
            }
        });
    });
});
