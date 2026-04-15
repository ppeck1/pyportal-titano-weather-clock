# app/audio.py — Non-blocking PWM audio
# Generates tones via audiopwmio + audiocore.RawSample.
# Patterns are sequences of (freq_hz, duration_ms) tuples.
# Call update() each loop tick to advance playback.

import time
import array
import math
import board
from app.constants import AUDIO_CLICK, AUDIO_TIMER_DONE, AUDIO_ALARM

# Patterns: list of (freq_hz, duration_ms); freq=0 → silence
_PATTERNS = {
    AUDIO_CLICK:      ((880, 30),),
    AUDIO_TIMER_DONE: ((660, 120), (0, 60), (660, 120), (0, 60), (880, 200)),
    AUDIO_ALARM:      ((880, 200), (0, 100), (880, 200), (0, 100),
                       (660, 200), (0, 300)),
}

_SAMPLE_RATE = 8000
_AMPLITUDE   = 28000    # 0–32767; lower = quieter


def _make_tone(freq, num_samples):
    buf = array.array("H", [0] * num_samples)
    if freq > 0:
        for i in range(num_samples):
            val = int(32768 + _AMPLITUDE * math.sin(2 * math.pi * freq * i / _SAMPLE_RATE))
            buf[i] = min(65535, max(0, val))
    else:
        for i in range(num_samples):
            buf[i] = 32768  # DC = silence
    return buf


class AudioManager:
    def __init__(self):
        self._mixer = None
        self._speaker = None
        self._enabled = False
        self._pattern  = []
        self._step     = 0
        self._loop     = False
        self._next_at  = 0.0
        self._playing  = False
        self._init_hw()

    def _init_hw(self):
        try:
            import audiopwmio
            import audiocore
            self._audiocore = audiocore
            # PyPortal Titano speaker pin
            self._speaker = audiopwmio.PWMAudioOut(board.SPEAKER)
            self._enabled = True
        except Exception:
            self._enabled = False

    def play(self, sound_name, loop=False):
        """Start playing a named sound pattern."""
        if not self._enabled:
            return
        pat = _PATTERNS.get(sound_name)
        if not pat:
            return
        self._pattern = list(pat)
        self._step    = 0
        self._loop    = loop
        self._playing = True
        self._next_at = time.monotonic()
        self._advance()

    def stop(self):
        """Stop playback immediately."""
        self._playing = False
        self._loop    = False
        if self._enabled and self._speaker:
            try:
                self._speaker.stop()
            except Exception:
                pass

    def is_playing(self):
        return self._playing

    def update(self):
        """Call each loop tick to advance non-blocking playback."""
        if not self._playing or not self._enabled:
            return
        if time.monotonic() >= self._next_at:
            self._advance()

    def _advance(self):
        if self._step >= len(self._pattern):
            if self._loop:
                self._step = 0
            else:
                self.stop()
                return
        freq, dur_ms = self._pattern[self._step]
        self._step += 1
        self._next_at = time.monotonic() + dur_ms / 1000.0
        num_samples = max(1, int(_SAMPLE_RATE * dur_ms / 1000.0))
        buf = _make_tone(freq, num_samples)
        try:
            sample = self._audiocore.RawSample(buf, sample_rate=_SAMPLE_RATE)
            self._speaker.play(sample)
        except Exception:
            pass

    def click(self):
        """Play the UI click sound only for valid UI actions and never over active alerts."""
        if self._playing and self._loop:
            return  # don't interrupt alerts
        self.play(AUDIO_CLICK)

    def deinit(self):
        self.stop()
        if self._speaker:
            try:
                self._speaker.deinit()
            except Exception:
                pass
