def get_price(sku):
    # profile A answer: in-memory dict, per-process
    return _CACHE.get(sku)

_CACHE = {}
