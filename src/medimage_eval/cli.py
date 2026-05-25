"""Command-line entry point: medimage-eval <command>."""

from __future__ import annotations

import click

import medimage_eval


@click.group()
@click.version_option(medimage_eval.__version__, prog_name="medimage-eval")
def main() -> None:
    """medimage-eval — audit-grade evaluation substrate."""


@main.command()
def smoke() -> None:
    """Run a hermetic smoke pass over the substrate primitives."""
    from medimage_eval.reporting import cohens_kappa, wilson_ci

    kappa = cohens_kappa([1, 0, 1, 1, 0], [1, 0, 0, 1, 0])
    low, high = wilson_ci(8, 10)
    click.echo(f"kappa(toy) = {kappa:+.4f}")
    click.echo(f"wilson(8/10) = [{low:.4f}, {high:.4f}]")
    click.echo("substrate smoke OK")


if __name__ == "__main__":
    main()
