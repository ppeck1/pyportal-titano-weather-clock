# app/app_controller.py — Application controller / state machine
# Owns the page list, handles navigation, dispatches input to pages.
# The main loop calls handle_events() each tick.

import time
import displayio
from app.constants import (
    BOOT, AMBIENT_ROTATE, MANUAL_NAV, FOCUSED_VIEW, ALARM_ACTIVE,
    ERROR_RECOVERABLE, PAGE_HERO, PAGE_LABELS,
    BTN_BACK, BTN_HOME, BTN_NEXT,
    TIMER_IDLE,
)


class AppController:

    def __init__(self, display, state, cache,
                 input_handler, audio,
                 timer_svc, alarm_svc):
        self._display = display
        self._state   = state
        self._cache   = cache
        self._input   = input_handler
        self._audio   = audio
        self._timer   = timer_svc
        self._alarm   = alarm_svc

        # Root display group — pages swap in here
        self._root = displayio.Group()
        display.root_group = self._root

        # Lazy page registry: (class, extra_kwargs)
        # Pages are instantiated on first visit to conserve RAM
        self._page_classes = None   # set in _register_pages()
        self._pages        = []
        self._current_page_obj = None

        self._register_pages()
        self._show_page(PAGE_HERO)
        self._alarm.set_dismiss_callback(self.on_alarm_dismissed)

    # ── Page registry ─────────────────────────────────────────────────────────

    def _register_pages(self):
        from app.pages.hero_page     import HeroPage
        from app.pages.forecast_page import ForecastPage
        from app.pages.timer_page    import TimerPage
        from app.pages.alarm_page    import AlarmPage
        from app.pages.status_page   import StatusPage

        # Calendar/Tasks pages are intentionally disabled on low-memory builds.
        self._page_classes = [
            (HeroPage,     {}),
            (ForecastPage, {}),
            (TimerPage,    {"timer_svc": self._timer, "audio": self._audio}),
            (AlarmPage,    {"alarm_svc": self._alarm, "audio": self._audio}),
            (StatusPage,   {}),
        ]
        self._pages = [None] * len(self._page_classes)
        print("AppController: active pages={}".format(len(self._page_classes)))

    @property
    def _page_count(self):
        return len(self._page_classes)

    def _get_page(self, idx):
        if self._pages[idx] is None:
            cls, kwargs = self._page_classes[idx]
            self._pages[idx] = cls(
                self._display, self._state, self._cache, **kwargs
            )
        return self._pages[idx]

    def _show_page(self, idx):
        if self._current_page_obj is not None:
            self._current_page_obj.hide()
        self._state.current_page = idx
        page = self._get_page(idx)
        page.show(self._root)
        self._current_page_obj = page

    def on_alarm_dismissed(self):
        """Visual/page-layer restoration after AlarmService owns dismiss state."""
        self._show_page(PAGE_HERO)

    def reset_ambient_timers(self, now=None):
        if now is None:
            now = time.monotonic()
        self._state.last_rotate_time = now
        self._state.last_input_time = now

    def enter_ambient_rotate(self, page_idx=None, now=None):
        if now is None:
            now = time.monotonic()
        if page_idx is not None:
            self._show_page(page_idx)
        self._state.mode = AMBIENT_ROTATE
        self.reset_ambient_timers(now)

    # ── Input routing ─────────────────────────────────────────────────────────

    def handle_events(self):
        """Process all pending input events and route to current page or controller."""
        s   = self._state
        now = time.monotonic()

        event = self._input.pop_event()
        while event is not None:
            # Alarm active — any press dismisses
            if s.mode == ALARM_ACTIVE:
                self._alarm.dismiss()
                break

            # Let current page try to consume the event first
            consumed = (self._current_page_obj is not None and
                        self._current_page_obj.handle_input(event))

            if not consumed:
                self._handle_nav(event, now)

            # Any input resets nav timeout
            s.last_input_time = now
            if s.mode == AMBIENT_ROTATE:
                s.mode = MANUAL_NAV
                s.last_rotate_time = now

            event = self._input.pop_event()

        # Ambient rotation timeout
        if s.mode == MANUAL_NAV:
            if (now - s.last_input_time) >= self._manual_timeout():
                self.enter_ambient_rotate(now=now)

        # Ambient auto-rotate
        if s.mode == AMBIENT_ROTATE:
            if (now - s.last_rotate_time) >= self._rotate_interval():
                s.last_rotate_time = now
                next_page = (s.current_page + 1) % self._page_count
                self._show_page(next_page)

    def _handle_nav(self, event, now):
        s = self._state
        if event == BTN_HOME:
            self._audio.click()
            self._show_page(PAGE_HERO)
            s.mode = MANUAL_NAV
        elif event == BTN_NEXT:
            self._audio.click()
            next_p = (s.current_page + 1) % self._page_count
            self._show_page(next_p)
            s.mode = MANUAL_NAV
        elif event == BTN_BACK:
            self._audio.click()
            prev_p = (s.current_page - 1) % self._page_count
            self._show_page(prev_p)
            s.mode = MANUAL_NAV

    # ── Scheduler callbacks ───────────────────────────────────────────────────

    def tick(self, now_struct):
        """Called each loop tick. Updates current page and manages state."""
        if self._current_page_obj is not None:
            self._current_page_obj.update(now_struct)
            self._current_page_obj.render_if_dirty()

    def mark_all_dirty(self):
        for p in self._pages:
            if p is not None:
                p.mark_dirty()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _manual_timeout(self):
        from app import config
        return config.MANUAL_TIMEOUT_SECS

    def _rotate_interval(self):
        from app import config
        return config.AMBIENT_ROTATE_SECS
