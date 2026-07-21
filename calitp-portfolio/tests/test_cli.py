from calitp_portfolio.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "calitp-portfolio" in result.stdout
