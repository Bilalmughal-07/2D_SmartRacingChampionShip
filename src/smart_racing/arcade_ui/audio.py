"""Small optional audio layer for the Arcade client.

The project does not require downloaded copyrighted assets, so the two themes
are generated as short deterministic WAV melodies at runtime.  Audio failures
(missing device, headless smoke, or an unavailable decoder) are deliberately
non-fatal: settings still persist and the game remains playable.
"""

from __future__ import annotations

import math
import tempfile
import wave
from pathlib import Path

from smart_racing.arcade_ui.session import GameSession


class AudioManager:
    """Manage menu background music and the championship race theme."""

    SAMPLE_RATE = 22050
    DURATION = 18

    def __init__(self, session: GameSession):
        self.session = session
        self.context = None
        self.player = None
        self.source = None
        self._paths: dict[str, Path] = {}

    def set_context(self, context: str) -> None:
        context = "championship" if context == "championship" else "menu"
        if context == "championship" and not self.session.settings.get("championship_music_enabled", True):
            context = "menu"
        if context == self.context:
            self._apply_volume()
            return
        self.stop()
        self.context = context
        if not self.session.settings.get("music_enabled", True):
            return
        try:
            import pyglet

            path = self._theme_path(context)
            self.source = pyglet.media.load(str(path), streaming=False)
            self.player = self.source.play()

            def replay(*_args):
                if self.context == context and self.player is not None:
                    self.player.seek(0)
                    self.player.play()

            self.player.on_eos = replay
            self._apply_volume()
        except Exception:
            self.player = None
            self.source = None

    def stop(self) -> None:
        if self.player is not None:
            try:
                self.player.pause()
                self.player.delete()
            except Exception:
                pass
        self.player = None
        self.source = None

    def refresh(self) -> None:
        """Apply settings immediately without changing the current theme."""
        if self.context is None:
            return
        if not self.session.settings.get("music_enabled", True):
            self.stop()
            return
        self.set_context(self.context)

    def _apply_volume(self) -> None:
        if self.player is not None:
            self.player.volume = max(0.0, min(1.0, float(self.session.settings.get("music_volume", 0.65))))

    def _theme_path(self, context: str) -> Path:
        if context not in self._paths:
            path = Path(tempfile.gettempdir()) / f"smart_racing_{context}_theme.wav"
            if not path.exists():
                self._write_theme(path, context)
            self._paths[context] = path
        return self._paths[context]

    @classmethod
    def _write_theme(cls, path: Path, context: str) -> None:
        menu_notes = (261.63, 329.63, 392.00, 523.25, 392.00, 329.63)
        championship_notes = (196.00, 246.94, 293.66, 392.00, 293.66, 246.94, 220.00, 293.66)
        notes = championship_notes if context == "championship" else menu_notes
        frames = []
        for index in range(cls.SAMPLE_RATE * cls.DURATION):
            time = index / cls.SAMPLE_RATE
            beat = int(time * 2.0) % len(notes)
            note = notes[beat]
            envelope = min(1.0, (time % 0.5) * 18.0) * min(1.0, ((0.5 - (time % 0.5)) * 18.0))
            tone = math.sin(2.0 * math.pi * note * time) * 0.16
            bass = math.sin(2.0 * math.pi * note / 2.0 * time) * 0.06
            frames.append(int(max(-1.0, min(1.0, (tone + bass) * envelope)) * 32767))
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(cls.SAMPLE_RATE)
            output.writeframes(b"".join(sample.to_bytes(2, "little", signed=True) for sample in frames))
