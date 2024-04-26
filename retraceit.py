import re, datetime, os, io
from PIL import Image, ImageDraw, ImageFont

MON_TO_NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 
              'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
             }

STN_BULLETS= {'Lougheed Stn': ['expo', 'mil'], 
              'Production Way Stn': ['expo', 'mil'],
              'Braid Stn': ['expo'],
              'Sapperton Stn': ['expo'],
              'Columbia Stn': ['expo'],
              'New Westminster Stn': ['expo'],
              '22nd St Stn': ['expo'],
              'Edmonds Stn': ['expo'],
              'Royal Oak Stn': ['expo'],
              'Metrotown Stn': ['expo'],
              'Patterson Stn': ['expo'],
              'Joyce Stn': ['expo'],
              '29th Av Stn': ['expo'],
              'Nanaimo Stn': ['expo'],
              'Commercial-Broadway Stn': ['expo', 'mil'],
              'Main Street-Science World Stn': ['expo'],
              'Stadium Stn': ['expo'],
              'Granville Stn': ['expo'],
              'Burrard Stn': ['expo'],
              'Waterfront Stn': ['expo', 'canada', 'wce', 'seabus'],
              'King George Stn': ['expo'],
              'Surrey Central Stn': ['expo'],
              'Gateway Stn': ['expo'],
              'Scott Road Stn': ['expo'],
              'Lafarge Lake/Douglas College Stn': ['mil'],
              'Lincoln Stn': ['mil'],
              'Coquitlam Central Stn': ['mil', 'wce'],
              'Inlet Centre Stn': ['mil'],
              'Moody Centre Stn': ['mil', 'wce'],
              'Burquitlam Stn': ['mil'],
              'Lake City Way Stn': ['mil'],
              'Sperling Stn': ['mil'],
              'Holdom Stn': ['mil'],
              'Brentwood Stn': ['mil'],
              'Gilmore Stn': ['mil'],
              'Rupert Stn': ['mil'],
              'Renfrew Stn': ['mil'],
              'VCC-Clark Stn': ['mil'],
              'Brighouse Stn': ['canada'],
              'Aberdeen Stn': ['canada'],
              'Lansdowne Stn': ['canada'],
              'Capstan Stn': ['canada'],
              'Bridgeport Stn': ['canada'],
              'Marine Drive Stn': ['canada'],
              'Langara-49th Stn': ['canada'],
              'Oakridge-41st Stn': ['canada'],
              'King Edward Stn': ['canada'],
              'Broadway-City Hall Stn': ['canada'],
              'Olympic Village Stn': ['canada'],
              'Yaletown-Roundhouse Stn': ['canada'],
              'Vancouver City Centre Stn': ['canada'],
              'YVR-Airport Stn': ['canada'],
              'Sea Island Ctr Stn': ['canada'],
              'Templeton Stn': ['canada'],
              'Lonsdale Quay': ['seabus'],
              'Port Coquitlam Stn': ['wce'],
              'Pitt Meadows Stn': ['wce'],
              'Maple Meadows Stn': ['wce'],
              'Port Haney Stn': ['wce'],
              'Mission City Stn': ['wce']
             }

NIGHTBUS_COLOUR = (0, 12, 66)
RB_COLOUR       = (0, 133, 34)

LINE_COLOURS={'99': (208, 65, 16),
              '099': (208, 65, 16),
              'R1': RB_COLOUR,
              'R2': RB_COLOUR,
              'R3': RB_COLOUR,
              'R4': RB_COLOUR,
              'R5': RB_COLOUR,
              'R6': RB_COLOUR,
              'N8': NIGHTBUS_COLOUR,
              'N9': NIGHTBUS_COLOUR,
              'N10': NIGHTBUS_COLOUR,
              'N15': NIGHTBUS_COLOUR,
              'N17': NIGHTBUS_COLOUR,
              'N19': NIGHTBUS_COLOUR,
              'N20': NIGHTBUS_COLOUR,
              'N22': NIGHTBUS_COLOUR,
              'N24': NIGHTBUS_COLOUR,
              'N35': NIGHTBUS_COLOUR,
             }

