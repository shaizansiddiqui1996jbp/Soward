import os
import discord
import logging
from discord.ext import commands
import motor.motor_asyncio as mongodb
from discord.colour import Color
from utilities.Tools import*

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

class utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Colour.green()
        self.connection = mongodb.AsyncIOMotorClient("mongodb+srv://rlx:rlx@rlx4.lxsal.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.connection["cluster0"]["servers"]
        self.tasks = []
        self.dump_tasks = []
        self.sniped = {}
        self.afk = {}
       

    @commands.Cog.listener()
    async def on_message_delete(self, message): 
        if message.guild == None: 
            return
        if message.author.bot: 
            return
        if not message.content: 
            return 
        self.sniped[message.channel.id] = message

    @commands.group(name="snipe", description="Snipes the most reecent deleted message", usage="snipe", aliases=["s"])
    @blacklist_check()
    async def snipe(self, ctx):
        message = self.sniped.get(ctx.channel.id)
        if message == None:
            return await ctx.send(embed=discord.Embed(title="snipe", description="There are no reecently deleted messages", color=0xFF1B1B))
        embed = discord.Embed(title="Message sent by %s" % (message.author), description=message.content, color=0xFF1B1B, timestamp=message.created_at)
        await ctx.send(embed=embed)


    @commands.group(invoke_without_command=True, name="dump", description="Shows dump commands", usage="dump")
    @blacklist_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dump(self, ctx):
        return await ctx.send(embed=discord.Embed(title="Dump", description="Please use `%shelp dump` instead!\n— This command group does not require a detailed help" % (ctx.prefix)))

    @dump.command()
    @blacklist_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def members(self, ctx):
        if ctx.guild.id in self.dump_tasks:
            return await ctx.send(embed=discord.Embed(title="Members | Dump", description="There is a dump task already running, please wait for it to finish", color=0xFF1B1B))
        with open(f"{ctx.guild.id}_members_dump.txt", "a+", encoding="utf-8") as f:
            for member in ctx.guild.members:
                f.write(f"{member} ({member.id})\n")
            f.close()
        await ctx.send(file=discord.File(f"{ctx.guild.id}_members_dump.txt"))
        os.remove(f"{ctx.guild.id}_members_dump.txt")

    @dump.command()
    @blacklist_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def channels(self, ctx):
        if ctx.guild.id in self.dump_tasks:
            return await ctx.send(embed=discord.Embed(title="Channels | Dump", description="There is a dump task already running, please wait for it to finish", color=0xFF1B1B))
        with open(f"{ctx.guild.id}_channels_dump.txt", "a+", encoding="utf-8") as f:
            for channel in ctx.guild.text_channels:
                f.write(f"[text_channel] {channel} ({channel.id})\n")
            for voice in ctx.guild.voice_channels:
                f.write(f"[voice_channel] {voice} ({voice.id})\n")
            f.close()
        await ctx.send(file=discord.File(f"{ctx.guild.id}_channels_dump.txt"))
        os.remove(f"{ctx.guild.id}_channels_dump.txt")

    @dump.command()
    @blacklist_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def roles(self, ctx):
        if ctx.guild.id in self.dump_tasks:
            return await ctx.send(embed=discord.Embed(title="Roles | Dump", description="There is a dump task already running, please wait for it to finish", color=0xFF1B1B))
        with open(f"{ctx.guild.id}_roles_dump.txt", "a+", encoding="utf-8") as f:
            for role in ctx.guild.roles:
                f.write(f"[role] {role} ({role.id})\n")
            f.close()
        await ctx.send(file=discord.File(f"{ctx.guild.id}_roles_dump.txt"))
        os.remove(f"{ctx.guild.id}_roles_dump.txt")

    @commands.group(name="jail", description="Jails a user", usage="jail <user>")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="jail")
        if not role:
            await ctx.guild.create_role(name="jail")

        jail = discord.utils.get(ctx.guild.text_channels, name="jail")
        if not jail:
            try:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
                }            
                jail = await ctx.guild.create_text_channel("jail", overwrites=overwrites)
                await ctx.send(embed=discord.Embed(title="jail", description="Your server has no jail channel, I created one for you %s" % (jail.mention), color=0xFF1B1B))
            except discord.Forbidden:
                return await ctx.send(embed=discord.Embed(title="jail", description="Please give me permissions, I am unable to create the jailed channel", color=0xFF1B1B))

        for channel in ctx.guild.channels:
            if channel.name == "jail":
                perms = channel.overwrites_for(member)
                perms.send_messages = True
                perms.read_messages = True
                await channel.set_permissions(member, overwrite=perms)
            else:
                perms = channel.overwrites_for(member)
                perms.send_messages = False
                perms.read_messages = False
                perms.view_channel = False
                await channel.set_permissions(member, overwrite=perms)

        role = discord.utils.get(ctx.guild.roles, name="jailed")
        await member.add_roles(role)

        await jail.send(content=member.mention, embed=discord.Embed(title="jail", description="Please live out your jail sentence until the court lets you free.", color=0xFF1B1B))
        await ctx.send(embed=discord.Embed(title="jail", description=" <:tick_right:1003345911067443241> | Successfully jailed **`%s`**" % (member.name), color=0xFF1B1B))
        await member.send(embed=discord.Embed(title="jail", description="You have been jailed in **`%s`** by **`%s`**" % (ctx.guild.name, ctx.author.name), color=0xFF1B1B))

    @commands.group(name="unjail", description="Unjails a user", usage="unjail <user>",  aliases=["free"])
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="jailed")
        for channel in ctx.guild.channels:
            if channel.name == "jail":
                perms = channel.overwrites_for(member)
                perms.send_messages = None
                perms.read_messages = None
                await channel.set_permissions(member, overwrite=perms)
            else:
                perms = channel.overwrites_for(member)
                perms.send_messages = None
                perms.read_messages = None
                perms.view_channel = None
                await channel.set_permissions(member, overwrite=perms)

        await member.remove_roles(role)
        await ctx.send(embed=discord.Embed(title="unjail", description=" <:tick_right:1003345911067443241> | Successfully unjailed **`%s`**" % (member.name), color=self.color))
        await member.send(embed=discord.Embed(title="unjail", description="you have been unjailed in **`%s`** by **`%s`**" % (ctx.guild.name, ctx.author.name), color=self.color))

    @commands.group(name="purgebot", description="deletes the bots messages", aliases=["pb"], usage="purgebot <amount>")
    @blacklist_check()
    @commands.has_permissions(administrator=True)
    async def purgebot(self, ctx, amount: int):
        msg = await ctx.send("cleaning...")
        async for message in ctx.message.channel.history(limit=amount).filter(lambda m: m.author == self.bot.user).map(lambda m: m):
            try:
                if message.id == msg.id:
                    pass
                else:
                    await message.delete()
            except:
                pass
        await msg.edit(content="cleaned up 👍")

def setup(bot):
    bot.add_cog(utility(bot))
