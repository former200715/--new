// NEXUS HOTEL - 主JS
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }

    // 汉堡按钮：展开/收起
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        });
    }

    // 侧边栏收起按钮
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    if (collapseBtn) {
        collapseBtn.addEventListener('click', closeSidebar);
    }

    // 点击遮罩层收起
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // 导航链接点击后自动收起
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768 || sidebar.classList.contains('open')) {
                closeSidebar();
            }
        });
    });

    // Flash消息自动消失
    document.querySelectorAll('.flash').forEach(el => {
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-8px)';
            setTimeout(() => el.remove(), 300);
        }, 4000);
    });

    // === 主题切换 ===
    const themeNames = { dark: '暗黑模式', light: '浅色模式' };
    const themeDots = { dark: '#00d4ff', light: '#0066ff' };
    const themeBtn = document.getElementById('themeBtn');
    const themeDropdown = document.getElementById('themeDropdown');
    const themeDot = document.getElementById('themeDot');
    const themeLabel = document.getElementById('themeLabel');

    const savedTheme = localStorage.getItem('nexus-theme') || 'dark';
    applyTheme(savedTheme);

    if (themeBtn && themeDropdown) {
        themeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            themeDropdown.classList.toggle('open');
        });

        themeDropdown.querySelectorAll('.theme-option').forEach(opt => {
            opt.addEventListener('click', () => {
                const theme = opt.dataset.theme;
                applyTheme(theme);
                localStorage.setItem('nexus-theme', theme);
                themeDropdown.classList.remove('open');
            });
        });

        document.addEventListener('click', () => {
            themeDropdown.classList.remove('open');
        });
    }

    function applyTheme(theme) {
        const isDark = theme === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        // Switch aurora mode
        if (typeof window.setAuroraTheme === 'function') {
            window.setAuroraTheme(isDark);
        }
        if (themeDot) themeDot.style.background = themeDots[theme];
        if (themeLabel) themeLabel.textContent = themeNames[theme];
        document.querySelectorAll('.theme-option').forEach(opt => {
            opt.classList.toggle('active', opt.dataset.theme === theme);
        });
    }

    // === Tooltip (JS fixed positioning, never clipped) ===
    var tooltipBox = document.createElement('div');
    tooltipBox.className = 'tooltip-box';
    document.body.appendChild(tooltipBox);

    document.addEventListener('mouseover', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (!el) { tooltipBox.classList.remove('visible'); return; }
        tooltipBox.textContent = el.getAttribute('data-tooltip');
        tooltipBox.classList.add('visible');
        positionTooltip(el);
    });

    document.addEventListener('mouseout', function(e) {
        var el = e.target.closest('[data-tooltip]');
        if (el) tooltipBox.classList.remove('visible');
    });

    function positionTooltip(el) {
        var rect = el.getBoundingClientRect();
        var tw = tooltipBox.offsetWidth;
        var th = tooltipBox.offsetHeight;
        var gap = 10;
        var x = rect.left + rect.width / 2 - tw / 2;
        var y = rect.top - th - gap;

        // 上方空间不够时显示在下方
        if (y < 8) y = rect.bottom + gap;

        // 左右边界修正
        if (x < 8) x = 8;
        if (x + tw > window.innerWidth - 8) x = window.innerWidth - tw - 8;

        tooltipBox.style.left = x + 'px';
        tooltipBox.style.top = y + 'px';
    }
});
