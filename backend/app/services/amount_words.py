from decimal import ROUND_HALF_UP, Decimal

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _below_hundred(n: int) -> list[str]:
    if n < 20:
        return [_ONES[n]] if n else []
    return [_TENS[n // 10]] + ([_ONES[n % 10]] if n % 10 else [])


def _below_thousand(n: int) -> list[str]:
    words = [_ONES[n // 100], "Hundred"] if n >= 100 else []
    return words + _below_hundred(n % 100)


def _indian_words(n: int) -> list[str]:
    if n >= 10_000_000:
        return _indian_words(n // 10_000_000) + ["Crore"] + _indian_words(n % 10_000_000)
    words = []
    for divisor, label in ((100_000, "Lakh"), (1_000, "Thousand")):
        if n >= divisor:
            words += _below_hundred(n // divisor) + [label]
            n %= divisor
    return words + _below_thousand(n)


def amount_in_words(amount) -> str:
    """Whole-rupee amount in Indian numbering, e.g. 'Twenty One Lakh Only'."""
    n = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    words = _indian_words(n) if n else ["Zero"]
    return " ".join(words) + " Only"
