"""
低調輕柔 RPG 音效管理器 (支援一鍵靜音與老闆鍵靜音)
"""

import math
import random
import struct
import pygame


class SoundManager:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.volume = 0.35  # 預設舒適溫和音量 (0.0 ~ 1.0)
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._generate_sounds()
            self.set_volume(self.volume)
        except Exception as e:
            print(f"[SoundManager] 音訊設備未就緒，使用純靜音模式: {e}")
            self.enabled = False

    def set_volume(self, vol: float):
        """設置全域音效音量 (0.0 ~ 1.0)"""
        self.volume = max(0.0, min(1.0, float(vol)))
        for snd in self.sounds.values():
            try:
                snd.set_volume(self.volume)
            except Exception:
                pass

    def _create_sound_from_samples(self, samples, sample_rate=22050):
        packed_data = bytearray()
        for s in samples:
            val = max(-32767, min(32767, int(s)))
            frame = struct.pack("<hh", val, val)
            packed_data.extend(frame)
        return pygame.mixer.Sound(buffer=bytes(packed_data))

    def _generate_sounds(self):
        sample_rate = 22050

        # 1. 普通打擊聲 (短促刀劍劈擊)
        duration = 0.05
        total_samples = int(sample_rate * duration)
        samples = []
        phase = 0.0
        for i in range(total_samples):
            t = i / total_samples
            freq = 420.0 - 240.0 * t
            phase += 2.0 * math.pi * freq / sample_rate
            noise = random.uniform(-0.4, 0.4)
            amp = ((1.0 - t) ** 1.8) * 0.22
            samples.append(amp * 32767 * (math.sin(phase) * 0.6 + noise * 0.4))
        self.sounds["hit"] = self._create_sound_from_samples(samples)

        # 2. 暴擊聲 (清脆金屬迴響)
        duration = 0.12
        total_samples = int(sample_rate * duration)
        samples = []
        phase1, phase2 = 0.0, 0.0
        for i in range(total_samples):
            t = i / total_samples
            phase1 += 2.0 * math.pi * 880.0 / sample_rate  # A5
            phase2 += 2.0 * math.pi * 1320.0 / sample_rate # E6
            amp = ((1.0 - t) ** 2) * 0.25
            samples.append(amp * 32767 * (math.sin(phase1) * 0.6 + math.sin(phase2) * 0.4))
        self.sounds["crit"] = self._create_sound_from_samples(samples)

        # 3. 升級音效 (明亮的三和弦琶音 C5 -> G5 -> C6)
        duration = 0.3
        total_samples = int(sample_rate * duration)
        samples = []
        notes = [523.25, 783.99, 1046.50]
        phase = 0.0
        for i in range(total_samples):
            t = i / total_samples
            note_idx = min(int(t * 3), 2)
            phase += 2.0 * math.pi * notes[note_idx] / sample_rate
            amp = ((1.0 - (t * 3) % 1.0) ** 1.3) * 0.22
            samples.append(amp * 32767 * math.sin(phase))
        self.sounds["levelup"] = self._create_sound_from_samples(samples)

        # 4. 戰利品掉落聲 (清脆金幣微響)
        duration = 0.08
        total_samples = int(sample_rate * duration)
        samples = []
        phase = 0.0
        for i in range(total_samples):
            t = i / total_samples
            freq = 950.0 + 300.0 * t
            phase += 2.0 * math.pi * freq / sample_rate
            amp = (1.0 - t) * 0.16
            samples.append(amp * 32767 * math.sin(phase))
        self.sounds["loot"] = self._create_sound_from_samples(samples)

        # 5. 鐵匠鍛造強化聲 (打鐵叮噹聲)
        duration = 0.14
        total_samples = int(sample_rate * duration)
        samples = []
        phase = 0.0
        for i in range(total_samples):
            t = i / total_samples
            phase += 2.0 * math.pi * 1174.66 / sample_rate # D6
            noise = random.uniform(-0.2, 0.2) * (1.0 - t)
            amp = ((1.0 - t) ** 2.2) * 0.25
            samples.append(amp * 32767 * (math.sin(phase) + noise))
        self.sounds["forge"] = self._create_sound_from_samples(samples)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_all()
        return self.muted

    def stop_all(self):
        if self.enabled:
            pygame.mixer.stop()

    def play(self, sound_name):
        if not self.enabled or self.muted:
            return
        sound = self.sounds.get(sound_name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass


# 全域單例
sound_mgr = SoundManager()