def grab_csv_lines(fp) -> list[str]:
    '''
    parse lines from csv, skipping newlines in quotes
        - fp may be either a file pointer, or a string containing the text of a 
          csv file
    '''
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
    
def get_stop_lines_dict(routes, trips, stops, stoptimes, include_dropoff_only=False):
    '''
    Build and return a dict mapping stops to the routes that stop at them.
        - set include_dropoff_only to include stops tagged as "dropoff only" in
          the gtfs. Useful for mapping possible tap locations in a system
          without exit taps
    '''
    results = {}

    for stop_time in stoptimes:
        t_id, _, _, stop_id, _, _, _, _ = stop_time 
        stop_code = stops[stop_id][0]
        trip = trips[t_id]
        rt_id = trip[0]
        rt = routes[rt_id][0]

        if include_dropoff_only or not is_dropoff_only(stop_time):
            if stop_code not in results:
                results[stop_code] = set()
            results[stop_code].add(rt)
        
    results = {stop_code: sorted(results[stop_code]) for stop_code in results}
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
        stops, _ = read_gtfs_stops(stops_fp)

    with open(os.path.join(gtfs_dir, 'stop_times.txt')) as stoptms_fp:
        stoptimes = get_stoptimes(stoptms_fp)

    print("finished reading gtfs data in %s" % (gtfs_dir))
    return routes, trips, stops, stoptimes


def get_routes_dict(fp):
    '''
    '''
    results = {}

    for line in grab_csv_lines(fp)[1:]:
        rt_id, _, rt_num, rt_name, _, rt_type, _, rt_color, rt_txt_colour = line.split(',')

        results[rt_id] = (rt_num, rt_name, rt_type, rt_color, rt_txt_colour)

    return results


def get_trips_dict(fp):
    '''
    '''
    results = {}

    for line in grab_csv_lines(fp)[1:]:
        rt_id, s_id, t_id, t_headsign, _, direction, block_id, shape_id, wheelchair, bike = line.split(',')

        results[t_id] = (rt_id, s_id, block_id, shape_id, direction, shape_id, wheelchair, bike)

    return results

def get_stoptimes(fp):
    '''
    Read a GTFS stop_times.txt file, returning a 
    '''
    results = []
    
    # skip file header
    fp.readline()

    for line in fp:
        line = line.strip()
        t_id, arr_time, dep_time, stop_id, stop_seq, _, pickup, dropoff, dist = line.split(',')
        
        results.append( (t_id, arr_time, dep_time, stop_id, stop_seq, pickup, dropoff, dist) )

    return results

def is_dropoff_only(stoptime_tuple):
    '''
    Returns True if the stop tim specified by the given stoptime_tuple is
    dropoff only, else False
    '''
    return stoptime_tuple[5] == '1' and stoptime_tuple[6] != '1'

def read_gtfs_stops(fp) -> (dict[str, tuple[str, str]], dict[str, str]):
    '''
    Read a GTFS stops.txt file, returning two dicts as follows:
        - stop_id: (stop_code, stop_name)
        - stop_code: stop_name
    '''
    stops, code_to_name = {}, {}

    # skip file header when receiving the list of lines
    for line in grab_csv_lines(fp)[1:]:
        contents = line.split(',')
        sid = contents[0]
        scode = contents[1]
        sname = contents[2]
        
        stops[sid] = (scode, sname)
        code_to_name[scode] = sname

    return stops, code_to_name

def load_csv(fp) -> list:
    '''
    Mar-12-2024 03:04 AM
    '''
    results = []

    for line in grab_csv_lines(fp):
        time, trans, prod, li, am, bal, jID, locDisp, _, _, _, ordNum, authCode, tot = line.split(',')

        time_grps = re.match("(\w{3})-(\d\d)-(\d{4})\s(\d\d):(\d\d) ([AP])M", time)
        if not time_grps:
            continue

        month, day, year, hr_12, mins, ampm = time_grps.groups()
        hr_24 = int(hr_12) + 12 if (ampm == 'P') else int(hr_12)
        if hr_12 == '12': hr_24 -= 12
        day = int(day)
        mins = int(mins)
        year = int(year)
        mon_num = MON_TO_NUM[month]
        processed_time = datetime.datetime(year, mon_num, day, hr_24, mins)

        stn_search = re.search(r".*\sat\s+(?:(.*Stn)|Bus Stop\s(\d+)|(.*Station)|(Lonsdale Quay))\s*", trans)
        stn = "".join([group for group in stn_search.groups() if group]) if stn_search else None
        if not stn: continue

        results.append( (processed_time, stn, prod) )
    return results

