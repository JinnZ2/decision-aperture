def get_price(sku):
    # profile A answer: return None on miss
    return _CACHE.get(sku)

_CACHE = {}
