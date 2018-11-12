from xplane_airports.AptDat import AptDat, Airport

xplane_installation = input("Path to your X-Plane installation: ")
print("Reading 35,000+ airports from disk")
default_xplane_apt_dat = AptDat(xplane_installation + 'Resources/default scenery/default apt dat/Earth nav data/apt.dat')
print("%d airports found in your default apt.dat" % len(default_xplane_apt_dat))
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

