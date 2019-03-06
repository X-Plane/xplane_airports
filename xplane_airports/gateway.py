"""
Tools for interfacing with the X-Plane Scenery Gateway's API.

Docs at: https://gateway.x-plane.com/api
"""
import base64
import zipfile
import requests
from dataclasses import dataclass
from enum import IntEnum
from io import BytesIO
from typing import Union
from xplane_airports.AptDat import Airport

GATEWAY_DOMAIN = "https://gateway.x-plane.com"  # The root URL for the Gateway API


class GatewayFeature(IntEnum):
    """
    Features that may be used to tag scenery packs on the Gateway.
    Note that these are subject to frequent addition/removal/change;
    only a few are guaranteed to be stable.
    """
    HasATCFlow = 1  # guaranteed stable
    HasTaxiRoute = 2  # guaranteed stable
    HasNavaidConflict = 3
    AlwaysFlatten = 4
    HasLogTxtIssue = 5
    LRInternalUse = 6  # guaranteed stable
    ExcludeSubmissions = 7  # guaranteed stable
    HasGroundRoutes = 8  # guaranteed stable
    TerrainIncompatible = 10
    RunwayNumberingOrLengthFix = 11
    AlwaysFlattenIneffective = 12
    MajorAirport = 15
    TerrainIncompatibleAtPerimeter = 17
    RunwayNumberingFix = 18
    IconicAirport = 19
    FloatingRunway = 20
    GroundRoutesCertified = 29
    FacadeInjection = 31
    ScenicAirport = 32
    MisusedGroundPolygons = 35
    Top30 = 36
    Top50 = 37
    RunwayInWater = 38
    RunwayUnusable = 40
    TerrainMeshMissing = 41
    LowResolutionTerrainPolygons = 42


@dataclass
class GatewayApt:
    """All the data we get back about an airport when we download a scenery pack via ``scenery_pack()``"""
    apt: Airport                     # Python object with the contents of the apt.dat file
    txt: Union[str, None]            # Contents of the DSF .txt file; airports with no 3D will not include this
    readme: str                      # Contents of the README for this scenery pack
    copying: str                     # Contents of the COPYING instructions for this scenery pack
    pack_metadata: dict              # The JSON object received from the Gateway with metadata about this particular scenery pack
    apt_metadata: Union[dict, None]  # The JSON object received from the Gateway with metadata about the airport this scenery pack represents; None if this hasn't been downloaded (yet)


def airports():
    """
    Queries the Scenery Gateway for all the airports it knows about. Note that the download size is greater than 1 MB.
    Documented at: https://gateway.x-plane.com/api#get-all-airports

    :returns: A dict with metadata on all 35,000+ airports; keys are X-Plane identifiers (which may or may not correspond to ICAO identifiers), and values are various airport metadata.
    :rtype: dict

    >>> airports()['KSEA']
    {'AirportCode': 'KSEA', 'AirportName': 'Seattle Tacoma Intl', 'AirportClass': None, 'Latitude': 47, 'Longitude': -122, 'Elevation': None, 'Deprecated': None, 'DeprecatedInFavorOf': None, 'AcceptedSceneryCount': 2, 'ApprovedSceneryCount': 2, 'ExcludeSubmissions': 0, 'RecommendedSceneryId': 45283, 'Status': 'Scenery Submitted', 'SceneryType': 0, 'SubmissionCount': 2, 'checkedOutBy': None, 'checkOutEndDate': None}

    >>> len(airports()) > 35000
    True
    """
    return {apt['AirportCode']: apt for apt in _gateway_json_request('/apiv1/airports', 'airports')}


def airport(airport_id):
    """
    Queries the Scenery Gateway for metadata on a single airport, plus metadata on all the scenery packs uploaded for that airport.
    Documented at: https://gateway.x-plane.com/api#get-a-single-airport

    :param airport_id: The identifier of the airport on the Gateway (may or may not be an ICAO ID)
    :type airport_id: str

    :returns: A dict with metadata about the airport
    :rtype: dict

    >>> expected_keys = {'icao', 'airportName', 'airportClass', 'latitude', 'longitude', 'elevation', 'acceptedSceneryCount', 'approvedSceneryCount', 'recommendedSceneryId', 'scenery'}
    >>> ksea = airport('KSEA')
    >>> all(key in ksea for key in expected_keys)
    True

    Includes metadata of all scenery packs uploaded for this airport:

    >>> len(airport('KSEA')['scenery']) >= 9
    True

    >>> all_scenery_metadata = airport('KSEA')['scenery']
    >>> first_scenery_pack_metadata = all_scenery_metadata[0]
    >>> expected_keys = {'sceneryId', 'parentId', 'userId', 'userName', 'dateUploaded', 'dateAccepted', 'dateApproved', 'dateDeclined', 'type', 'features', 'artistComments', 'moderatorComments', 'Status'}
    >>> all(key in first_scenery_pack_metadata for key in expected_keys)
    True
    """
    return _gateway_json_request('/apiv1/airport/' + airport_id, 'airport')


