"""
Tools for reading, inspecting, and manipulating X-Plane’s airport (apt.dat) files.
"""
import itertools
from contextlib import suppress
from dataclasses import dataclass, field
from operator import attrgetter
from os import PathLike
import re
from enum import IntEnum, Enum
from pathlib import Path
from typing import Callable, Collection, Dict, Iterable, List, Optional, Union, FrozenSet
from xplane_airports._cached_prop import apt_cached_property

WED_LINE_ENDING = '\n'


class RowCode(IntEnum):
    AIRPORT_HEADER		= 1
    _RUNWAY_OLD			= 10  # Legacy runway/taxiway record from X-Plane 8.10 and earlier
    TOWER_LOCATION		= 14
    STARTUP_LOCATION	= 15
    SEAPORT_HEADER		= 16
    HELIPORT_HEADER		= 17
    BEACON 				= 18
    WINDSOCK 			= 19
    FREQUENCY_AWOS 		= 50
    FREQUENCY_CTAF 		= 51
    FREQUENCY_DELIVERY 	= 52
    FREQUENCY_GROUND 	= 53
    FREQUENCY_TOWER 	= 54
    FREQUENCY_APPROACH 	= 55
    FREQUENCY_CENTER 	= 56
    FREQUENCY_UNICOM 	= 57
    FILE_END			= 99
    # These records were new with X-Plane 8.50
    TAXI_SIGN 			= 20
    PAPI_LIGHTS			= 21

    LAND_RUNWAY		= 100  # These replace the old type 10 record.
    WATER_RUNWAY	= 101
    HELIPAD 		= 102
    TAXIWAY 		= 110
    FREE_CHAIN		= 120
    BOUNDARY 		= 130

    LINE_SEGMENT	= 111
    LINE_CURVE		= 112
    RING_SEGMENT	= 113
    RING_CURVE 		= 114
    END_SEGMENT	 	= 115
    END_CURVE 		= 116

    # These records were new with X-Plane 10
    FLOW_DEFINITION	= 1000  # 1000 <traffic flow name, must be unique to the ICAO airport>
    FLOW_WIND		= 1001  # 1001 <metar icao> <wind dir min> <wind dir max> <wind max speed>
    FLOW_CEILING	= 1002  # 1002 <metar icao> <ceiling minimum>
    FLOW_VISIBILITY	= 1003  # 1003 <metar icao> <vis minimum>
    FLOW_TIME		= 1004  # 1004 <zulu time start> <zulu time end>

    CHANNEL_AWOS 		= 1050  # 8.33kHz 6-digit COM channels replacing the 50..57 records
    CHANNEL_CTAF 		= 1051
    CHANNEL_DELIVERY	= 1052
    CHANNEL_GROUND 		= 1053
    CHANNEL_TOWER 		= 1054
    CHANNEL_APPROACH	= 1055
    CHANNEL_CENTER 		= 1056
    CHANNEL_UNICOM 		= 1057

    FLOW_RUNWAY_RULE		= 1100
    FLOW_PATTERN			= 1101
    FLOW_RUNWAY_RULE_CHANNEL= 1110

    TAXI_ROUTE_HEADER	= 1200
    TAXI_ROUTE_NODE		= 1201
    TAXI_ROUTE_EDGE		= 1202
    TAXI_ROUTE_SHAPE	= 1203
    TAXI_ROUTE_HOLD		= 1204
    TAXI_ROUTE_ROAD		= 1206

    START_LOCATION_NEW	= 1300 # Replaces 15 record
    START_LOCATION_EXT	= 1301
    METADATA			= 1302

    TRUCK_PARKING		= 1400
    TRUCK_DESTINATION	= 1401

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

airport_header_codes = (RowCode.AIRPORT_HEADER, RowCode.SEAPORT_HEADER, RowCode.HELIPORT_HEADER)
runway_codes = (RowCode.LAND_RUNWAY, RowCode.WATER_RUNWAY, RowCode.HELIPAD)


