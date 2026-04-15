# app/tasks_service.py — Tasks data service
# Reads tasks from the dashboard.json feed.
# Never touches Google APIs directly.

class TasksService:
    def __init__(self, cache):
        self._cache = cache

    def ingest(self, tasks):
        """Accepts a list of {title, priority} dicts from dashboard feed."""
        try:
            self._cache.tasks = [
                {"title": str(t.get("title", "")),
                 "priority": str(t.get("priority", "normal")).lower()}
                for t in (tasks or [])
            ][:5]
        except Exception as e:
            print("TasksService: ingest failed:", e)

    def update_if_due(self, state):
        """No-op: tasks are updated via dashboard_service.update_if_due()."""
        pass
