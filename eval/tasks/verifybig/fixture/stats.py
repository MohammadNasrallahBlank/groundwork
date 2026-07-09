def median(xs):
    """Median of a list. Bug: for even-length lists it returns the lower of
    the two middle values instead of their average."""
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else s[n // 2 - 1]
