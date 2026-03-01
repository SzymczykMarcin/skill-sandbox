(() => {
  const STORAGE_KEY = 'sql-course-progress-v1';

  function emptyProgress() {
    return { completedLessons: {}, startedLessons: {}, lessonDrafts: {}, lastVisitedLesson: null };
  }

  function loadProgress() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return emptyProgress();
      }
      const parsed = JSON.parse(raw);
      return {
        completedLessons: parsed.completedLessons || {},
        startedLessons: parsed.startedLessons || {},
        lessonDrafts: parsed.lessonDrafts || {},
        lastVisitedLesson: parsed.lastVisitedLesson || null,
      };
    } catch (_error) {
      return emptyProgress();
    }
  }

  function saveProgress(progress) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }

  function updateProgress(mutator) {
    const progress = loadProgress();
    mutator(progress);
    saveProgress(progress);
  }

  window.SQLCourseProgress = {
    STORAGE_KEY,
    loadProgress,
    updateProgress,
  };
})();