class RunwayType(IntEnum):
    """Row codes used to identify different types of runways"""
    LAND_RUNWAY = RowCode.LAND_RUNWAY
    WATER_RUNWAY = RowCode.WATER_RUNWAY
    HELIPAD = RowCode.HELIPAD

    def __int__(self):
        return self.value


class MetadataKey(Enum):
    # NOTE: These have to match the key names in WED_MetaDataKeys.cpp
    CITY = 'city'
    COUNTRY = 'country'
    DATUM_LAT = 'datum_lat'
    DATUM_LON = 'datum_lon'
    FAA_CODE = 'faa_code'
    LABEL_3D_OR_2D = 'gui_label'
    IATA_CODE = 'iata_code'
    ICAO_CODE = 'icao_code'
    LOCAL_CODE = 'local_code'
    LOCAL_AUTHORITY = 'local_authority'
    REGION_CODE = 'region_code'
    STATE = 'state'
    TRANSITION_ALT = 'transition_alt'
    TRANSITION_LEVEL = 'transition_level'


class AptDatLine:
    """
    A single line from an apt.dat file.
    """
    __slots__ = ('raw', 'row_code')

    def __init__(self, line_text: str):
        self.raw = line_text.strip()
        self.row_code = self.raw.split(' ', 1)[0]
        with suppress(ValueError):
            self.row_code = int(self.row_code)

    def is_runway(self) -> bool:
        """:returns: True if this line represents a land runway, waterway, or helipad"""
        return self.row_code in runway_codes

    def is_ignorable(self) -> bool:
        """:returns: True if this line carries no semantic value for any airport in the apt.dat file."""
        return AptDatLine.raw_is_ignorable(self.raw)

    def is_airport_header(self) -> bool:
        """:returns: True if this line marks the beginning of an airport, seaport, or heliport"""
        return self.row_code in airport_header_codes

    def is_file_header(self) -> bool:
        """:returns: True if this is part of an apt.dat file header"""
        return AptDatLine.raw_is_file_header(self.raw)

    @property
    def runway_type(self) -> RowCode:
        """
        :returns: The type of runway represented by this line
        """
        assert self.is_runway()
        return RowCode(self.row_code)

    @property
    def tokens(self) -> List[Union[RowCode, str]]:
        """:returns: The tokens in this line"""
        return AptDatLine.tokenize(self.raw)

    def __str__(self):
        return re.sub(' +', ' ', self.raw)  # Replace multiple spaces with a single

    def __repr__(self):
        return self.raw

    def __bool__(self):
        return not self.is_ignorable()

    @staticmethod
    def raw_is_file_header(line: str) -> bool:
        """:returns: True if this is part of an apt.dat file header"""
        return line.strip() in ['I', 'A'] or "Generated by WorldEditor" in line

    @staticmethod
    def raw_is_ignorable(line: str) -> bool:
        """:returns: True if this is part of an apt.dat file header"""
        if AptDatLine.raw_is_file_header(line):
            return True
        stripped = line.strip()
        return not stripped or stripped == str(RowCode.FILE_END)

    @staticmethod
    def tokenize(line: str) -> List[Union[RowCode, str]]:
        ################################################################################
        # WARNING: This is at the core of the *hottest* of our hot paths.
        #          If you touch this at all, be sure to compare the before & after
        #          using benchmark.py.
        ################################################################################
        tokens = [t
                  for t in line.strip().split(' ')
                  if t]
        if tokens:
            tokens[0] = RowCode(int(tokens[0]))
        return tokens


@dataclass
class TaxiRouteNode:
    """
    A node in a taxiway routing network, used for routing aircraft via ATC.
    Every node must be part of one or more edges.
    Note that taxi routing networks (beginning with TAXI_ROUTE_HEADER line types)
    may or may not correspond to taxiway pavement.
    """
    id: int     # The node identifier (must be unique within an airport)
    lon: float  # Node's longitude
    lat: float  # Node's latitude


