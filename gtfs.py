import os, io
from collections import namedtuple

StopTime = namedtuple('StopTime', ['trip_id', 'arr_time', 'dep_time', 'stop_id', 'stop_seq', 'pickup_type', 'dropoff_type', 'dist'])
# to be enhanced
StopInfo = namedtuple('Stop', ['code', 'name'])
Trip = namedtuple('Trip', ['rt_id', 'service_id', 'block_id', 'shape_id', 'direction', 'wheelchair', 'bike'])
RouteInfo = namedtuple('Route', ['num', 'name', 'type', 'colour', 'txt_colour'])
GTFS = namedtuple('GTFS', ['routes', 'trips', 'stops', 'stoptimes', 'stop_id_to_code'])

def grab_csv_lines(fp) -> list[str]:
    '''
    parse lines from csv, skipping newlines in quotes
        - fp may be either a file pointer, or a string containing the text of a 
          csv file
    '''
    # TODO: is there a faster/better alogirhtm for this?
    contents = fp.read() if type(fp) == io.TextIOWrapper else fp
    flen = len(contents)
    idx = next_newline = 0
    inverb = False

    results = []

    while idx < flen:
        cur_idx = idx 

        while (inverb or next_newline <= idx) and (next_newline != flen or next_quote != flen):
            next_newline = contents.find("\n", cur_idx)
            if next_newline == -1: next_newline = flen
            next_quote = contents.find('"', cur_idx)
            if next_quote == -1: next_quote = flen
            inverb = not inverb if next_quote <= next_newline and next_quote < flen else inverb
            cur_idx = min(next_quote, next_newline) +1

        results.append(contents[idx:next_newline])

        idx = next_newline + 1

    return results

def read_gtfs_data(gtfs_dir):
    '''
    '''
    print("reading gtfs data: %s" % (gtfs_dir))
    with open(os.path.join(gtfs_dir, 'routes.txt')) as rts_fp:
        routes = get_routes_dict(rts_fp)

    with open(os.path.join(gtfs_dir, 'trips.txt')) as trips_fp:
        trips = get_trips_dict(trips_fp)

    with open(os.path.join(gtfs_dir, 'stops.txt')) as stops_fp:
        stops, stop_id_to_code = read_gtfs_stops(stops_fp)

    with open(os.path.join(gtfs_dir, 'stop_times.txt')) as stoptms_fp:
        stoptimes = get_stoptimes(stoptms_fp)

    print("finished reading gtfs data in %s" % (gtfs_dir))
    return GTFS(routes, trips, stops, stoptimes, stop_id_to_code)


def get_stop_lines_dict(gtfs_tup, include_dropoff_only=False):
    '''
    Build and return a dict mapping stops to the routes that stop at them.
        - set include_dropoff_only to include stops tagged as "dropoff only" in
          the gtfs. Useful for mapping possible tap locations in a system
          without exit taps
    '''
    trips  = gtfs_tup.trips
    routes = gtfs_tup.routes
    stops  = gtfs_tup.stops

    results = {}

    for stop_time in gtfs_tup.stoptimes:
        t_id, _, _, stop_id, _, _, _, _ = stop_time 
        stop_code = stops[stop_id].code
        trip = trips[t_id]
        rt_id = trip.rt_id
        rt = routes[rt_id].num

        if include_dropoff_only or not is_dropoff_only(stop_time):
            if stop_code not in results:
                results[stop_code] = set()
            results[stop_code].add(rt)
        
    results = {stop_code: sorted(results[stop_code]) for stop_code in results}
    return results

def get_routes_dict(fp) -> dict[str, RouteInfo]:
    '''
    Read the GTFS routes.txt file point to by fp, and return a dict d:
        d[rt_id]: RouteInfo tuple
    '''
    results = {}

    for line in grab_csv_lines(fp)[1:]:
        rt_id, _, rt_num, rt_name, _, rt_type, _, rt_color, rt_txt_colour = line.split(',')

        results[rt_id] = RouteInfo(rt_num, rt_name, rt_type, rt_color, rt_txt_colour)

    return results

def get_trips_dict(fp) -> dict[str, Trip]:
    '''
    Read the GTFS trips.text file pointed to by fp, and return a dict d:
        d[trip_id]: Trip tuple
    '''
    results = {}

    for line in grab_csv_lines(fp)[1:]:
        # headsign is not used by all agencies and should just use the headsign
        # on the stop times instead
        rt_id, s_id, t_id, t_headsign, _, direction, block_id, shape_id, wheelchair, bike = line.split(',')

        results[t_id] = Trip(rt_id, s_id, block_id, shape_id, direction, wheelchair, bike)

    return results


def read_gtfs_stops(fp) -> (dict[str, StopInfo], dict[str, str]):
    '''
    Read a GTFS stops.txt file, returning two dicts as follows:
        - stop_id: StopInfo
        - stop_code: stop_name
    '''
    stops, code_to_name = {}, {}

    # skip file header when receiving the list of lines
    for line in grab_csv_lines(fp)[1:]:
        contents = line.split(',')
        sid = contents[0]
        scode = contents[1]
        sname = contents[2]
        
        stops[sid] = StopInfo(scode, sname)
        code_to_name[scode] = sname

    return stops, code_to_name

def get_stoptimes(fp) -> list[StopTime]:
    '''
    Read a GTFS stop_times.txt file, returning a list of StopTime tuples
    '''
    results = []
    
    # skip file header
    fp.readline()

    for line in fp:
        line = line.strip()
        t_id, arr_time, dep_time, stop_id, stop_seq, _, pickup, dropoff, dist = line.split(',')
        
        results.append( StopTime(t_id, arr_time, dep_time, stop_id, stop_seq, pickup, dropoff, dist) )

    return results

    
def is_dropoff_only(stoptime_tuple):
    '''
    Returns True if the stop tim specified by the given stoptime_tuple is
    dropoff only, else False
    '''
    return stoptime_tuple.pickup_type == '1' and stoptime_tuple.dropoff_type != '1'
