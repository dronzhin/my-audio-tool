import subprocess
import tempfile
from pathlib import Path

from audio_splitter.splitter import AudioSplitter


def create_dummy_audio(path: Path, duration_sec: int = 2):
    """Создает тихий MP3-файл заданной длительности через FFmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=stereo:d={duration_sec}",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "9",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def test_init_creates_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.mp3"
        output_dir = Path(tmpdir) / "output"

        # Создаем фиктивный файл
        create_dummy_audio(input_file)

        # Инициализируем сплиттер
        splitter = AudioSplitter(str(input_file), output_dir=str(output_dir))

        assert splitter.output_dir.exists()
        assert splitter.duration_sec > 0


def test_split_by_duration_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.mp3"
        output_dir = Path(tmpdir) / "chunks"

        # Создаем файл длиной 5 секунд
        create_dummy_audio(input_file, duration_sec=5)

        splitter = AudioSplitter(str(input_file), output_dir=str(output_dir))

        # Нарезаем по 2 секунды (должно получиться 3 файла: 2с, 2с, 1с)
        files = splitter.split_by_duration(chunk_sec=2, smart=False)

        assert len(files) == 3
        for f in files:
            assert f.exists()
            assert f.suffix == ".mp3"
