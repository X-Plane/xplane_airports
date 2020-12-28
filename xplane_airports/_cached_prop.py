# Python 3.6-compatible wrapper for using cached_property
# If you're pre-Python 3.8, you get no caching. You'll be okay.
try:
    import functools
    apt_cached_property = functools.cached_property
except:
    apt_cached_property = property
