from memento import run


def test_run():
    matrix = {
        "parameters": {"param1": [1, 2, 3], "param2": [4, 5, 6]},
        "exclude": [{"param1": 3, "param2": 6}],
    }

    configurations = run(matrix)
    expected = [
        {"param1": 1, "param2": 4},
        {"param1": 1, "param2": 5},
        {"param1": 1, "param2": 6},
        {"param1": 2, "param2": 4},
        {"param1": 2, "param2": 5},
        {"param1": 2, "param2": 6},
        {"param1": 3, "param2": 4},
        {"param1": 3, "param2": 5},
        # Excluded
        # {"param1": 3, "param2": 6},
    ]

    assert len(configurations) == len(expected)

    for config, expected in zip(configurations, expected):
        assert config.asdict() == expected
