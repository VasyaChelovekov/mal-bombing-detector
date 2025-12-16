"""CLI version command tests."""

from typer.testing import CliRunner

from src._version import __version__
from src.cli.commands import app


def test_version_command_prints_package_version() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