class IcaoWidth(Enum):
    A = 'A'  # 4.5m wheelbase, 15m wingspan
    B = 'B'  # 6m   wheelbase, 24m wingspan
    C = 'C'  # 9m   wheelbase, 36m wingspan
    D = 'D'  # 14m  wheelbase, 52m wingspan
    E = 'E'  # 14m  wheelbase, 65m wingspan
    F = 'F'  # 16m  wheelbase, 80m wingspan

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, string: str):
        for enum_def in cls:
            if string == enum_def.value:
                return enum_def
        raise LookupError(f'No instance of {cls} matches "{string}"')


@dataclass
class TaxiRouteEdge:
    """
    An edge in a taxiway routing network, used for routing aircraft via ATC.
    Every edge is defined by its two node endpoints.
    Edges may support one- or two-way traffic.
    """
    node_begin: int  # The identifier of the beginning node
    node_end: int    # The identifier of the terminal node
    name: str        # The taxiway identifier, used to build ATC taxi clearances (like "taxi via A, T, Q")---may be the empty string
    is_runway: bool = False  # If false, it's a taxiway
    one_way: bool = False  # If false, it supports two-way traffic
    icao_width: Optional[IcaoWidth] = None  # The width class of the taxiway; unknown if None

    @staticmethod
    def from_tokenized_line(tokens: List[Union[RowCode, str]]) -> 'TaxiRouteEdge':
        edge = TaxiRouteEdge(name=" ".join(tokens[5:]), node_begin=int(tokens[1]), node_end=int(tokens[2]), one_way=tokens[3] == 'oneway')

        taxiway_type = tokens[4]
        if taxiway_type.startswith('taxiway_'):  # has an explicit width class
            with suppress(LookupError):
                edge.icao_width = IcaoWidth.from_str(taxiway_type[-1:])
        elif taxiway_type == 'runway':
            edge.is_runway = True
        return edge


@dataclass
class TaxiRouteNetwork:
    nodes: Dict[int, TaxiRouteNode] = field(default_factory=dict)
    edges: List[TaxiRouteEdge] = field(default_factory=list)

    @staticmethod
    def from_lines(apt_dat_lines: Collection[AptDatLine]) -> 'TaxiRouteNetwork':
        return TaxiRouteNetwork.from_tokenized_lines([line.tokens for line in apt_dat_lines if not line.is_ignorable()])

    @staticmethod
    def from_tokenized_lines(tokenized_lines: Collection[List[Union[RowCode, str]]]) -> 'TaxiRouteNetwork':
        nodes = {
            node.id: node
            for node in map(lambda tokens: TaxiRouteNode(id=int(tokens[4]), lon=float(tokens[2]), lat=float(tokens[1])),
                            filter(lambda line: line[0] == RowCode.TAXI_ROUTE_NODE, tokenized_lines))
        }
        edges = [TaxiRouteEdge.from_tokenized_line(tokens)
                 for tokens in tokenized_lines
                 if tokens[0] == RowCode.TAXI_ROUTE_EDGE]
        return TaxiRouteNetwork(nodes=nodes, edges=edges)


