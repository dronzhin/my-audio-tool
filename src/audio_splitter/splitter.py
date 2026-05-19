import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional
from tqdm import tqdm


class AudioSplitter:
    """FFmpeg-native audio splitter. Streams data, uses ~20MB RAM regardless of file size."""

    def __init__(self, input_path: str, output_dir: str = "output_chunks", output_format: Optional[str] = None):
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.input_ext = self.input_path.suffix.lstrip('.').lower()
        self.output_format = output_format or self.input_ext or 'mp3'
        self.duration_sec = self._get_duration()

    def _get_duration(self) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(self.input_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())

    def _detect_silences(self, min_silence_sec: float, thresh_db: int) -> List[Tuple[float, float]]:
        cmd = [
            "ffmpeg", "-i", str(self.input_path),
            "-af", f"silencedetect=noise={thresh_db}dB:d={min_silence_sec}",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.e+-]+)", res.stderr)]
        ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.e+-]+)", res.stderr)]

        silences = []
        for i, s in enumerate(starts):
            e = ends[i] if i < len(ends) else self.duration_sec
            silences.append((s, e))
        return silences

    def _find_best_split(self, target: float, tolerance: float, silences: List[Tuple[float, float]]) -> float:
        win_start, win_end = target - tolerance, target + tolerance
        candidates = [(s, e) for s, e in silences if s < win_end and e > win_start]
        if not candidates:
            return target
        best = min(candidates, key=lambda x: abs((x[0] + x[1]) / 2 - target))
        return (best[0] + best[1]) / 2

    def _export_chunk(self, start: float, end: float, out_path: Path) -> None:
        # Потоковая нарезка через FFmpeg. -c copy избегает перекодирования и экономит RAM/CPU.
        # Если формат вывода отличается от входа, FFmpeg автоматически перекодирует (всё равно потоково).
        cmd = [
            "ffmpeg", "-y", "-i", str(self.input_path),
            "-ss", str(start), "-to", str(end),
            "-avoid_negative_ts", "1"
        ]
        if self.output_format == self.input_ext:
            cmd.extend(["-c", "copy"])
        cmd.append(str(out_path))

        subprocess.run(cmd, capture_output=True, check=True)

    def split_by_duration(self, chunk_sec: float = 900, prefix: str = "chunk",
                          smart: bool = True, tolerance_sec: float = 15.0,
                          min_silence_ms: int = 500, silence_thresh_db: int = -40) -> List[Path]:
        exported = []
        targets = [i * chunk_sec for i in range(1, int(self.duration_sec / chunk_sec) + 1)]
        actual_splits = [0.0]

        silences = []
        if smart:
            with tqdm(total=1, desc="🔍 Detecting silence", bar_format="{desc}: {bar}") as pbar:
                silences = self._detect_silences(min_silence_ms / 1000, silence_thresh_db)
                pbar.update(1)

            for target in tqdm(targets, desc="📐 Calculating split points", unit="pt"):
                best = self._find_best_split(target, tolerance_sec, silences)
                best = max(best, actual_splits[-1] + 1.0)
                actual_splits.append(best)
        else:
            actual_splits.extend(targets)

        actual_splits.append(self.duration_sec)

        for i in tqdm(range(len(actual_splits) - 1), desc=f"⏳ Exporting {prefix}", unit="chunk"):
            start, end = actual_splits[i], actual_splits[i + 1]
            out_path = self.output_dir / f"{prefix}_{i + 1:03d}.{self.output_format}"
            self._export_chunk(start, end, out_path)
            exported.append(out_path)

        return exported

    def split_by_timestamps(self, timestamps: List[Tuple[float, float]], prefix: str = "part") -> List[Path]:
        exported = []
        for i, (start, end) in enumerate(tqdm(timestamps, desc=f"⏳ Exporting {prefix}", unit="chunk"), start=1):
            if start < 0 or end > self.duration_sec or start >= end:
                continue
            out_path = self.output_dir / f"{prefix}_{i:03d}.{self.output_format}"
            self._export_chunk(start, end, out_path)
            exported.append(out_path)
        return exported

    def split_by_silence(self, min_silence_ms: int = 1000, silence_thresh_db: int = -40,
                         keep_silence_ms: int = 500, prefix: str = "silence") -> List[Path]:
        silences = self._detect_silences(min_silence_ms / 1000, silence_thresh_db)
        if not silences:
            out_path = self.output_dir / f"{prefix}_001.{self.output_format}"
            self._export_chunk(0, self.duration_sec, out_path)
            return [out_path]

        # Аудио-чанки находятся МЕЖДУ паузами
        audio_ranges = []
        prev_end = 0.0
        for s_start, s_end in silences:
            if s_start > prev_end + 0.1:
                audio_ranges.append((prev_end, s_start))
            prev_end = s_end
        if self.duration_sec > prev_end + 0.1:
            audio_ranges.append((prev_end, self.duration_sec))

        exported = []
        for i, (start, end) in enumerate(tqdm(audio_ranges, desc=f"⏳ Exporting {prefix}", unit="chunk"), start=1):
            out_path = self.output_dir / f"{prefix}_{i:03d}.{self.output_format}"
            self._export_chunk(start, end, out_path)
            exported.append(out_path)
        return exported