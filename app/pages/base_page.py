# app/pages/base_page.py — Page base class
# All pages inherit from BasePage.
# Pages own their displayio.Group; never fetch from the network.

import displayio

class BasePage:
    """
    Abstract base. Subclasses must implement:
      _build()   — create all display objects, append to self.group
      _refresh() — update label text / tile indices from cache/state
    """

    def __init__(self, display, state, cache):
        self._display = display
        self._state   = state
        self._cache   = cache
        self._dirty   = True
        self._built   = False
        self.group    = displayio.Group()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def show(self, root):
        """Attach page group to root and refresh."""
        if not self._built:
            self._build()
            self._built = True
            self._dirty = True
        # Clear root and show this page
        while len(root) > 0:
            root.pop()
        root.append(self.group)
        self._dirty = True
        self.render()

    def hide(self):
        """Called when navigating away. Subclasses may clean up."""
        pass

    def update(self, now):
        """
        Called every loop tick with current time struct.
        Subclasses mark self._dirty when data changes.
        """
        pass

    def handle_input(self, event):
        """
        Handle a BTN_BACK / BTN_HOME / BTN_NEXT event.
        Return True if the event was consumed (prevents app_controller fallback).
        """
        return False

    def render(self):
        """Force a full redraw."""
        if self._built:
            self._refresh()
            self._dirty = False

    def render_if_dirty(self):
        """Redraw only if dirty flag is set."""
        if self._dirty and self._built:
            self._refresh()
            self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    # ── Subclass hooks ────────────────────────────────────────────────────────

    def _build(self):
        raise NotImplementedError

    def _refresh(self):
        raise NotImplementedError
