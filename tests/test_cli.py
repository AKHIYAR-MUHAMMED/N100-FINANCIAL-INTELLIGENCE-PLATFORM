import pytest
from pathlib import Path
from src.cli import build_parser, main, cmd_status, cmd_risk


def test_cli_parser_help(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])


def test_cli_status_command(capsys):
    db_path = Path("data/db/nifty100.db")
    ret = main(["--db", str(db_path), "status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "BlueStocks Data Foundation" in captured.out
    assert "Table Record Counts" in captured.out


def test_cli_risk_command(capsys):
    ret = main(["risk", "--ticker", "COMP01", "--simulations", "100"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Risk Profile: COMP01" in captured.out
    assert "Monte Carlo 5-Year Trajectory" in captured.out


def test_cli_no_command(capsys):
    ret = main([])
    assert ret == 0


def test_cli_export_command(capsys):
    ret = main(["export", "--ticker", "COMP01", "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "COMP01" in captured.out

