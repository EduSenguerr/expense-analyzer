from expense_analyzer.normalize import normalize_description


def test_normalize_removes_trailing_numbers() -> None:
    assert normalize_description("Starbucks #1234") == "STARBUCKS"


def test_normalize_removes_noise_words() -> None:
    assert normalize_description("POS DEBIT Netflix") == "NETFLIX"
