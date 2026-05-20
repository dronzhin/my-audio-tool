import time
from pathlib import Path

import click

from audio_splitter.splitter import AudioSplitter


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--mode", type=click.Choice(["duration", "timestamps", "silence"]),
              default="duration", show_default=True,
              help="Splitting mode")
@click.option("--out", default=None, type=click.Path(file_okay=False),
              help="Output directory (default: <input_filename>/)")
@click.option("--chunk", default=900.0, type=float,
              help="Chunk duration in seconds (default: 900 = 15 min)")
@click.option("--min-silence", default=1000, type=int,
              help="Minimum silence length in ms (for silence mode)")
@click.option("--thresh", default=-40, type=int,
              help="Silence threshold in dB (for silence mode)")
@click.option("--format", "out_format", default=None,
              help="Output format (mp3, wav, flac). Defaults to input format.")
@click.option("--smart/--no-smart", default=True,
              help="Search for silence near target point to avoid cutting words (default: enabled)")
@click.option("--tolerance", default=15.0, type=float,
              help="Silence search window ±seconds from target point (default: 15)")
def cli(input_file, mode, out, chunk, min_silence, thresh, out_format, smart, tolerance):
    """🎧 Audio Splitter CLI - Split audio files by duration, timestamps, or silence."""
    try:
        # 📁 Динамическая папка по умолчанию: имя файла без расширения
        if out is None:
            out = Path(input_file).stem

        splitter = AudioSplitter(input_file, output_dir=out, output_format=out_format)
        click.echo(f"📂 Loaded: {Path(input_file).name} ({splitter.duration_sec:.1f}s) → {out}/")

        start_time = time.perf_counter()  # ⏱️ Старт таймера

        if mode == "duration":
            click.echo(f"⏱️ Splitting by duration: {chunk}s (smart={smart}, tolerance=±{tolerance}s)...")
            files = splitter.split_by_duration(
                chunk_sec=chunk, smart=smart, tolerance_sec=tolerance,
                min_silence_ms=min_silence, silence_thresh_db=thresh
            )
        elif mode == "silence":
            click.echo(f"🔇 Splitting by silence: min={min_silence}ms, thresh={thresh}dB...")
            files = splitter.split_by_silence(min_silence_ms=min_silence, silence_thresh_db=thresh)
        elif mode == "timestamps":
            click.echo("⚠️ Timestamps mode requires a JSON/CSV file. Use --timestamps-file option (coming soon).")
            return

        elapsed = time.perf_counter() - start_time
        click.echo(f"✅ Done! {len(files)} files saved to '{out}/'")
        click.echo(f"⏱️ Total time: {elapsed:.2f}s")
    except KeyboardInterrupt:
        click.echo("\n⛔ Interrupted by user.")
        raise SystemExit(130) from None
    except Exception as e:
        raise click.ClickException(str(e)) from e

if __name__ == "__main__":
    cli()
