def calculate_total(prices):
    """Sum of prices"""
    return sum(prices)


def apply_discount(total, percent):
    """Apply discount; percent must be between 0 and 100"""
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return total * (1 - percent / 100)


def calculate_tax(price, country, is_business, has_exemption):
    if country == "DE":
        if is_business:
            if has_exemption:
                return 0
            return price * 0.19
        return price * 0.19
    if country == "FR":
        if is_business:
            return price * 0.20
        return price * 0.20
    return price * 0.10