def recommended_scenery_packs(selective_apt_ids=None):
    """
    A generator to iterate over the recommended scenery packs for all (or just the selected) airports on the Gateway.
    Downloads and unzips all files into memory.

    :param selective_apt_ids: If ``None``, we will download scenery for all 35,000+ airports; if a list of airport IDs (as returned by ``airports()``), the airports whose recommended packs we should download.
    :type selective_apt_ids: Union[collections.Iterable[str], None]

    :returns: A generator of the recommended scenery packs; each pack contains the same data as a call to ``scenery_pack()`` directly
    :rtype: collections.Iterable[GatewayApt]

    Easily request a subset of airports:

    >>> packs = recommended_scenery_packs(['KSEA', 'KLAX', 'KBOS'])
    >>> len(list(packs)) == 3 and all(isinstance(pack, GatewayApt) for pack in packs)
    True

    Audit airports for specific features:

    >>> all_3d = True
    >>> all_have_atc_flow = True
    >>> all_have_taxi_route = True
    >>> for pack in recommended_scenery_packs(['KATL', 'KORD', 'KDFW', 'KLAX']):
    ...     all_3d &= pack.pack_metadata['type'] == '3D' and pack.txt is not None
    ...     all_have_atc_flow &= GatewayFeature.HasATCFlow in pack.pack_metadata['features'] and pack.apt.has_traffic_flow
    ...     all_have_taxi_route &= GatewayFeature.HasTaxiRoute in pack.pack_metadata['features'] and pack.apt.has_taxi_route
    >>> all_3d and all_have_atc_flow and all_have_taxi_route
    True
    """
    all_airports = airports()
    if selective_apt_ids:
        all_airports = list(apt for apt_id, apt in all_airports.items() if apt_id in selective_apt_ids)

    for airport in all_airports:
        if not airport['Deprecated'] and airport['RecommendedSceneryId']:
            out = scenery_pack(airport['RecommendedSceneryId'])
            out.apt_metadata = airport
            yield out


def scenery_pack(pack_to_download):
    """
    Downloads a single scenery pack, including its apt.dat and any associated DSF from the Gateway, and unzips it into memory.

    :param pack_to_download: If ``int``, the scenery ID of the pack to be downloaded; if ``str``, the airport whose recommended pack we should download.
    :type pack_to_download: Union[str, int]

    :returns: the downloaded files and the metadata about the scenery pack
    :rtype: GatewayApt

    >>> expected_keys = {'sceneryId', 'parentId', 'icao', 'aptName', 'userId', 'userName', 'dateUploaded', 'dateAccepted', 'dateApproved', 'dateDeclined', 'type', 'features', 'artistComments', 'moderatorComments', 'additionalMetadata', 'masterZipBlob'}
    >>> ksea_pack_metadata = scenery_pack('KSEA').pack_metadata
    >>> all(key in ksea_pack_metadata for key in expected_keys)
    True
    >>> scenery_pack('KORD').pack_metadata['type'] in ('3D', '2D')
    True
    >>> all(isinstance(feature, GatewayFeature) for feature in scenery_pack('KMCI').pack_metadata['features'])
    True
    """
    def unzip_pack_to_memory(gateway_zip_stream, pack_md=None, apt_md=None):
        with zipfile.ZipFile(gateway_zip_stream) as z:
            out = GatewayApt(apt=None, txt=None, readme='', copying='', pack_metadata=pack_md, apt_metadata=apt_md)
            for file_name in z.namelist():
                if file_name.endswith('.txt'):
                    out.txt = z.read(file_name).decode("utf-8")
                elif file_name.endswith('.dat'):
                    out.apt = Airport.from_str(z.read(file_name).decode("utf-8"), file_name)
                elif file_name.endswith('.zip'):
                    with zipfile.ZipFile(BytesIO(z.read(file_name))) as zipped_pack:
                        for j, pack_file_name in enumerate(zipped_pack.namelist()):
                            if 'README' in pack_file_name.upper():
                                out.readme = zipped_pack.read(pack_file_name).decode("utf-8")
                            elif 'COPYING' in pack_file_name.upper():
                                out.readme = zipped_pack.read(pack_file_name).decode("utf-8")
            return out

    apt_metadata = None
    if isinstance(pack_to_download, str):
        # If we were given a string airport ID (instead of just a numeric scenery pack ID), we need an extra request to first determine the ID of the recommended pack for this airport
        apt_metadata = _gateway_json_request('/apiv1/airport/' + pack_to_download, 'airport')
        pack_to_download = apt_metadata['recommendedSceneryId']

    pack = _gateway_json_request("/apiv1/scenery/%d" % pack_to_download, 'scenery')
    if pack['features']:
        assert isinstance(pack['features'], str), 'The JSON decoder mangled our text-list of feature IDs'
        pack['features'] = list(GatewayFeature(int(feature_str)) for feature_str in pack['features'].split(',') if int(feature_str) in list(map(int, GatewayFeature)))
    return unzip_pack_to_memory(BytesIO(base64.b64decode(pack['masterZipBlob'])), pack, apt_metadata)


# TODO: API for bulk download and editing of scenery packs


def _gateway_json_request(relative_download_url, expected_key):
    r = requests.get(GATEWAY_DOMAIN + relative_download_url)
    if r.status_code != 200:
        raise AssertionError("HTTP Status %d returned by %s" % (r.status_code, GATEWAY_DOMAIN + relative_download_url))
    return r.json()[expected_key]

