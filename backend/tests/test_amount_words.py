from app.services.amount_words import amount_in_words


def test_lakh():
    assert amount_in_words(1654200) == "Sixteen Lakh Fifty Four Thousand Two Hundred Only"


def test_lakh_round():
    assert amount_in_words(2138000) == "Twenty One Lakh Thirty Eight Thousand Only"


def test_thousand():
    assert amount_in_words(75200) == "Seventy Five Thousand Two Hundred Only"


def test_crore():
    assert amount_in_words(12345678) == (
        "One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight Only"
    )


def test_rounds_paise_down():
    assert amount_in_words(100.49) == "One Hundred Only"


def test_rounds_paise_up():
    assert amount_in_words(100.50) == "One Hundred One Only"


def test_zero():
    assert amount_in_words(0) == "Zero Only"
