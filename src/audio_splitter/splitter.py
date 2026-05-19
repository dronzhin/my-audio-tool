from pathlib import Path
from typing import List, Tuple, Optional
from pydub import AudioSegment
from pydub.silence import split_on_silence


class AudioSplitter:
    """Core audio splitting engine."""

    def __init__(self, input_path: str, output_dir: str = "output_chunks", output_format: Optional[str] = None):
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.audio = AudioSegment.from_file(self.input_path)
        self.duration_sec = len(self.audio) / 1000.0
        self.output_format = output_format or self.input_path.suffix.lstrip('.') or 'mp3'

    def split_by_duration(self, chunk_sec: float = 300, prefix: str = "chunk") -> List[Path]:
        chunk_ms = int(chunk_sec * 1000)
        chunks = [self.audio[i:i + chunk_ms] for i in range(0, len(self.audio), chunk_ms)]
        return self._export_chunks(chunks, prefix)

    def split_by_timestamps(self, timestamps: List[Tuple[float, float]], prefix: str = "part") -> List[Path]:
        chunks = []
        for start, end in timestamps:
            if start < 0 or end > self.duration_sec or start >= end:
                continue
            chunks.append(self.audio[int(start * 1000):int(end * 1000)])
        return self._export_chunks(chunks, prefix)

    def split_by_silence(self, min_silence_ms: int = 1000, silence_thresh_db: int = -40,
                         keep_silence_ms: int = 500, prefix: str = "silence") -> List[Path]:
        chunks = split_on_silence(
            self.audio,
            min_silence_len=min_silence_ms,
            silence_thresh=silence_thresh_db,
            keep_silence=keep_silence_ms
        )
        if not chunks:
            chunks = [self.audio]
        return self._export_chunks(chunks, prefix)

    def _export_chunks(self, chunks: List[AudioSegment], prefix: str) -> List[Path]:
        exported = []
        for i, chunk in enumerate(chunks, start=1):
            out_path = self.output_dir / f"{prefix}_{i:03d}.{self.output_format}"
            chunk.export(out_path, format=self.output_format)
            exported.append(out_path)
        return exported
