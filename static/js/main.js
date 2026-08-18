/* ==========================================================================
   SARKARI RESULT PORTAL JAVASCRIPT (SEARCH, THEME, NAVIGATION & TOOLS)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle (Dark / Light Mode)
    const themeBtn = document.getElementById('themeToggle');
    const htmlEl = document.documentElement;
    
    const savedTheme = localStorage.getItem('sr_theme') || 'light';
    htmlEl.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = htmlEl.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-theme', newTheme);
            localStorage.setItem('sr_theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeBtn) return;
        if (theme === 'dark') {
            themeBtn.innerHTML = '<i class="fas fa-sun" style="color: #ffdd00;"></i>';
            themeBtn.title = "Switch to Light Mode";
        } else {
            themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
            themeBtn.title = "Switch to Dark Mode";
        }
    }

    // 2. Mobile Navigation Toggle
    const mobileToggle = document.getElementById('mobileNavToggle');
    const navLinks = document.getElementById('navLinks');
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }

    // 3. Search Modal & Live Search Engine
    const openSearchBtn = document.getElementById('openSearchModal');
    const closeSearchBtn = document.getElementById('closeSearchModal');
    const searchModal = document.getElementById('searchModal');
    const searchInput = document.getElementById('liveSearchInput');
    const searchResultsBox = document.getElementById('searchResultsBox');
    const filterTags = document.querySelectorAll('.filter-tag');

    let activeCategory = '';
    let searchDebounce = null;

    function openModal() {
        if (!searchModal) return;
        searchModal.classList.add('open');
        setTimeout(() => { if (searchInput) searchInput.focus(); }, 50);
    }

    function closeModal() {
        if (!searchModal) return;
        searchModal.classList.remove('open');
    }

    if (openSearchBtn) openSearchBtn.addEventListener('click', openModal);
    if (closeSearchBtn) closeSearchBtn.addEventListener('click', closeModal);

    if (searchModal) {
        searchModal.addEventListener('click', (e) => {
            if (e.target === searchModal) closeModal();
        });
    }

    // Keyboard shortcut (Ctrl+K or /)
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
            e.preventDefault();
            openModal();
        } else if (e.key === 'Escape' && searchModal && searchModal.classList.contains('open')) {
            closeModal();
        }
    });

    // Category Tags Filter in Modal
    filterTags.forEach(btn => {
        btn.addEventListener('click', function() {
            filterTags.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            activeCategory = this.getAttribute('data-cat') || '';
            performSearch();
        });
    });

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(performSearch, 150);
        });
    }

    function performSearch() {
        if (!searchInput || !searchResultsBox) return;
        const query = searchInput.value.trim();

        if (!query && !activeCategory) {
            searchResultsBox.innerHTML = `<div class="search-hint"><i class="fas fa-keyboard"></i> Type above to instantly search through hundreds of live Sarkari notifications...</div>`;
            return;
        }

        searchResultsBox.innerHTML = `<div class="search-hint"><i class="fas fa-spinner fa-spin"></i> Searching Sarkari Database...</div>`;

        fetch(`/api/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(activeCategory)}`)
            .then(res => res.json())
            .then(data => {
                if (!data.results || data.results.length === 0) {
                    searchResultsBox.innerHTML = `<div class="search-hint"><i class="fas fa-exclamation-circle"></i> No results found for "${query}". Try searching another keyword.</div>`;
                    return;
                }

                let html = '';
                data.results.forEach(item => {
                    const catBadgeColor = getCatColor(item.category);
                    html += `
                        <a href="${item.url}" class="search-result-row">
                            <div class="sr-row-left">
                                <span class="sr-cat-tag" style="background-color: ${catBadgeColor};">${item.category_name}</span>
                                <span class="sr-item-title">${highlightMatch(item.title, query)}</span>
                            </div>
                            <i class="fas fa-arrow-right" style="color: #999; font-size: 12px;"></i>
                        </a>
                    `;
                });
                searchResultsBox.innerHTML = html;
            })
            .catch(err => {
                searchResultsBox.innerHTML = `<div class="search-hint"><i class="fas fa-times-circle"></i> Error performing search. Please try again.</div>`;
            });
    }

    function highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark style="background:#ffeb3b; color:#000; padding:1px 3px; border-radius:2px;">$1</mark>');
    }

    function getCatColor(cat) {
        const map = {
            'result': '#077822',
            'admit-card': '#0d13b5',
            'latest-jobs': '#ab183d',
            'answer-key': '#c78334',
            'syllabus': '#868a08',
            'admission': '#ed13e3'
        };
        return map[cat] || '#ab183d';
    }

    // 4. Back to Top Button
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTopBtn.style.display = 'flex';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});
