(() => {
  const STORAGE_KEY = 'sql-course-theme-v1';
  const THEME_LIGHT = 'light';
  const THEME_DARK = 'dark';

  function isValidTheme(value) {
    return value === THEME_LIGHT || value === THEME_DARK;
  }

  function resolveInitialTheme() {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (isValidTheme(stored)) {
      return stored;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? THEME_DARK : THEME_LIGHT;
  }

  function applyTheme(theme, { persist = true } = {}) {
    if (!isValidTheme(theme)) {
      return;
    }
    document.documentElement.dataset.theme = theme;
    if (persist) {
      window.localStorage.setItem(STORAGE_KEY, theme);
    }
    updateToggleLabel(theme);
  }

  function updateToggleLabel(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) {
      return;
    }
    const isDark = theme === THEME_DARK;
    toggle.setAttribute('aria-pressed', String(isDark));
    toggle.textContent = isDark ? 'Tryb jasny' : 'Tryb ciemny';
  }

  function initThemeToggle() {
    const theme = document.documentElement.dataset.theme || resolveInitialTheme();
    applyTheme(theme, { persist: false });

    const toggle = document.getElementById('theme-toggle');
    if (!toggle) {
      return;
    }
    toggle.addEventListener('click', () => {
      const current = document.documentElement.dataset.theme === THEME_DARK ? THEME_DARK : THEME_LIGHT;
      applyTheme(current === THEME_DARK ? THEME_LIGHT : THEME_DARK);
    });
  }

  window.SQLCourseTheme = {
    applyTheme,
    initThemeToggle,
    STORAGE_KEY,
  };

  initThemeToggle();
})();
