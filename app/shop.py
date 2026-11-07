def calculate_total(prices):
    """Sum of prices"""
    return sum(prices)


def apply_discount(total, percent):
    """Apply discount; percent must be between 0 and 100"""
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return total * (1 - percent / 100)
