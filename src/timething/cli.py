from pathlib import Path

import click

from timething import dataset, job, text, utils, cutter  # type: ignore


@click.group()
def cli():
    """Timething is a library for aligning text transcripts with audio.
    Use one of the commands listed below to get started.
    """
    pass


@cli.command()
@click.option(
    "--model",
    default="english",
    show_default=True,
    help="Key in timething/models.yaml.",
)
@click.option(
    "--metadata",
    required=True,
    type=click.Path(exists=True),
    help="Full path to metadata csv.",
)
@click.option(
    "--alignments-dir",
    required=True,
    type=click.Path(exists=True),
    help="Dir to write results to.",
)
@click.option(
    "--batch-size",
    required=True,
    type=int,
    help="Number of examples per batch",
)
@click.option(
    "--n-workers",
    required=True,
    type=int,
    help="Number of worker processes to use",
)
@click.option(
    "--use-gpu",
    type=bool,
    default=True,
    show_default=True,
    help="Use the gpu, if we have one",
)
def align(
    model: str,
    metadata: str,
    alignments_dir: str,
    batch_size: int,
    n_workers: int,
    use_gpu: bool,
):
    """Align text transcripts with audio.

    You provide the audio files, as well as a text file with the complete text
    transcripts. Timething will output a list of time-codes for each word and
    character that indicate when this word or letter was spoken in the audio
    you provided.
    """

    # retrieve the config for the given model
    cfg = utils.load_config(model)

    # construct the dataset
    ds = dataset.SpeechDataset(Path(metadata), cfg.sampling_rate)

    # construct and run the job
    click.echo("setting up aligment job...")
    j = job.Job(
        cfg,
        ds,
        Path(alignments_dir),
        batch_size=batch_size,
        n_workers=n_workers,
        gpu=use_gpu,
    )

    # construct the generic model text cleaner
    ds.clean_text_fn = text.TextCleaner(cfg.language, j.aligner.vocab())

    # go
    click.echo("starting aligment job...")
    j.run()


@cli.command()
@click.option(
    "--from-meta",
    required=True,
    type=click.Path(exists=True),
    help="Full path to the source dataset metadata csv.",
)
@click.option(
    "--to-meta",
    required=True,
    help="Full path to the destination dataset metadata csv; will be created.",
)
@click.option(
    "--alignments-dir",
    required=True,
    type=click.Path(exists=True),
    help="Aligments dir for the source dataset.",
)
@click.option(
    "--cut-threshold-seconds",
    default=8.0,
    type=float,
    help="Maximum duration. Source recordings over this will be recut.",
)
@click.option(
    "--pause-threshold-model-frames",
    default=20,
    type=int,
    help="Lowest value of model frames between words before snipping here.",
)
def recut(
    from_meta: str,
    to_meta: str,
    alignments_dir: str,
    cut_threshold_seconds: float,
    pause_threshold_model_frames: int
):
    """Recut an existing dataset.

    Sometimes you want smaller files, like when training a machine learning
    model. This command will cut long recordings into smaller ones, such that
    the cut threshold in seconds is never exceeded. Will write out a new
    dataset with split audio and split texts.
    """

    cutter.dataset_recut(
        Path(from_meta),
        Path(to_meta),
        Path(alignments_dir),
        cut_threshold_seconds,
        pause_threshold_model_frames,
    )


if __name__ == "__main__":
    cli(prog_name='timething')  # type: ignore
