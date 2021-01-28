def flatten(arr: list, type=object):
    res = []

    for _ in arr:
        if isinstance(_, type) and not isinstance(_, list):
            res.append(_)
        else:
            res += flatten(_)

    return res

