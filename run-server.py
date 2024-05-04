import discord, urllib, os, io
from enum import Enum
from datetime import datetime
from PIL import Image
import retraceit as rt

rt_db = rt.retraceit_db()
bot = discord.Bot()

async def upload_img(ctx, img: Image, fname: str, msg_text = 'Your generated image:'):
   fp = io.BytesIO()
   img.save(fp, format='png')

   # seek to beginning of saved image data
   fp.seek(0)
   await ctx.followup.send(msg_text, file=discord.File(fp, filename=fname))
   fp.close()

@bot.slash_command()
async def test(ctx):
    await ctx.respond("as of %s, we are online!" % (datetime.now()))

@bot.command()
async def gen_stop_stats(ctx, num: discord.Option(input_type=int, description="the number of stops to list", name="num"), system: rt.system_t, compass_history_csv: discord.Attachment, img_width: discord.Option(input_type=int, descrption="width of the generated image, in pixels", name="img_width") = 1050):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_counts_img(contents, rt_db, width=int(img_width), num=int(num))
   await upload_img(ctx, img, 'stop_stats.png')

@bot.command()
async def gen_time_stats(ctx, system: rt.system_t, compass_history_csv: discord.Attachment,
                         img_width: discord.Option(input_type=int, descrption="width of the generated image, in pixels", name="img_width") = 800):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_hr_counts_img(contents, rt_db, width=int(img_width))
   await upload_img(ctx, img, 'stop_stats.png')

@bot.command()
async def gen_month_stats(ctx, system: rt.system_t, compass_history_csv: discord.Attachment,
                          img_width: discord.Option(input_type=int, description="width of the generated image, in pixels", name="img_width") = 800):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_month_counts_img(contents, rt_db, width=int(img_width))
   await upload_img(ctx, img, 'stop_stats.png')

@bot.command()
async def gen_monthly_cost_stats(ctx, system: rt.system_t, compass_history_csv: discord.Attachment,
                                 img_width: discord.Option(input_type=int, description="width of the generated image, in pixels", name="img_width") = 800):
   await ctx.response.defer()
   contents = await compass_history_csv.read()
   contents = contents.decode('utf-8')

   img = rt.top_month_counts_img(contents, rt_db, width=int(img_width), spend=True)
   await upload_img(ctx, img, 'stop_stats.png',
                    "Note that costs of any passes purchased are not included in these totals.")

bot.run(os.environ.get("RETRACEIT_TOKEN"))