def get_hr_counts(trips):
    '''
    '''
    results = {hr: 0 for hr in range(0, 24)}

    for trip in trips:
        time = trip[0]

        results[time.hour] += 1

    return results


def get_counts(trips):
    '''
    '''
    results = {}

    for trip in trips:
        loc = trip[1]

        if loc in results: results[loc] += 1
        else: results[loc] = 1
    return results

def get_month_counts(trips):
    '''
    '''
    results = {}

    for trip in trips:
        date = trip[0]
        yr, mn = date.year, date.month
        month_str = "%s-%s" % (yr, mn)

        if month_str in results: results[month_str] += 1
        else: results[month_str] = 1
    return results

def get_top_counts(counts):
    return sorted(list(counts.items()), key=lambda x: -x[1])

def print_top_counts(top_counts, stop_names = {}, width = 30):
    print("Stn/stop".ljust(width) + "| Count ")
    print("-"* width + "+-------")
    
    for place, count in top_counts:
        place = stop_names[place] if place in stop_names else place
        print(shorten(place, width).rjust(width) + '|' + str(count).rjust(7))

def shorten(string, length = 30):
    if type(string) != str:
        string = str(string)

    if len(string) <= length:
        return string

    return string[:length]

def cleanup_data(counts):
    to_rename = {'Moody Center Stn': 'Moody Centre Stn'}
    to_merge  = {'Commercial Drive Stn': 'Commercial-Broadway Stn',
                 'Port Coquitlam Station': 'Port Coquitlam Stn',
                 'Port Moody Stn': 'Moody Centre Stn',
                 'Main Street Stn': 'Main Street-Science World Stn',
                 'Main Street-Science World Station': 'Main Street-Science World Stn'}

    for name in to_rename:
        if name in counts:
            counts[to_rename[name]] = counts[name]
            del counts[name]
    for name in to_merge:
        if name in counts:
            counts[to_merge[name]] = counts.get(to_merge[name], 0) + counts[name]
            del counts[name]

def calc_top_counts(fp, gtfs):
   '''
   - gtfs is either a path to a gtfs directory, or a  5-tuple
   '''
   if type(gtfs) == str:
       with open(os.path.join(gtfs, 'stops.txt')) as stops_fp:
           _, stops = read_gtfs_stops(stops_fp)
   else:
       stops = gtfs[4]
   gtfs = read_gtfs_data(gtfs) if type(gtfs) == str else gtfs[:4]
   lines = get_stop_lines_dict(*gtfs)

   trips = load_csv(fp)
   counts = get_counts(trips)
   cleanup_data(counts)
   top_counts = get_top_counts(counts)

   return top_counts, lines, counts, stops

def top_counts_text(fp, gtfs_dir, width = 30):
   top_counts, lines, _, stops = calc_top_counts(fp, gtfs_dir)
   print_top_counts(top_counts, stops, width)

def top_counts_img(fp, gtfs_dir, width = 1000, num = 14, out_fname = 'out.png'):
   return gen_img(*calc_top_counts(fp, gtfs_dir), width = width, num = num, out_fname=out_fname)

