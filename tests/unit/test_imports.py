def test_imports():
    """Verify core components can be imported."""
    import bubble_sim.cli
    import bubble_sim.version

    assert bubble_sim.version.__version__ == "0.1.0"
