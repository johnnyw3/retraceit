import discord, urllib, os, io
from enum import Enum
from datetime import datetime
import retraceit as rt

class system_t(Enum):
    TRANSLINK = 0

GTFS = {}

print("INITALIZING GTFS DATABASE")
tl_gtfs_dir = os.environ.get('RETRACEIT_TRANSLINK_GTFSDIR')
if tl_gtfs_dir:
    print("reading TransLink data...")
    tl_gtfs = rt.read_gtfs_data(tl_gtfs_dir)
    with open(os.path.join(tl_gtfs_dir, 'stops.txt')) as fp:
        _, tl_stops = rt.read_gtfs_stops(fp)
    GTFS[system_t.TRANSLINK] = (*tl_gtfs, tl_stops)
print("DATABASE INIT COMPLETE")

bot = discord.Bot()


@bot.slash_command()
async def test(ctx):
    await ctx.respond("as of %s, we are online!" % (datetime.now()))

@bot.command()
async def gen_stop_stats(ctx, num: discord.Option(input_type=int, description="the number of stops to list", name="num"), system: system_t, compass_history_csv: discord.Attachment, img_width: discord.Option(input_type=int, descrption="width of the generated image, in pixels", name="img_width") = 1050):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_counts_img(contents, GTFS[system], width=int(img_width), num=int(num))
   fp = io.BytesIO()
   img.save(fp, format='png')

   # seek to beginning of saved image data
   fp.seek(0)
   await ctx.followup.send("Your generated image:", file=discord.File(fp, filename='stop_stats.png'))
   fp.close()

bot.run(os.environ.get("RETRACEIT_TOKEN"))
