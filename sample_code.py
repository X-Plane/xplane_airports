from xplane_airports.AptDat import AptDat, Airport
from pathlib import Path

xplane_installation = Path(input("Path to your X-Plane installation: "))
assert xplane_installation.is_dir(), f"{xplane_installation} does not exist or is not a directory"
print("Reading 35,000+ airports from disk (this will take awhile)")
default_xplane_apt_dat = AptDat(xplane_installation / 'Resources/default scenery/default apt dat/Earth nav data/apt.dat')
print(f"{len(default_xplane_apt_dat)} %d airports found in your default apt.dat")
print()


ksea = default_xplane_apt_dat['KSEA']
""":type ksea: Airport"""
print("KSEA's airport data on disk begins:")
print(ksea.head())
print()


from xplane_airports.gateway import airports
all_apts = airports()
print("There are %d airports on the X-Plane Scenery Gateway" % len(all_apts))
print("KSEA has the following metadata on the Gateway:")
for key, value in all_apts['KSEA'].items():
    print('\t', key, ':', value)
print()


from xplane_airports.gateway import scenery_pack, GatewayApt
ksea_recommended_pack = scenery_pack('KSEA')
""":type ksea_recommended_pack: GatewayApt"""
print("KSEA downloaded from the Gateway begins:")
print(ksea_recommended_pack.apt.head())

