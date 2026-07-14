import sqlite3

import pandas as pd

from src.analytics.peer import PeerAnalyzer


def test_peer_analyzer_init():
    analyzer = PeerAnalyzer()
    assert analyzer.peer_df is not None
    assert "ticker" in analyzer.peer_df.columns
    assert "group_name" in analyzer.peer_df.columns
    assert "is_benchmark" in analyzer.peer_df.columns


def test_peer_analyzer_get_group():
    analyzer = PeerAnalyzer()
    assert analyzer.get_company_peer_group("COMP01") == "IT Services"
    assert analyzer.get_company_peer_group("COMP02") == "Banking"
    assert analyzer.get_company_peer_group("COMP85") == "No peer group assigned"
    assert analyzer.get_company_peer_group("INVALID") == "No peer group assigned"


def test_peer_percentiles_table_insertion():
    analyzer = PeerAnalyzer()
    analyzer.calculate_percentiles_and_save()

    conn = sqlite3.connect(analyzer.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM peer_percentiles")
    count = cursor.fetchone()[0]
    assert count > 0

    cursor.execute("SELECT * FROM peer_percentiles LIMIT 1")
    row = cursor.fetchone()
    assert len(row) == 6
    conn.close()


def test_peer_ranking_correctness():
    conn = sqlite3.connect("data/db/nifty100.db")

    query = """
        SELECT company_id, value, percentile_rank
        FROM peer_percentiles
        WHERE peer_group_name = 'IT Services' AND metric = 'roe' AND year = 2023
        ORDER BY value DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        pct_ranks = df["percentile_rank"].tolist()
        for i in range(len(pct_ranks) - 1):
            assert pct_ranks[i] >= pct_ranks[i + 1]
