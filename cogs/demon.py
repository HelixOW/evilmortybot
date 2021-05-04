import discord
import asyncio
import utilities.embeds as embeds
import utilities.reactions as emojis
from discord.ext import commands
from discord.ext.commands import Context, has_permissions
from typing import Optional, Tuple, AsyncGenerator, Dict, Union, List, Any
from sqlite3 import Cursor
from utilities import connection


demon_offer_messages = {}


async def add_demon_role(role: discord.Role, demon: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('INSERT INTO demon_roles VALUES (?, ?, ?)', (role.id, role.guild.id, demon))
    connection.commit()


async def get_demon_role(guild: discord.Guild, demon: str) -> Optional[Tuple[int]]:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT role_id FROM demon_roles WHERE guild=? AND demon_type=?', (guild.id, demon)).fetchone()


async def get_raid_channels() -> AsyncGenerator[Dict[str, int], None]:
    cursor: Cursor = connection.cursor()
    row: Tuple[int, int]
    for row in cursor.execute('SELECT * FROM "raid_channels"'):
        yield {"guild": row[0], "channel_id": row[1]}


async def add_raid_channel(by: discord.Message) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('INSERT INTO "raid_channels" VALUES (?, ?)', (by.guild.id, by.channel.id))
    connection.commit()


async def get_friendcode(of: discord.Member) -> Optional[Tuple[int]]:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT gc_id FROM "users" WHERE discord_id=?', (of.id,)).fetchone()


async def get_profile_name_and_friendcode(of: discord.Member) -> AsyncGenerator[Dict[str, Union[str, int]], None]:
    cursor: Cursor = connection.cursor()
    for row in cursor.execute('SELECT name, gc_id FROM "users" WHERE discord_id=?', (of.id,)):
        yield {"name": row[0], "code": row[1]}


async def get_demon_profile(of: discord.Member, name: str) -> Optional[Tuple[int, int, str]]:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT * FROM "users" WHERE discord_id=? AND name=?', (of.id, name.lower())).fetchone()


async def create_demon_profile(of: discord.Member, gc_id: int, name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('INSERT OR IGNORE INTO "users" VALUES (?, ?, ?)', (of.id, gc_id, name.lower()))
    connection.commit()


async def delete_demon_profile(of: discord.Member, name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('DELETE FROM "users" WHERE name=? AND discord_id=?', (name.lower(), of.id))
    connection.commit()


async def update_demon_profile(of: discord.Member, gc_id: int, name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('UPDATE "users" SET gc_id=?, name=? WHERE discord_id=? AND name=?',
                   (gc_id, name.lower(), of.id, name.lower()))
    connection.commit()


async def try_getting_channel(x, bot):
    try:
        return (await bot.fetch_channel(x["channel_id"])).name + " in " + (await bot.fetch_guild(x["guild"])).name
    except discord.NotFound:
        cursor: Cursor = connection.cursor()
        cursor.execute('DELETE FROM "raid_channels" WHERE channel_id=? AND guild=?', (x["channel_id"], x["guild"]))
        connection.commit()
    except discord.Forbidden:
        return "Can't access channel"


class DemonCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    def mutual_guilds(self, person: discord.Member) -> List[discord.Guild]:
        return [g for g in self.bot.guilds if g.get_member(person.id) is not None]

    def shared_guilds(self, person1: discord.Member, person2: discord.Member) -> List[discord.Guild]:
        return [x for x in self.mutual_guilds(person1) if x in self.mutual_guilds(person2)]

    @commands.group()
    @commands.guild_only()
    async def demon(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await embeds.Help.send_demon_help(ctx, ctx.author.mention)

    @demon.command(name="friend", aliases=["friendcode", "code"])
    async def demon_friend(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of = ctx.author

        friendcode: Optional[Tuple[int]] = await get_friendcode(of)

        if friendcode is None:
            if of == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}: You are not registered in the bot yet! `..demon tag <grandcross friendcode> <profile name>` to create one")
            else:
                await ctx.send(f"{ctx.author.mention}: {of.display_name} is not registered in the bot yet!")
        else:
            await ctx.send(f"{ctx.author.mention}: {friendcode[0]}")

    @demon.command(name="offer")
    async def demon_offer(self, ctx: Context, reds: int = 0, greys: int = 0, crimsons: int = 0, *,
                          additional_message: str = ""):
        if reds == 0 and greys == 0 and crimsons == 0:
            return await ctx.send(
                content=f"{ctx.author.mention}",
                embed=embeds.ErrorEmbed(error_message="Please provide at least one demon")
            )
        author: discord.Member = ctx.author
        guild_created_in: discord.Guild = ctx.guild

        async for channel_list_item in get_raid_channels():
            try:
                channel: discord.TextChannel = await self.bot.fetch_channel(channel_list_item["channel_id"])
                guild: discord.Guild = await self.bot.fetch_guild(channel_list_item["guild"])
            except (discord.Forbidden, discord.errors.NotFound) as _:
                cursor: Cursor = connection.cursor()
                cursor.execute('DELETE FROM "raid_channels" WHERE channel_id=? AND guild=?',
                               (channel_list_item["channel_id"], channel_list_item["guild"]))
                connection.commit()
                continue
            except discord.Forbidden:
                continue

            mentions: List[str] = []

            red_role = await get_demon_role(guild, "red")
            grey_role = await get_demon_role(guild, "grey")
            crimson_role = await get_demon_role(guild, "red")
            all_role = await get_demon_role(guild, "all")

            if reds != 0 and red_role is not None:
                mentions.append(guild.get_role(red_role[0]).mention)
            if greys != 0 and grey_role is not None:
                mentions.append(guild.get_role(grey_role[0]).mention)
            if crimsons != 0 and crimson_role is not None:
                mentions.append(guild.get_role(crimson_role[0]).mention)

            if all_role is not None and None in [red_role, grey_role, crimson_role]:
                mentions.append(guild.get_role(all_role[0]).mention)

            to_claim: discord.Message = await channel.send(
                content=", ".join(mentions),
                embed=discord.Embed(
                    title=f"{author.display_name} offers:",
                    description="\n" +
                                (f"Reds: `{reds}` \n" if reds != 0 else "") +
                                (f"Greys: `{greys}` \n" if greys != 0 else "") +
                                (f"Crimsons: `{crimsons}` \n" if crimsons != 0 else "") +
                                (f"\n {additional_message} \n" if additional_message != "" else "") +
                                "\nClick 🆗 to claim them." +
                                "\nMake sure to have a empty spot in your friends list!",
                    color=discord.Color.green()
                ).set_thumbnail(url=author.avatar_url)
            )

            await to_claim.add_reaction(emojis.OK)

            demon_offer_messages[to_claim.id]: Dict[str, Any] = {
                "created_in": guild_created_in,
                "guild": guild,
                "channel": channel,
                "creator": author
            }

        if len(demon_offer_messages) == 0:
            return await ctx.send(f"{author.mention} no channel to broadcast in found")

        def check(added_reaction, user):
            return user != self.bot.user and str(added_reaction.emoji) in emojis.OK

        try:
            added_reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60 * 60 * 4)

            if user == author:
                await ctx.send(f"{author.mention} deleted your demon offer.")
            else:
                author_friendcode: Optional[Tuple[int]] = await get_friendcode(author)
                claim_friendcode: Optional[Tuple[int]] = await get_friendcode(user)

                if author_friendcode is None and claim_friendcode is None:
                    await ctx.send(f"{author.mention}: {user.mention} has claimed your demons!")
                elif author_friendcode is None and claim_friendcode is not None:
                    await ctx.send(
                        f"{author.mention}: {user.mention} (Friendcode: {claim_friendcode[0]}) has claimed your demons!")
                elif author_friendcode is not None and claim_friendcode is None:
                    await ctx.send(
                        f"{author.mention} (Friendcode: {author_friendcode[0]}): {user.mention} has claimed your demons!")
                else:
                    await ctx.send(
                        f"{author.mention} (Friendcode: {author_friendcode[0]}): {user.mention} (Friendcode: {claim_friendcode[0]}) has claimed your demons!")

                if len(self.shared_guilds(author, user)) != 0 and added_reaction.message.guild.id != \
                        demon_offer_messages[added_reaction.message.id]["created_in"].id:
                    await author.send(
                        content=f"Please contact {user.mention} (from {self.shared_guilds(author, user)[0]}) for your demons")

            for offer_id in [message_id for message_id in demon_offer_messages if
                             demon_offer_messages[message_id]["creator"].id == author.id]:
                try:
                    demon_offer_messages[offer_id]["claimed_by"] = user
                    offer_message: discord.Message = await demon_offer_messages[offer_id]["channel"].fetch_message(
                        offer_id)
                    new_embed: discord.Embed = discord.Embed(
                        title=f"~~{offer_message.embeds[0].title}~~ Claimed",
                        description=f"~~{offer_message.embeds[0].description}~~"
                    ).set_footer(text=f"Claimed by {user.display_name}")
                    await offer_message.edit(embed=new_embed)
                    await offer_message.clear_reactions()
                except discord.errors.NotFound:
                    pass

        except asyncio.TimeoutError:
            offer_messages: List[int] = [message_id for message_id in demon_offer_messages if
                                         demon_offer_messages[message_id]["creator"].id == author.id]
            for offer_id in offer_messages:
                try:
                    msg: discord.Message = await demon_offer_messages[offer_id]["channel"].fetch_message(offer_id)
                    new_embed: discord.Embed = discord.Embed(
                        title=f"~~{msg.embeds[0].title}~~ Timed out",
                        description=f"~~{msg.embeds[0].description}~~"
                    ).set_footer(text="Time ran out.")
                    await msg.edit(embed=new_embed)
                    await msg.clear_reactions()
                except discord.errors.NotFound:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):  # if people dont share a server. reply to the offer message
        if message.reference is None:
            return

        demon_msg_id: int = message.reference.message_id

        if demon_msg_id not in demon_offer_messages:
            return

        offer_data: Dict[str, Any] = demon_offer_messages[demon_msg_id]

        if "claimed_by" not in offer_data:
            return

        if len(self.shared_guilds(offer_data['creator'], offer_data['claimed_by'])) == 0:
            if message.author.id == offer_data['creator'].id:
                await offer_data['claimed_by'].send(
                    content=f"Message from {offer_data['creator'].mention} regarding your demon offer:",
                    embed=discord.Embed(description=message.content))
            else:
                await offer_data['creator'].send(
                    content=f"Message from {offer_data['claimed_by'].mention} regarding your demon offer:",
                    embed=discord.Embed(description=message.content))

    @demon.command(name="profile", aliases=["create", "tag"])
    async def demon_profile(self, ctx: Context, gc_id: int = 0, name: str = "main"):
        if gc_id == 0:
            return self.demon_info(ctx)

        if await get_demon_profile(ctx.author, name) is None:
            await create_demon_profile(ctx.author, gc_id, name)
            await ctx.send(f"{ctx.author.mention}: Added profile {name}  with friendcode {gc_id}")
        else:
            if gc_id == -1:
                await delete_demon_profile(ctx.author, name)
                await ctx.send(f"{ctx.author.mention}: Deleted profile {name}")
            else:
                await update_demon_profile(ctx.author, gc_id, name)
                await ctx.send(f"{ctx.author.mention}: Edited profile {name} to friendcode {gc_id}")

    @demon.command(name="info", aliases=["me"])
    async def demon_info(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of: discord.Member = ctx.message.author
        await ctx.send(
            content=f"{ctx.author.mention}",
            embed=discord.Embed(
                title=f"Info about {of.display_name}",
                description="Names: \n" + "\n".join([
                    "{}: {}".format(x["name"], x["code"])
                    async for x in get_profile_name_and_friendcode(of)
                ])
            ))

    @demon.command(name="channel")
    @has_permissions(manage_channels=True)
    async def demon_channel(self, ctx: Context, action: str = "none"):
        if action == "none":
            await add_raid_channel(ctx.message)
            return await ctx.send(f"{ctx.author.mention} added demon channel!")

        channels: List[discord.TextChannel] = [await try_getting_channel(x, self.bot) async for x in get_raid_channels()]
        await ctx.author.send("\n".join(channels))

    @demon.command(name="role")
    @has_permissions(manage_roles=True)
    async def demon_role(self, ctx: Context, role: discord.Role, demon_type: str):
        await add_demon_role(role, demon_type)
        await ctx.send(f"{ctx.author.mention}: Added Demon role!")


def setup(_bot):
    _bot.add_cog(DemonCog(_bot))
