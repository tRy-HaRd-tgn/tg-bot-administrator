class Sidebar {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.toggleBtn = document.querySelector('.sidebar-toggle');
        this.mobileToggle = document.querySelector('.sidebar-toggle-mobile');
        this.mobileOverlay = document.querySelector('.mobile-overlay');
        this.mainContent = document.querySelector('.main-content');
        
        this.init();
    }

    init() {
        // Восстанавливаем состояние сайдбара
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            this.sidebar.classList.add('collapsed');
            document.body.classList.add('sidebar-collapsed');
        }

        // Обработчики событий
        this.toggleBtn?.addEventListener('click', () => this.toggle());
        this.mobileToggle?.addEventListener('click', () => this.toggleMobile());
        this.mobileOverlay?.addEventListener('click', () => this.closeMobile());

        // Обработчик изменения размера окна
        window.addEventListener('resize', () => this.handleResize());
    }

    toggle() {
        this.sidebar.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed');
        
        // Сохраняем состояние
        localStorage.setItem('sidebarCollapsed', this.sidebar.classList.contains('collapsed'));
    }

    toggleMobile() {
        this.sidebar.classList.toggle('mobile-visible');
        this.mobileOverlay.classList.toggle('visible');
        document.body.style.overflow = this.sidebar.classList.contains('mobile-visible') ? 'hidden' : '';
    }

    closeMobile() {
        this.sidebar.classList.remove('mobile-visible');
        this.mobileOverlay.classList.remove('visible');
        document.body.style.overflow = '';
    }

    handleResize() {
        if (window.innerWidth > 768) {
            this.closeMobile();
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.sidebar = new Sidebar();
    
    // Вызываем функцию при загрузке и изменении размера окна
    setupMobileView();
    window.addEventListener('resize', setupMobileView);
    
    // Добавляем активный класс текущему пункту меню
    function setActiveMenuItem() {
        const currentPath = window.location.pathname;
        
        menuLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    setActiveMenuItem();
});
