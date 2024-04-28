import discord, urllib, os, io
from enum import Enum
from datetime import datetime
from PIL import Image
#from retraceit import retraceit_db, system_t
import retraceit as rt

rt_db = rt.retraceit_db()
bot = discord.Bot()

@bot.slash_command()
async def test(ctx):
    await ctx.respond("as of %s, we are online!" % (datetime.now()))

@bot.command()
async def gen_stop_stats(ctx, num: discord.Option(input_type=int, description="the number of stops to list", name="num"), system: rt.system_t, compass_history_csv: discord.Attachment, img_width: discord.Option(input_type=int, descrption="width of the generated image, in pixels", name="img_width") = 1050):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_counts_img(contents, rt_db, width=int(img_width), num=int(num))
   fp = io.BytesIO()
   img.save(fp, format='png')

   # seek to beginning of saved image data
   fp.seek(0)
   await ctx.followup.send("Your generated image:", file=discord.File(fp, filename='stop_stats.png'))
   fp.close()

bot.run(os.environ.get("RETRACEIT_TOKEN"))