def gen_img(top_counts, lines, counts, stops, width = 1000, num = 14, 
            is_desc = True, title = 'Top Transit Stops', 
            category_title = 'Stops used', out_fname = 'out.png'):

   # bullets should be 54x54px
   img_dir= os.environ.get("RETRACEIT_IMGDIR")
   expo   = Image.open(os.path.join(img_dir, "expo.png"))
   canada = Image.open(os.path.join(img_dir, "canada.png"))
   mil    = Image.open(os.path.join(img_dir, "mil.png"))
   wce    = Image.open(os.path.join(img_dir, "wce.png"))
   seabus = Image.open(os.path.join(img_dir, "seabus.png"))
   bullets = {'expo': expo, 'canada': canada, 'mil': mil, "wce": wce, "seabus": seabus}

   height = 160+60*num if num < len(top_counts) else 160+60*len(top_counts)
   img = Image.new('RGBA', (width, height), color=(0, 52, 86))
   d = ImageDraw.Draw(img)

   fnt_file = os.environ.get("RETRACEIT_FNTFILE")
   fnt = ImageFont.truetype(fnt_file, 40)
   title_fnt = ImageFont.truetype(fnt_file, 60)

   logo_path = os.environ.get("RETRACEIT_HEADER_LOGO")
   header_text_xpos = 20
   if logo_path: 
       logo       = Image.open(INSERT_LOGO_HERE)
       logo_sized = logo.resize((160, 160))
       img.alpha_composite(logo_sized, dest=(0, 0))
       header_text_xpos += 160

   d.text( (header_text_xpos, 10), title, font=title_fnt, fill='white')

   total_taps = sum([counts[stop] for stop in counts])
   category_text = '; %s: %s' % (category_title, len(top_counts)) if category_title else ''
   d.text( (header_text_xpos, 90), "Taps: %s%s" % (total_taps, category_text),
                      font=fnt, fill='white')

   idx = 1
   top_cnt = top_counts[0][1] if is_desc else max([cnt for stop, cnt in top_counts])

   for stop, cnt in top_counts[:num]:
       stop_name = stops[stop] if stop in stops else stop
       ypos = 100+60*idx
       d.rectangle( (0, ypos, cnt/top_cnt*width, ypos+60 ), fill=(30, 82, 116))
       d.text( (width-100, ypos), "%3d" % (cnt), font=fnt, fill='white')

       if stop_name in STN_BULLETS:
           text_xpos = 20 + len(STN_BULLETS[stop_name])*60

           for bullet_idx, bullet in enumerate(STN_BULLETS[stop_name]):
               img.alpha_composite(bullets[bullet], dest=(10+60*bullet_idx, ypos))

       elif stop in lines:
           text_xpos = 20 + len(lines[stop])*76
           for rt_idx, rt_num in enumerate(lines[stop]):
               rt_box_xpos = 10+76*rt_idx
               rect_colour = LINE_COLOURS[rt_num] if rt_num in LINE_COLOURS else (99, 130, 161)

               d.rectangle( (rt_box_xpos, ypos, rt_box_xpos+72, ypos+54 ), fill=rect_colour)
               d.multiline_text((rt_box_xpos+37, ypos+25), str(rt_num), font=fnt,
                                fill='white', align='center', anchor='mm')
       else:
           text_xpos = 10

       stop_text_len = d.textlength(stop_name, font=fnt)
       while (text_xpos + stop_text_len > width-110 and len(stop_name) > 3):
           stop_name = stop_name[:-4] + '...'
           stop_text_len = d.textlength(stop_name, font=fnt)
           
       if stop_name != '...':
           d.text( (text_xpos, ypos), stop_name, font=fnt, fill='white')
       idx += 1

   img.save(out_fname)
   return out_fname

def top_month_counts(fp):
   trips = load_csv(fp)
   counts = get_month_counts(trips)
   top_counts = get_top_counts(counts)
   return top_counts, counts

def top_month_counts_text(fp, width = 10):
   top_counts, _ = top_month_counts(fp)
   print_top_counts(top_counts, width = width)

def top_month_counts_img(fp, width = 800, out_fname = 'out.png'):
   top_counts, counts = top_month_counts(fp)
   gen_img(top_counts, {}, counts, {}, width = width, num=len(counts), 
           is_desc=False, title = "Taps by Month", category_title='Months',
           out_fname=out_fname)

def top_hr_counts(fp, width = 30):
   trips = load_csv(fp)
   counts = get_hr_counts(trips)
   top_counts = sorted(list(counts.items()))
   print_top_counts(top_counts, width = width)

def top_hr_counts_img(fp, width = 800, out_fname = 'out.png'):
   trips = load_csv(fp)
   counts = get_hr_counts(trips)
   top_counts = [(str(hr), cnt) for hr, cnt in sorted(list(counts.items()))]
   gen_img(top_counts, {}, counts, {}, width = width, num=24, is_desc=False,
           title='Taps by Hour', category_title=None, out_fname=out_fname)
