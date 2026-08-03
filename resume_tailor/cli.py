"""Command-line entry point for resume-tailor."""

import click

from . import __version__


@click.group()
@click.version_option(__version__, prog_name="resume-tailor")
def main() -> None:
    """Generate job-tailored one-page resumes from data/master.yaml."""


if __name__ == "__main__":
    main()
