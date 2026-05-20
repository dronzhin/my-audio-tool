import pytest
from pydub import AudioSegment

from audio_splitter.splitter import AudioSplitter


@pytest.fixture
def sample_audio(tmp_path):
    """Create a 2-second silent WAV file for testing."""
    audio = AudioSegment.silent(duration=2000, frame_rate=44100)
    file_path = tmp_path / "test.wav"
    audio.export(file_path, format="wav")
    return file_path


def test_init_valid_file(sample_audio, tmp_path):
    splitter = AudioSplitter(str(sample_audio), output_dir=str(tmp_path / "out"))
    assert splitter.duration_sec == pytest.approx(2.0, abs=0.1)
    assert splitter.output_format == "wav"


def test_init_invalid_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        AudioSplitter("nonexistent.mp3")


def test_split_by_duration(sample_audio, tmp_path):
    out_dir = tmp_path / "duration_out"
    splitter = AudioSplitter(str(sample_audio), output_dir=str(out_dir))
    files = splitter.split_by_duration(chunk_sec=1.0)
    assert len(files) == 2
    assert all(f.exists() for f in files)
    assert all(f.suffix == ".wav" for f in files)


def test_split_by_silence(sample_audio, tmp_path):
    out_dir = tmp_path / "silence_out"
    splitter = AudioSplitter(str(sample_audio), output_dir=str(out_dir))
    files = splitter.split_by_silence(min_silence_ms=500, silence_thresh_db=-50)
    assert len(files) >= 1
    assert all(f.exists() for f in files)
