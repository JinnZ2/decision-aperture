def get_price(sku):
    # profile B answer: same structure, different log line wording
    return _CACHE.get(sku)  # cache lookup

_CACHE = {}
