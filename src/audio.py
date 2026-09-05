"""Menu sounds, synthesised at start-up so the project ships no audio files.

Each sound is a decaying sine burst built as a numpy array and handed straight to the mixer,
the same way the wall textures are generated rather than loaded.
"""

import numpy as np
import pygame

from src import settings

SELECT = "select"  # a level that opens, or the quit button
LOCKED = "locked"  # a level card that is still shut

ATTACK_SAMPLES = 64  # ramp in, so the waveform never starts on a step and pops
DECAY = 5.0  # e-folds across a burst, leaving it at 0.7% by the end
FULL_SCALE = 32767  # peak of a signed 16-bit sample

_sounds = {}


def _burst(frequency, seconds, rate):
    """One sine burst with a soft attack and an exponential decay, in -1..1."""
    time = np.arange(int(rate * seconds), dtype=np.float64) / rate
    envelope = np.exp(-time * (DECAY / seconds))
    ramp = min(ATTACK_SAMPLES, len(envelope))
    envelope[:ramp] *= np.linspace(0.0, 1.0, ramp)
    return np.sin(2.0 * np.pi * frequency * time) * envelope


def _to_sound(samples, channels):
    """Normalise a waveform to the UI volume and hand it to the mixer."""
    frames = (samples / np.max(np.abs(samples)) * settings.UI_VOLUME * FULL_SCALE).astype(np.int16)
    if channels > 1:
        frames = np.repeat(frames[:, None], channels, axis=1)
    return pygame.sndarray.make_sound(np.ascontiguousarray(frames))


def load():
    """Build the menu sounds; False when the machine has no usable audio device."""
    mixer = pygame.mixer.get_init()
    if mixer is None:
        return False
    rate, _, channels = mixer
    try:
        # a rising pair reads as confirmation, a low pair as refusal
        _sounds[SELECT] = _to_sound(np.concatenate([_burst(660.0, 0.045, rate),
                                                    _burst(990.0, 0.075, rate)]), channels)
        _sounds[LOCKED] = _to_sound(_burst(170.0, 0.13, rate)
                                    + 0.35 * _burst(85.0, 0.13, rate), channels)
    except (pygame.error, ValueError):  # a mixer format numpy cannot be shaped into
        _sounds.clear()
        return False
    return True


def play(name):
    """Play one menu sound, staying silent when audio was never available."""
    sound = _sounds.get(name)
    if sound is not None:
        sound.play()


def wait(name):
    """Block for a sound's length, so a click is not cut off by the window closing."""
    sound = _sounds.get(name)
    if sound is not None:
        pygame.time.wait(int(sound.get_length() * 1000))
