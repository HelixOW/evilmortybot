import discord
import asyncio
import utilities.reactions as emojis
from discord.ext import commands
from discord.ext.commands import Context, has_permissions
from typing import Optional, Tuple, AsyncGenerator, Dict, Union, List, Any
from utilities import embeds, ask
from utilities.sql_helper import execute, fetch_item, rows, fetch_rows, exists

demon_offer_messages = {}


async def add_demon_role(role: discord.Role, demon: str) -> None:
    await execute('INSERT INTO "demon_roles" VALUES (?, ?, ?)', (role.id, role.guild.id, demon))


async def get_demon_role(guild: discord.Guild, demon: str) -> Optional[int]:
    return await fetch_item('SELECT role_id FROM "demon_roles" WHERE guild=? AND demon_type=?', (guild.id, demon))


async def get_raid_channels() -> AsyncGenerator[Dict[str, int], None]:
    async for row in rows('SELECT * FROM "raid_channels"'):
        yield {"guild": row[0], "channel_id": row[1]}


async def add_raid_channel(by: discord.Message) -> None:
    await execute('INSERT INTO "raid_channels" VALUES (?, ?)', (by.guild.id, by.channel.id))


async def get_friendcode(of: discord.Member) -> Optional[int]:
    return await fetch_item('SELECT gc_id FROM "users" WHERE discord_id=?', (of.id,))


async def get_friendcode_with_id(discord_id: int) -> Optional[int]:
    return await fetch_item('SELECT gc_id FROM "users" WHERE discord_id=?', (discord_id,))


async def get_profile_name_and_friendcode(of: discord.Member) -> AsyncGenerator[Dict[str, Union[str, int]], None]:
    async for row in rows('SELECT name, gc_id FROM "users" WHERE discord_id=?', (of.id,)):
        yield {"name": row[0], "code": row[1]}


async def get_demon_profile(of: discord.Member, name: str) -> Optional[Tuple[int, int, str]]:
    return await fetch_item('SELECT * FROM "users" WHERE discord_id=? AND name=?', (of.id, name.lower()))


async def create_demon_profile(of: discord.Member, gc_id: int, name: str) -> None:
    await execute('INSERT OR IGNORE INTO "users" VALUES (?, ?, ?)', (of.id, gc_id, name.lower()))


async def delete_demon_profile(of: discord.Member, name: str) -> None:
    await execute('DELETE FROM "users" WHERE name=? AND discord_id=?', (name.lower(), of.id))


async def update_demon_profile(of: discord.Member, gc_id: int, name: str) -> None:
    await execute('UPDATE "users" SET gc_id=?, name=? WHERE discord_id=? AND name=?',
                  (gc_id, name.lower(), of.id, name.lower()))


def demon_converter(demon: str) -> List[str]:
    notified: List[str] = []
    for d in demon.lower().split(","):
        d = d.strip()
        if d in ["red", "reds"]:
            notified.append("reds")
        elif d in ["grays", "gray", "greys", "grey"]:
            notified.append("grays")
        elif d in ["crimsons", "crimson", "howlex"]:
            notified.append("crimsons")
        elif d in ["belmos", "bellmoth", "bellmoths"]:
            notified.append("bellmoths")
    return notified


async def get_demon_queue(demon: str) -> List[Dict[str, int]]:
    demon = demon.lower()
    if demon in ["red", "reds"]:
        demon = "reds"
    elif demon in ["grays", "gray", "greys", "grey"]:
        demon = "grays"
    elif demon in ["crimsons", "crimson", "howlex"]:
        demon = "crimsons"
    elif demon in ["belmos", "bellmoth", "bellmoths"]:
        demon = "bellmoths"
    elif demon in ["all"]:
        return await fetch_rows('SELECT * FROM "demon_offers" WHERE reds>=1 OR grays>=1 OR crimsons>=1 OR bellmoths>=1',
                                lambda x: {
                                    "offer_id": x[0],
                                    "reds": x[1] == 1,
                                    "grays": x[2] == 1,
                                    "crimsons": x[3] == 1,
                                    "bellmoths": x[4] == 1
                                })
    else:
        return []
    return await fetch_rows('SELECT * FROM "demon_offers" WHERE ' + demon + '=1',
                            lambda x: {
                                "offer_id": x[0],
                                "reds": x[1] == 1,
                                "grays": x[2] == 1,
                                "crimsons": x[3] == 1,
                                "bellmoths": x[4] == 1
                            })


async def add_demon_queue(of: discord.Member, reds: bool, grays: bool, crimsons: bool, bellmoths: bool) -> None:
    await execute('INSERT OR IGNORE INTO "demon_offers" VALUES (?, ?, ?, ?, ?)',
                  (of.id, int(reds), int(grays), int(crimsons), int(bellmoths)))


