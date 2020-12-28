import gc
import timeit
from xplane_airports.AptDat import AptDat
from pathlib import Path

xplane_installation = Path('/Users/tyler/design')
assert xplane_installation.is_dir(), f"{xplane_installation} does not exist or is not a directory"

iterations = 3
print(f"Repeating {iterations} iterations of parsing 35,000+ airports from disk (this will take awhile)")

# Tyler observes: We can't just run a bunch of iterations using timeit(), because it disables GC,
# and we use gigabytes of RAM per parse of our giant files.
#
# It's not realistic to benchmark us parsing multiple 300 MB files... there are only so many airports in the world!
total_seconds = 0
for i in range(iterations):
    total_seconds += timeit.timeit(lambda: AptDat(xplane_installation / 'Resources/default scenery/default apt dat/Earth nav data/apt.dat'), number=1)
    gc.collect()

print(f"Average time over {iterations} runs: {total_seconds / iterations}")
