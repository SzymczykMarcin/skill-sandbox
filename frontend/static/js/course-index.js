(() => {
  const { STORAGE_KEY, loadProgress } = window.SQLCourseProgress;

  function getLessonStatus(slug, progress) {
    if (progress.completedLessons?.[slug]) {
      return 'completed';
    }
    const hasDraft = typeof progress.lessonDrafts?.[slug] === 'string' && progress.lessonDrafts[slug].trim().length > 0;
    if (progress.startedLessons?.[slug] || hasDraft) {
      return 'in-progress';
    }
    return 'not-started';
  }

  function renderIndexState() {
    const progress = loadProgress();

    for (const el of document.querySelectorAll('[data-lesson-status]')) {
      const slug = el.getAttribute('data-lesson-status');
      const status = getLessonStatus(slug, progress);
      if (status === 'completed') {
        el.textContent = 'Ukończona';
        el.classList.add('completed');
        el.classList.remove('in-progress');
      } else if (status === 'in-progress') {
        el.textContent = 'W trakcie';
        el.classList.add('in-progress');
        el.classList.remove('completed');
      } else {
        el.textContent = 'Nie rozpoczęta';
        el.classList.remove('in-progress', 'completed');
      }
    }

    const continueBtn = document.getElementById('continue-learning');
    const targetSlug = progress.lastVisitedLesson;
    if (targetSlug) {
      continueBtn.href = `/kurs/sql/${encodeURIComponent(targetSlug)}`;
      continueBtn.classList.remove('disabled');
    } else {
      continueBtn.href = '/kurs/sql';
      continueBtn.classList.add('disabled');
    }
  }

  document.getElementById('reset-progress').addEventListener('click', () => {
    const confirmed = window.confirm('Na pewno zresetować cały postęp kursu SQL?');
    if (!confirmed) {
      return;
    }
    window.localStorage.removeItem(STORAGE_KEY);
    renderIndexState();
  });

  renderIndexState();
})();
