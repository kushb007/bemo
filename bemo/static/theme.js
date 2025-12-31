// Theme Management for Bemo
(function() {
  'use strict';

  // Get theme and layout from localStorage or use defaults
  function getTheme() {
    return localStorage.getItem('bemo-theme') || 'light';
  }

  function getLayout() {
    return localStorage.getItem('bemo-layout') || 'comfortable';
  }

  // Set theme
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('bemo-theme', theme);
    updateThemeIcon(theme);
    updateEditorTheme(theme);
  }

  // Set layout
  function setLayout(layout) {
    document.documentElement.setAttribute('data-layout', layout);
    localStorage.setItem('bemo-layout', layout);
  }

  // Update theme icon in navbar
  function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
      if (theme === 'dark') {
        themeIcon.className = 'bi bi-sun-fill';
      } else {
        themeIcon.className = 'bi bi-moon-fill';
      }
    }
  }

  // Update ACE editor theme if editor exists
  function updateEditorTheme(theme) {
    if (typeof ace !== 'undefined' && window.editor) {
      const editorTheme = theme === 'dark' ? 'ace/theme/monokai' : 'ace/theme/github';
      window.editor.setTheme(editorTheme);
    }
  }

  // Toggle theme
  function toggleTheme() {
    const currentTheme = getTheme();
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }

  // Toggle layout
  function toggleLayout() {
    const currentLayout = getLayout();
    const newLayout = currentLayout === 'comfortable' ? 'compact' : 'comfortable';
    setLayout(newLayout);
  }

  // Initialize theme on page load
  function initTheme() {
    const theme = getTheme();
    const layout = getLayout();
    setTheme(theme);
    setLayout(layout);
  }

  // Add event listeners when DOM is ready
  function addEventListeners() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        toggleTheme();
      });
    }

    const layoutToggle = document.getElementById('layout-toggle');
    if (layoutToggle) {
      layoutToggle.addEventListener('click', function(e) {
        e.preventDefault();
        toggleLayout();
        
        // Update button text
        const currentLayout = getLayout();
        const layoutText = layoutToggle.querySelector('.layout-text');
        if (layoutText) {
          layoutText.textContent = currentLayout === 'comfortable' ? 'Comfortable' : 'Compact';
        }
      });
    }
  }

  // Initialize on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTheme();
      addEventListeners();
    });
  } else {
    initTheme();
    addEventListeners();
  }

  // Export functions for use in other scripts
  window.BemoTheme = {
    getTheme: getTheme,
    setTheme: setTheme,
    toggleTheme: toggleTheme,
    getLayout: getLayout,
    setLayout: setLayout,
    toggleLayout: toggleLayout
  };
})();