async def update_demon_queue(of: discord.Member, reds: bool, grays: bool, crimsons: bool, bellmoths: bool) -> None:
    await execute('UPDATE "demon_offers" SET reds=?, grays=?, crimsons=?, bellmoths=? WHERE discord_id=?',
                  (int(reds), int(grays), int(crimsons), int(bellmoths), of.id))


async def in_demon_queue(of: discord.Member) -> bool:
    return await exists('SELECT * FROM "demon_offers" WHERE discord_id=?', (of.id,))


def demon_bools_to_str(x) -> str:
    li = []
    if x['reds']:
        li.append("Reds")
    if x['grays']:
        li.append("Grays")
    if x['crimsons']:
        li.append("Crimsons")
    if x['bellmoths']:
        li.append("Bellmoths")
    return ', '.join(li)


async def try_getting_channel(x, bot):
    try:
        return (await bot.fetch_channel(x["channel_id"])).name + " in " + (await bot.fetch_guild(x["guild"])).name
    except discord.NotFound:
        await execute('DELETE FROM "raid_channels" WHERE channel_id=? AND guild=?', (x["channel_id"], x["guild"]))
    except discord.Forbidden:
        return "Can't access channel"


def lookup_demon_info(member: discord.Member):
    for x in demon_offer_messages:
        if not demon_offer_messages[x]:
            continue
        if "claimed_by" not in demon_offer_messages[x]:
            return
        if demon_offer_messages[x]["creator"].id == member.id:
            return demon_offer_messages[x]["claimed_by"]
        if demon_offer_messages[x]["claimed_by"].id == member.id:
            return demon_offer_messages[x]["creator"]
    return None


class DemonCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group()
    @commands.guild_only()
    async def demon(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await embeds.Help.send_demon_help(ctx, ctx.author.mention)

    @demon.command(name="queue", aliases=["list"])
    async def demon_queue(self, ctx: Context, demon: str = "all"):
        queue = await get_demon_queue(demon.lower())
        if demon != "all":
            return await ctx.send(ctx.author.mention, embed=embeds.DefaultEmbed(title=f"Queue for {demon.lower().capitalize()}", description="\n".join(
                [self.bot.get_user(x['offer_id']).display_name +
                 (f" __{await get_friendcode_with_id(x['offer_id'])}__" if await get_friendcode_with_id(x['offer_id']) is not None else "") +
                 f" (_..profile {self.bot.get_user(x['offer_id']).mention}_)"
                 for x in queue])))

        await ctx.send(ctx.author.mention, embed=embeds.DefaultEmbed(title=f"Demon Queue", description="\n".join(
            [self.bot.get_user(x['offer_id']).display_name +
             (f" __{await get_friendcode_with_id(x['offer_id'])}__" if await get_friendcode_with_id(x['offer_id']) is not None else "") +
             f" (_..profile {self.bot.get_user(x['offer_id']).mention}_)"
             f" for {demon_bools_to_str(x)}"
             for x in queue])))

    @demon.command(name="notify", aliases=["ping"])
    async def demon_notify(self, ctx: Context):
        what_demon: List[str] = await ask(ctx,
                                          question="Which demon do you want to be notified for?", convert=demon_converter)
        if len(what_demon) == 0:
            return await update_demon_queue(ctx.author, False, False, False, False)

        if await in_demon_queue(ctx.author):
            await update_demon_queue(ctx.author, "reds" in what_demon, "grays" in what_demon, "crimsons" in what_demon, "bellmoths" in what_demon)
        else:
            await add_demon_queue(ctx.author, "reds" in what_demon, "grays" in what_demon, "crimsons" in what_demon, "bellmoths" in what_demon)
        await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Success", description="You are now in queue for " + ", ".join(what_demon)))

    @demon.command(name="friend", aliases=["friendcode", "code"])
    async def demon_friend(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of = ctx.author

        friendcode: Optional[int] = await get_friendcode(of)

        if friendcode is None:
            if of == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}: You are not registered in the bot yet! `..demon tag <grandcross friendcode> <profile name>` to create one")
            else:
                await ctx.send(f"{ctx.author.mention}: {of.display_name} is not registered in the bot yet!")
        else:
            await ctx.send(f"{ctx.author.mention}: {friendcode}")

    @demon.command(name="offer")
    async def demon_offer(self, ctx: Context, reds: int = 0, greys: int = 0, crimsons: int = 0, belmos: int = 0, *,
                          additional_message: str = ""):
        if reds == 0 and greys == 0 and crimsons == 0 and belmos == 0:
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
                await execute('DELETE FROM "raid_channels" WHERE channel_id=? AND guild=?',
                              (channel_list_item["channel_id"], channel_list_item["guild"]))
                continue
            except discord.Forbidden:
                continue

            mentions: List[str] = []

            red_role = await get_demon_role(guild, "red")
            grey_role = await get_demon_role(guild, "grey")
            crimson_role = await get_demon_role(guild, "crimson")
            belmos_role = await get_demon_role(guild, "bellmoth")
            all_role = await get_demon_role(guild, "all")

            if reds != 0 and red_role is not None:
                mentions.append(guild.get_role(red_role).mention)
            if greys != 0 and grey_role is not None:
                mentions.append(guild.get_role(grey_role).mention)
            if crimsons != 0 and crimson_role is not None:
                mentions.append(guild.get_role(crimson_role).mention)
            if belmos != 0 and belmos_role is not None:
                mentions.append(guild.get_role(belmos_role).mention)

            if all_role is not None and None in [red_role, grey_role, crimson_role, belmos_role]:
                mentions.append(guild.get_role(all_role).mention)

            to_claim: discord.Message = await channel.send(
                content=", ".join(mentions),
                embed=discord.Embed(
                    title=f"{author.display_name} offers:",
                    description="\n" +
                                (f"Reds: `{reds}` \n" if reds != 0 else "") +
                                (f"Greys: `{greys}` \n" if greys != 0 else "") +
                                (f"Crimsons: `{crimsons}` \n" if crimsons != 0 else "") +
                                (f"Bellmoths: `{belmos}` \n" if belmos != 0 else "") +
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
            user: discord.User
            added_reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60 * 60 * 4)

            if user == author:
                await ctx.send(f"{author.mention} deleted your demon offer.")
            else:
                # author_profile: BotUser = await read_bot_user(author)
                # if reds != 0:
                #   await author_profile.add_red_offer(reds)
                # if greys != 0:
                #    await author_profile.add_gray_offer(greys)
                # if crimsons != 0:
                #   await author_profile.add_crimson_offer(crimsons)

                author_friendcode: Optional[int] = await get_friendcode(author)
                claim_friendcode: Optional[int] = await get_friendcode(user)

                if author_friendcode is None and claim_friendcode is None:
                    await author.send(f"{user.display_name} has claimed your demons! (DM me to chat with {user.display_name}. You got 5 Minutes)")
                    await user.send(
                        f"Please contact {author.display_name} from {author.guild.name} for their friendcode (DM me to chat with {author.display_name}. You got 5 Minutes)")
                elif author_friendcode is None and claim_friendcode is not None:
                    await author.send(
                        f"{user.mention} (Friendcode: {claim_friendcode}) has claimed your demons! (DM me to chat with {user.display_name}. You got 5 Minutes)")
                    await user.send(
                        f"Please contact {author.display_name} from {author.guild.name} for their friendcode! (DM me to chat with {author.display_name}. You got 5 Minutes)")
                elif author_friendcode is not None and claim_friendcode is None:
                    await author.send(
                        f"{user.mention} has claimed your demons! (DM me to chat with {user.display_name}. You got 5 Minutes)")
                    await user.send(
                        f"Please add {author.mention} (Friendcode: {author_friendcode}) (DM me to chat with {author.display_name}. You got 5 Minutes)")
                else:
                    await author.send(
                        f"{user.mention} (Friendcode: {claim_friendcode}) has claimed your demons! (DM me to chat with {user.display_name}. You got 5 Minutes)")
                    await user.send(
                        f"You claimed demons from {author.mention} (Friendcode: {author_friendcode}) (DM me to chat with {author.display_name}. You got 5 Minutes)"
                    )

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

            await asyncio.sleep(60 * 5)

            copy = demon_offer_messages.copy()

            for x in copy:
                if demon_offer_messages[x]["creator"].id == author.id:
                    del demon_offer_messages[x]

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
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.channel.DMChannel):
            return

        if message.author.id == self.bot.user.id:
            return

        partner: discord.Member = lookup_demon_info(message.channel.recipient)

        if not partner:
            return None

        await partner.send(f"Message from '{message.author.display_name}' regarding your demons", embed=discord.Embed(
            description=message.content
        ))
        await message.add_reaction(emojis.OK)

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

        channels: List[discord.TextChannel] = [await try_getting_channel(x, self.bot) async for x in
                                               get_raid_channels()]
        await ctx.author.send("\n".join(channels))

    @demon.command(name="role")
    @has_permissions(manage_roles=True)
    async def demon_role(self, ctx: Context, role: discord.Role, demon_type: str):
        await add_demon_role(role, demon_type)
        await ctx.send(f"{ctx.author.mention}: Added Demon role!")


def setup(_bot):
    _bot.add_cog(DemonCog(_bot))