@dataclass
class Airport:
    """A single airport from an apt.dat file."""
    from_file: Optional[Path] = None  # Path to the apt.dat file from which this airport was read
    raw_lines: List[str] = field(default_factory=list)  # The complete text of the portion of the apt.dat file pertaining to this airport, with leading & trailing whitespace removed
    xplane_version: int = 1100    # The version of X-Plane apt.dat spec (1050, 1100, 1130, etc.) used by the airport
    # An intermediate tokenization, used for speed of parsing.
    # The first element is the RowCode of the line, remaining elements (if any) are strings.
    tokenized_lines: List[List[Union[RowCode, str]]] = field(default_factory=list)

    def __bool__(self):
        return bool(self.tokenized_lines)

    def __str__(self):
        return WED_LINE_ENDING.join(self.raw_lines)

    def head(self, num_lines: int=10) -> str:
        """
        :param num_lines: The max number of lines to return
        :return: The first `num_lines` of the apt.dat text for this airport
        """
        return WED_LINE_ENDING.join(itertools.islice(self.raw_lines, 0, num_lines - 1))

    def write_to_disk(self, path_to_write_to: Optional[PathLike]):
        """
        Writes a complete apt.dat file containing only this airport
        :param path_to_write_to: A complete file path (ending in .dat); if None, we'll use the path this airport came from
        """
        if not path_to_write_to:
            path_to_write_to = self.from_file
        assert str(path_to_write_to).endswith('.dat')
        with open(str(path_to_write_to), 'w') as f:
            f.write("I" + WED_LINE_ENDING)
            f.write(f"{self.xplane_version} Generated by WorldEditor{WED_LINE_ENDING}{WED_LINE_ENDING}")
            f.write(str(self))
            f.write(str(RowCode.FILE_END) + WED_LINE_ENDING)

    @apt_cached_property
    def text(self) -> List[AptDatLine]:
        return [AptDatLine(line) for line in self.raw_lines]

    @property
    def name(self) -> str:
        """:returns: The name of the airport, like 'Seattle-Tacoma Intl'"""
        return ' '.join(self.tokenized_lines[0][5:])

    @property
    def id(self) -> str:
        """:returns: The airport's X-Plane ID which often (but by no means always) matches with its ICAO ID"""
        return self.tokenized_lines[0][4]

    @apt_cached_property
    def metadata(self) -> Dict[MetadataKey, str]:
        """:returns: Metadata about the airport defined by X-Plane"""
        out = {}
        for tokenized_line in self.tokenized_lines:
            if tokenized_line[0] == RowCode.METADATA:
                val = ' '.join(tokenized_line[2:]) if len(tokenized_line) > 2 else ''
                with suppress(ValueError):  # If we don't now about this MetadataKey type, ignore it
                    out[MetadataKey(tokenized_line[1])] = val
        return out

    @property
    def has_atc(self) -> bool:
        """:returns: True if the airport's header line indicates the airport has air traffic control"""
        return self.tokenized_lines[0][2] == '1'

    @property
    def elevation_ft_amsl(self) -> float:
        """:returns: The elevation, in feet above mean sea level, indicated by the airport's header line"""
        return float(self.tokenized_lines[0][1])

    @property
    def has_taxiway(self) -> bool:
        """:returns: True if this airport defines any taxiway geometry"""
        return self.has_row_code([RowCode.RING_SEGMENT, RowCode.RING_CURVE])

    @property
    def has_taxi_route(self) -> bool:
        """:returns: True if this airport defines routing rules for ATC's use of its taxiways."""
        return self.has_row_code(RowCode.TAXI_ROUTE_HEADER)

    @property
    def has_traffic_flow(self) -> bool:
        """:returns: True if this airport defines rules for when and under what conditions certain runways should be used by ATC"""
        return self.has_row_code(RowCode.FLOW_DEFINITION)

    @property
    def has_ground_routes(self) -> bool:
        """:returns: True if this airport defines any destinations for ground vehicles (like baggage cars, fuel trucks, etc.), ground truck parking locations, or taxi routes"""
        return self.has_row_code([RowCode.TRUCK_PARKING, RowCode.TRUCK_DESTINATION, RowCode.TAXI_ROUTE_HEADER])

    @property
    def has_taxiway_sign(self) -> bool:
        """:returns: True if this airport defines any taxi signs"""
        return self.has_row_code(RowCode.TAXI_SIGN)

    @property
    def has_comm_freq(self) -> bool:
        """
        :returns: True if this airport defines communication radio frequencies for interacting with ATC
        """
        return self.has_row_code([RowCode.FREQUENCY_AWOS, RowCode.FREQUENCY_CTAF, RowCode.FREQUENCY_DELIVERY, RowCode.FREQUENCY_GROUND, RowCode.FREQUENCY_TOWER, RowCode.FREQUENCY_APPROACH, RowCode.FREQUENCY_CENTER])

    def has_row_code(self, row_code_or_codes: Union[int, str, Iterable[int]]) -> bool:
        """
        :param row_code_or_codes: One or more "row codes" (the first token at the beginning of a line; almost always int)
        :returns: True if the airport has any lines in its text that begin with the specified row code(s)
        """
        if isinstance(row_code_or_codes, int):
            return row_code_or_codes in self.row_codes
        elif isinstance(row_code_or_codes, str):
            return RowCode(int(row_code_or_codes)) in self.row_codes
        return any(code in self.row_codes
                   for code in row_code_or_codes)

    @apt_cached_property
    def row_codes(self) -> FrozenSet[RowCode]:
        return frozenset(line_tokens[0] for line_tokens in self.tokenized_lines)

    @staticmethod
    def _rwy_center(rwy_tokens: List[Union[RowCode, str]], start: int, end: int) -> float:
        """
        :param rwy_tokens: The tokenized runway line
        :param start: index of the start coordinate in the tokens property of the runway
        :param end: index of the end coordinate in the tokens property of the runway
        :returns: Runway center
        """
        return 0.5 * (float(rwy_tokens[start]) + float(rwy_tokens[end]))

    @property
    def latitude(self) -> float:
        """
        :returns: The latitude of the airport, which X-Plane calculates as the latitude of the center of the first runway.
        """
        rwy_0 = self._first_runway_tokens()
        if rwy_0[0] == RunwayType.LAND_RUNWAY:
            return Airport._rwy_center(rwy_0, 9, 18)
        elif rwy_0[0] == RunwayType.WATER_RUNWAY:
            return Airport._rwy_center(rwy_0, 4, 7)
        elif rwy_0[0] == RunwayType.HELIPAD:
            return float(rwy_0[2])

    @property
    def longitude(self) -> float:
        """
        :returns: The longitude of the airport, which X-Plane calculates as the longitude of the center of the first runway.
        """
        rwy_0 = self._first_runway_tokens()
        if rwy_0[0] == RunwayType.LAND_RUNWAY:
            return Airport._rwy_center(rwy_0, 10, 19)
        elif rwy_0[0] == RunwayType.WATER_RUNWAY:
            return Airport._rwy_center(rwy_0, 5, 8)
        elif rwy_0[0] == RunwayType.HELIPAD:
            return float(rwy_0[3])

    def _first_runway_tokens(self) -> List[Union[RowCode, str]]:
        rwy_0_list = list(itertools.islice(self._runway_lines(), 1))
        assert rwy_0_list, f"Airport {self.id} appears to have no runway lines: {self.tokenized_lines}"
        return rwy_0_list[0]

    def _runway_lines(self) -> Iterable[List[Union[RowCode, str]]]:
        return (line_tokens
                for line_tokens in self.tokenized_lines
                if line_tokens[0] in runway_codes)

    @apt_cached_property
    def atc_network(self) -> TaxiRouteNetwork:
        return TaxiRouteNetwork.from_tokenized_lines(self.tokenized_lines)

    @staticmethod
    def from_lines(dat_lines: List[str], from_file_name: Optional[Path] = None, xplane_version: int = 1100) -> 'Airport':
        """
        :param dat_lines: The lines of the apt.dat file
        :param from_file_name: The name of the apt.dat file you read this airport in from
        :param xplane_version: The version of the apt.dat spec this airport uses (1050, 1100, 1130, etc.)
        """
        tokenized = [AptDatLine.tokenize(line) for line in dat_lines if line.lstrip()]
        return Airport(from_file_name, dat_lines, xplane_version, tokenized)

    @staticmethod
    def from_str(file_text: str, from_file_name: Optional[PathLike] = None, xplane_version: int = 1100) -> 'Airport':
        """
        :param file_text: The portion of the apt.dat file text that specifies this airport
        :param from_file_name: The name of the apt.dat file you read this airport in from
        """
        cleaned_lines = list(filter(lambda l: not AptDatLine.raw_is_ignorable(l), file_text.splitlines()))
        return Airport.from_lines(cleaned_lines, from_file_name, xplane_version)


