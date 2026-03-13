from typer.testing import CliRunner

from bubble_sim.cli import app

runner = CliRunner()


def test_cli_version():
    """Verify CLI version command works."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "bubble-sim version: 0.1.0" in result.stdout


def test_cli_check():
    """Verify CLI check command works."""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Environment check: OK" in result.stdout
