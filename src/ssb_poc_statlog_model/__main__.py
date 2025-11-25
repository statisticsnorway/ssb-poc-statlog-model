"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """SSB POC Statlog Model."""


if __name__ == "__main__":
    main(prog_name="ssb-poc-statlog-model")  # pragma: no cover
