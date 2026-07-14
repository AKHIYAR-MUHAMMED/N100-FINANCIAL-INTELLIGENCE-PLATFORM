import pandas as pd

from src.screener.engine import ScreenerEngine


def test_screener_engine_init():
    engine = ScreenerEngine()
    assert engine.config is not None
    assert "presets" in engine.config
    assert "metrics" in engine.config


def test_screener_config_presets():
    engine = ScreenerEngine()
    presets = engine.config["presets"]
    assert "quality_compounder" in presets
    assert "value_pick" in presets
    assert "growth_accelerator" in presets
    assert "dividend_champion" in presets
    assert "debt_free_blue_chip" in presets
    assert "turnaround_watch" in presets


def test_screener_engine_load_data():
    engine = ScreenerEngine()
    df_all = engine.load_and_prepare_data()
    assert isinstance(df_all, pd.DataFrame)
    assert not df_all.empty

    # Check that derived columns exist
    assert "dividend_yield" in df_all.columns
    assert "market_cap" in df_all.columns
    assert "cfo_pat_ratio" in df_all.columns
    assert "fcf_positive_flag" in df_all.columns
    assert "fcf_cagr" in df_all.columns
    assert "composite_quality_score" in df_all.columns


def test_screener_composite_score_range():
    engine = ScreenerEngine()
    df_all = engine.load_and_prepare_data()
    scores = df_all["composite_quality_score"]
    assert scores.min() >= 0.0
    assert scores.max() <= 100.0


def test_screener_apply_filters():
    engine = ScreenerEngine()
    df_all = engine.load_and_prepare_data()
    latest_df = engine.get_latest_company_data(df_all)

    # Test presets return within acceptable limits (5 to 50)
    for preset_name in engine.config["presets"].keys():
        filtered = engine.apply_preset_filters(latest_df, preset_name)
        assert isinstance(filtered, pd.DataFrame)
        assert len(filtered) >= 5
        assert len(filtered) <= 50

        # Verify sort order is descending by composite score
        scores = filtered["composite_quality_score"].tolist()
        assert scores == sorted(scores, reverse=True)
