import numpy as np

lats = [20, 20, 20, 30, 30, 30, 30, 50, 50, 70]
lons = [0, 15, 30, 0, 10, 20, 30, 0, 30, 15]


def test_lats():
    global lats, lons
    mylats = np.array(lats)
    mylons = np.array(lons)
    (n_lats,) = mylats.shape
    diffs = np.diff(mylats)
    assert np.all(diffs >= 0) or np.all(diffs <= 0)
    levs = np.array(sorted(set(mylats)))
    (n_levs,) = levs.shape
    hits = mylats.reshape(n_lats, 1) == levs.reshape(1, n_levs)
    lev_counts = hits.sum(axis=0)
    print("lev_counts =", lev_counts)
    for lev in levs:
        lons_at_lev = mylons[lats == lev]
        # check lons within each lev are distinct and monotonic
        n_lons_at_lev = len(lons_at_lev)
        if n_lons_at_lev > 1:
            assert len(set(lons_at_lev)) == n_lons_at_lev
            diffs = np.diff(lons_at_lev)
            assert np.all(diffs >= 0) or np.all(diffs <= 0)
