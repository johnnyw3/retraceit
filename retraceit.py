import re, datetime, os, io, gtfs
from PIL import Image, ImageDraw, ImageFont
from enum import Enum

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

class system_t(Enum):
    TRANSLINK = 0

class retraceit_db:
   def __init__(self):
        self.gtfs = {}

        print("INITALIZING GTFS DATABASE")
        tl_gtfs_dir = os.environ.get('RETRACEIT_TRANSLINK_GTFSDIR')
        if tl_gtfs_dir:
            print("reading TransLink data...")
            self.gtfs[system_t.TRANSLINK] = gtfs.read_gtfs_data(tl_gtfs_dir)

        print("LOADING ROUTE BULLETS")
        # bullets should be 54x54px
        self.bullets = {}
        img_dir = os.environ.get("RETRACEIT_IMGDIR")
        for bullet_fname in os.listdir(img_dir):
            bullet_name, ext = os.path.splitext(bullet_fname)
            if ext != '.png' and ext != '.jpg':
                continue
            self.bullets[bullet_name] = Image.open(os.path.join(img_dir, bullet_fname))

        print("LOADING FONTS")
        fnt_file = os.environ.get("RETRACEIT_FNTFILE")
        assert os.path.exists(fnt_file)
        self.fnt = ImageFont.truetype(fnt_file, 40)
        self.title_fnt = ImageFont.truetype(fnt_file, 60)

        logo_path = os.environ.get("RETRACEIT_HEADER_LOGO")
        if logo_path:
            print("LOADING HEADER LOGO")
            logo       = Image.open(logo_path)
            logo_sized = logo.resize((160, 160))
            self.logo = logo_sized

        print("DATABASE INIT COMPLETE")

def load_csv(fp) -> list:
    '''
    Mar-12-2024 03:04 AM
    '''
    results = []

    for line in gtfs.grab_csv_lines(fp):
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

def calc_top_counts(fp, system_gtfs):
   '''
   - gtfs is either a path to a gtfs directory, or a  5-tuple
   '''
   if type(system_gtfs) == str:
       with open(os.path.join(gtfs, 'stops.txt')) as stops_fp:
           _, stops = gtfs.read_gtfs_stops(stops_fp)
   else:
       stops = system_gtfs[4]

   system_gtfs = gtfs.read_gtfs_data(system_gtfs) if type(system_gtfs) == str else system_gtfs

   trips = load_csv(fp)
   counts = get_counts(trips)
   cleanup_data(counts)
   top_counts = get_top_counts(counts)

   return top_counts, counts

def top_counts_text(fp, gtfs_dir, width = 30):
   top_counts, = calc_top_counts(fp, gtfs_dir)
   print_top_counts(top_counts, stops, width)

def top_counts_img(fp, db: retraceit_db, width = 1000, num = 14):
   stops = db.gtfs[system_t.TRANSLINK].stop_id_to_code
   lines = gtfs.get_stop_lines_dict(db.gtfs[system_t.TRANSLINK])

   return gen_img(*calc_top_counts(fp, db.gtfs[system_t.TRANSLINK]), lines, stops, db, width = width, num = num)

def gen_img(top_counts, counts, lines, stops, db, width = 1000, num = 14,
            is_desc = True, title = 'Top Transit Stops', 
            category_title = 'Stops used') -> Image:
   '''
   '''
   height = 160+60*num if num < len(top_counts) else 160+60*len(top_counts)
   img = Image.new('RGBA', (width, height), color=(0, 52, 86))
   d = ImageDraw.Draw(img)

   header_text_xpos = 20
   if db.logo:
       img.alpha_composite(db.logo, dest=(0, 0))
       header_text_xpos += 160

   d.text( (header_text_xpos, 10), title, font=db.title_fnt, fill='white')

   total_taps = sum([counts[stop] for stop in counts])
   category_text = '; %s: %s' % (category_title, len(top_counts)) if category_title else ''
   d.text( (header_text_xpos, 90), "Taps: %s%s" % (total_taps, category_text),
                      font=db.fnt, fill='white')

   idx = 1
   top_cnt = top_counts[0][1] if is_desc else max([cnt for stop, cnt in top_counts])

   for stop, cnt in top_counts[:num]:
       stop_name = stops[stop] if stop in stops else stop
       ypos = 100+60*idx
       d.rectangle( (0, ypos, cnt/top_cnt*width, ypos+60 ), fill=(30, 82, 116))
       d.text( (width-100, ypos), "%3d" % (cnt), font=db.fnt, fill='white')

       if stop_name in STN_BULLETS:
           text_xpos = 20 + len(STN_BULLETS[stop_name])*60

           for bullet_idx, bullet in enumerate(STN_BULLETS[stop_name]):
               img.alpha_composite(db.bullets[bullet], dest=(10+60*bullet_idx, ypos))

       elif stop in lines:
           text_xpos = 20 + len(lines[stop])*76
           for rt_idx, rt_num in enumerate(lines[stop]):
               rt_box_xpos = 10+76*rt_idx
               rect_colour = LINE_COLOURS[rt_num] if rt_num in LINE_COLOURS else (99, 130, 161)

               d.rectangle( (rt_box_xpos, ypos, rt_box_xpos+72, ypos+54 ), fill=rect_colour)
               d.multiline_text((rt_box_xpos+37, ypos+25), str(rt_num), font=db.fnt,
                                fill='white', align='center', anchor='mm')
       else:
           text_xpos = 10

       stop_text_len = d.textlength(stop_name, font=db.fnt)
       while (text_xpos + stop_text_len > width-110 and len(stop_name) > 3):
           stop_name = stop_name[:-4] + '...'
           stop_text_len = d.textlength(stop_name, font=db.fnt)
           
       if stop_name != '...':
           d.text( (text_xpos, ypos), stop_name, font=db.fnt, fill='white')
       idx += 1

   return img

def top_month_counts(fp):
   trips = load_csv(fp)
   counts = get_month_counts(trips)
   top_counts = get_top_counts(counts)
   return top_counts, counts

def top_month_counts_text(fp, width = 10):
   top_counts, _ = top_month_counts(fp)
   print_top_counts(top_counts, width = width)

def top_month_counts_img(fp, db, width = 800):
   top_counts, counts = top_month_counts(fp)
   return gen_img(top_counts, counts, {}, {}, db, width = width, num=len(counts), 
                  is_desc=False, title = "Taps by Month", category_title='Months')

def top_hr_counts(fp, width = 30):
   trips = load_csv(fp)
   counts = get_hr_counts(trips)
   top_counts = sorted(list(counts.items()))
   print_top_counts(top_counts, width = width)

def top_hr_counts_img(fp, db, width = 800):
   trips = load_csv(fp)
   counts = get_hr_counts(trips)
   top_counts = [(str(hr), cnt) for hr, cnt in sorted(list(counts.items()))]
   return gen_img(top_counts, counts, {}, {}, db, width = width, num=24, is_desc=False,
                  title='Taps by Hour', category_title=None)