class AptDat:
    """
    A container class for ``Airport`` objects.
    Parses X-Plane's gigantic apt.dat files, which may have data on hundreds of airports.
    """
    def __init__(self, path_to_file: Optional[PathLike] = None, xplane_version: int = 1100):
        """
        :param path_to_file Location of the apt.dat (or ICAO.dat) file to read from disk
        :param xplane_version The version of the apt.dat spec used by this file---overridden by any file we read (assuming it has a proper header).
        """
        self.airports = []
        """:type: list[Airport]"""
        self.xplane_version = xplane_version

        if path_to_file:
            self.path_to_file = Path(path_to_file).expanduser()
            with self.path_to_file.open(encoding="utf8") as f:
                self._parse_text(f.readlines(), path_to_file)
        else:
            self.path_to_file = None

    @staticmethod
    def from_file_text(dat_file_text: str, from_file: Optional[PathLike] = None) -> 'AptDat':
        """
        :param dat_file_text: The contents of an apt.dat (or ICAO.dat) file
        :param from_file: Path to the file from which this was read
        """
        # TODO: Provide an API to stream the file from disk so we don't have to store the whole thing in memory
        return AptDat()._parse_text(dat_file_text, from_file)

    def clone(self) -> 'AptDat':
        out = AptDat()
        out.airports = list(self.airports)
        out.path_to_file = self.path_to_file
        return out

    def _parse_text(self, dat_text: Union[List[str], str], from_file: Optional[PathLike] = None) -> 'AptDat':
        if not isinstance(dat_text, list):  # Must be a newline-containing string
            assert isinstance(dat_text, str)
            dat_text = dat_text.splitlines()

        has_file_header = dat_text[0].strip() in ('A', 'I') and 'Generated by WorldEditor' in dat_text[1]
        if has_file_header:
            self.xplane_version = AptDatLine(dat_text[1]).row_code
            assert self.xplane_version < 9999, f"Invalid X-Plane apt.dat spec version {self.xplane_version} specified in file header"
            dat_text = dat_text[2:]

        self.path_to_file = from_file
        tokenized_lines = []
        raw_lines = []
        for line in dat_text:
            ################################################################################
            # WARNING: This is the *hottest* of hot paths.
            #          If you touch any of this loop, be sure to compare the before & after
            #          using benchmark.py.
            ################################################################################
            tokenized = AptDatLine.tokenize(line)
            if tokenized:
                if tokenized[0] in airport_header_codes:
                    if tokenized_lines:  # finish off the previous airport
                        self.airports.append(Airport(from_file, raw_lines, self.xplane_version, tokenized_lines))
                    raw_lines = [line]
                    tokenized_lines = [tokenized]
                else:
                    tokenized_lines.append(tokenized)
                    raw_lines.append(line)
        if tokenized_lines:  # finish off the final airport
            if tokenized_lines[-1][0] == RowCode.FILE_END:
                tokenized_lines.pop()
                raw_lines.pop()
            self.airports.append(Airport(from_file, raw_lines, self.xplane_version, tokenized_lines))
        return self

    def write_to_disk(self, path_to_write_to: Optional[PathLike] = None):
        """
        Writes a complete apt.dat file containing this entire collection of airports.
        :param path_to_write_to: A complete file path (ending in .dat); if None, we'll use the path we read this apt.dat in from
        """
        if not path_to_write_to:
            path_to_write_to = self.path_to_file
        assert path_to_write_to and Path(path_to_write_to).suffix == '.dat', f"Invalid apt.dat path: {path_to_write_to}"
        with Path(path_to_write_to).expanduser().open('w', encoding="utf8") as f:
            f.write("I" + WED_LINE_ENDING)
            f.write(f"{self.xplane_version} Generated by WorldEditor{WED_LINE_ENDING}{WED_LINE_ENDING}")
            for apt in self.airports:
                f.write(str(apt))
                f.write(WED_LINE_ENDING * 2)
            f.write(str(RowCode.FILE_END) + WED_LINE_ENDING)

    def sort(self, key: str = 'name'):
        """
        By default, we store the airport data in whatever order we read it from the apt.dat file.
        When you call sort, though, we'll ensure that it's in order (default to name order, just like it's always
        been in the shipping versions of X-Plane).

        :param key: The ``Airport`` key to sort on
        """
        self.airports = sorted(self.airports, key=attrgetter(key))

    def search_by_id(self, id: str) -> Optional[Airport]:
        """
        :param id: The X-Plane ID of the airport you want to query
        :returns: The airport with the specified ID, or ``None`` if no matching airport exists in this collection.
        """
        found = self.search_by_predicate(lambda apt: apt.id.upper() == id.upper())
        if found:
            assert len(found) == 1, "No two airports in a given apt.dat file should ever have the same airport code"
            return found[0]
        return None

    def search_by_name(self, name: str) -> List[Airport]:
        """
        :param name: The name of the airport you want to query
        :returns: All airports that match the specified name, case-insensitive (an empty list if no airports match)
        """
        return self.search_by_predicate(lambda apt: apt.name.upper() == name.upper())

    def search_by_predicate(self, predicate_fn: Callable[[Airport], bool]) -> List[Airport]:
        """
        :param predicate_fn: We will collect all airports for which this function returns ``True``
        """
        return list(apt for apt in self.airports if predicate_fn(apt))

    @property
    def ids(self) -> Iterable[str]:
        """
        :returns: A generator containing the X-Plane IDs of all airports in the collection. Note that these IDs may or may not correspond to the airports' ICAO identifiers.
        """
        return (apt.id for apt in self.airports)

    @property
    def names(self) -> Iterable[str]:
        """
        :returns: A generator containing the names of all airports in the collection
        """
        return (apt.name for apt in self.airports)

    def __str__(self):
        """
        :returns: The raw text of the complete apt.dat file
        """
        return WED_LINE_ENDING.join(str(apt) for apt in self.airports)

    def __getitem__(self, key: Union[int, str]) -> Airport:
        """
        Returns the airport at the specified index (if ``key`` is an int), or with the specified identifier or name (if ``key`` is a string).
         Raises a KeyError if no airport could be found using those criteria.
        """
        if isinstance(key, int):
            assert key < len(self.airports), "Tried to access index %d, but this AptDat only has %d airports" % (key, len(self.airports))
            return self.airports[key]
        assert isinstance(key, str)
        for pred in [self.search_by_id, self.search_by_name]:
            result = pred(key)
            if result:
                return result
        raise KeyError("No airport with ID or name '%s'" % key)

    def __repr__(self):
        return str(list(self.ids))

    def __eq__(self, other: 'AptDat'):
        return self.airports == other.airports

    def __iter__(self):
        return (apt for apt in self.airports)

    def __contains__(self, item: Union[str, Airport]):
        if isinstance(item, str):
            return any(apt.id == item for apt in self.airports)
        return any(apt == item for apt in self.airports)

    def __delitem__(self, key: Union[str, int]):
        if isinstance(key, str):
            self.airports = [apt for apt in self.airports if apt.id != key]
        elif isinstance(key, int):
            del self.airports[key]
        else:
            self.airports.remove(key)

    def __reversed__(self):
        return reversed(self.airports)

    def __len__(self):
        return len(self.airports)

    def __concat__(self, other: 'AptDat') -> 'AptDat':
        """
        Get a new airport data object that combines the airport data in other with the data in this object.
        Note that no de-duplication will occur---it's your job to make sure the two airport data are disjoint.
        """
        out = AptDat()
        out.airports = list(self.airports) + list(other.airports)
        return out

    def __iconcat__(self, other: 'AptDat'):
        """
        Add the airport data in other to the data in this object.
        Note that no de-duplication will occur---it's your job to make sure the two airport data are disjoint.
        """
        self.airports += list(other.airports)

    def __add__(self, apt: Airport):
        """
        Add the airport data in other to the data in this object.
        Note that no de-duplication will occur---it's your job to make sure the two airport data are disjoint.
        """
        out = AptDat()
        out.airports = self.airports + [apt]
        return out

    def __iadd__(self, apt: Airport):
        """
        Add the airport data in other to the data in this object.
        Note that no de-duplication will occur---it's your job to make sure the two airport data are disjoint.
        """
        self.airports.append(apt)
        return self
