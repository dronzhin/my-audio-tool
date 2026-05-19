import click
from pathlib import Path
from src.audio_splitter.splitter import AudioSplitter


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--mode", type=click.Choice(["duration", "timestamps", "silence"]), required=True,
              help="Splitting mode")
@click.option("--out", default="output_chunks", type=click.Path(file_okay=False),
              help="Output directory")
@click.option("--chunk", default=300.0, type=float,
              help="Chunk duration in seconds (for duration mode)")
@click.option("--min-silence", default=1000, type=int,
              help="Minimum silence length in ms (for silence mode)")
@click.option("--thresh", default=-40, type=int,
              help="Silence threshold in dB (for silence mode)")
@click.option("--format", "out_format", default=None,
              help="Output format (mp3, wav, flac). Defaults to input format.")
def cli(input_file, mode, out, chunk, min_silence, thresh, out_format):
    """🎧 Audio Splitter CLI - Split audio files by duration, timestamps, or silence."""
    try:
        splitter = AudioSplitter(input_file, output_dir=out, output_format=out_format)
        click.echo(f"📂 Loaded: {Path(input_file).name} ({splitter.duration_sec:.1f}s)")

        if mode == "duration":
            click.echo(f"⏱️ Splitting by duration: {chunk}s per chunk...")
            files = splitter.split_by_duration(chunk_sec=chunk)
        elif mode == "silence":
            click.echo(f"🔇 Splitting by silence: min={min_silence}ms, thresh={thresh}dB...")
            files = splitter.split_by_silence(min_silence_ms=min_silence, silence_thresh_db=thresh)
        elif mode == "timestamps":
            click.echo("⚠️ Timestamps mode requires a JSON/CSV file. Use --timestamps-file option (coming soon).")
            return

        click.echo(f"✅ Done! {len(files)} files saved to '{out}/'")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
