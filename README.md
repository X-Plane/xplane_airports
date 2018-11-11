`xplane_airports`: Tools for working with X-Plane airport data[¶](#xplane-airports-tools-for-working-with-x-plane-airport-data "Permalink to this headline")
============================================================================================================================================================

`xplane_airports` is a Python package for interacting with [X-Plane](https://www.x-plane.com)'s airport data (`apt.dat`) files.

There are two primary components to this:

1. The `AptDat` module: used to parse & query raw `apt.dat` files (e.g., the files stored on disk in your X-Plane installation) 
2. The `gateway` module: used to interact with [the X-Plane Scenery Gateway](https://gateway.x-plane.com) to get information about what airports are available, and to download individual scenery packs contributed by the community.
 

## The `AptDat` module

Tools for reading, inspecting, and manipulating X-Plane’s airport (apt.dat) files.

### AptDat

_class_ `AptDat.AptDat`(_path\_to\_file=None_)

A container class for `Airport` objects. Parses X-Plane’s gigantic `apt.dat` files, which may have data on hundreds of airports.

Field `airports`\
Type: list\[Airport\]

_static_ `from_file_text`(_apt\_dat\_file\_text_, _from\_file_)\
Parameters:

- **apt\_dat\_file\_text** (_str_): The contents of an apt.dat (or ICAO.dat) file
- **from\_file** (_str_): Path to the file from which this was read

Property `ids`\
Returns: A generator containing the X-Plane IDs of all airports in the collection. Note that these IDs may or may not correspond to the airports’ ICAO identifiers.\
Return type: collection.Iterable\[str\]

Property `names`\
Returns: A generator containing the names of all airports in the collection\
Return type: collection.Iterable\[str\]

Method `search_by_id`(_apt\_id_)\
Parameter: **apt\_id** (_str_) – The X-Plane ID of the airport you want to query\
Returns: The airport with the specified ID, or `None` if no matching airport exists in this collection.\
Return type: Union\[[Airport](#AptDat.Airport), None\]

Method `search_by_name`(_apt\_name_)\
Parameter: **apt\_name** (_str_) – The name of the airport you want to query\
Returns: All airports that match the specified name, case-insensitive (an empty list if no airports match)
Return type: list\[[Airport](#AptDat.Airport)\]

Method `search_by_predicate`(_predicate\_fn_)\
Parameter: **predicate\_fn** (_(_[_Airport_](#AptDat.Airport)_)_ _\-> bool_) – We will collect all airports for which this function returns `True`\
Return type: list\[[Airport](#AptDat.Airport)\]

Method `sort`(_key='name'_)\
By default, we store the airport data in whatever order we read it from the apt.dat file. When you call sort, though, we’ll ensure that it’s in order (default to name order, just like it’s always been in the shipping versions of X-Plane).\
Parameter: **key** (_str_) – The [Airport](#AptDat.Airport) key to sort on
