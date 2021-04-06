import discord
from discord import Embed
from utilities.units import image_to_discord

import utilities.messages as m
import utilities.reactions as e
import utilities.images as i


class ErrorEmbed(Embed):
    def __init__(self, error_message: str, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.dark_red()
        self.set_author(
            name="Error: " + error_message,
            icon_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/error.png"
        )
        self.set_footer(text="© Heⅼіх Sama#0578",
                        icon_url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")


class HelpEmbed(Embed):
    def __init__(self, help_title: str, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.gold()
        self.set_author(
            name=help_title,
            icon_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/help.png"
        )
        self.set_footer(text="© Heⅼіх Sama#0578",
                        icon_url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")
        self.blank_fields = 0

    def add_blank_field(self, inline=False):
        self.blank_fields += 1
        self.add_field(
            name="\u200b"*self.blank_fields,
            value="\u200b",
            inline=inline
        )
        return self


class SuccessEmbed(Embed):
    def __init__(self, success_title, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.green()
        self.set_author(
            name=success_title,
            icon_url="https://media.discordapp.net/attachments/818474483743588392/828791636069974066/success.png"
        )


class Help:
    help: HelpEmbed = HelpEmbed(
        help_title="Help Page 1",
        description="__*Commands:*__ (Either start with `..`, `>king`, `>diane`)"
    ).add_field(
        name="unit [criteria]",
        value="""
        Displays a random unit matching the provided criteria
        
        Please check criteria down below
        """
    ).add_field(
        name="team [criteria]",
        value="""
        Displays a random team matching the provided criteria
        
        If you don't own a unit, click on the number below the message
        
        Please check criteria down below
        """
    ).add_field(
        name="pvp <@Enemy> [criteria]",
        value="""
        Create 2 random teams.
        
        Each player gets to reroll units he doesn't obtain.
        
        Please check criteria down below
        """
    ).add_field(
        name="tarot",
        value="""
        Custom Rule Set PvP Mode created by `Jeremy Hex#0364`
        
        For ruleset do ..tarot rules
        """
    ).add_blank_field(
    ).add_field(
        name="single [@For] [banner]",
        value="""
        Emulates a single draw on the given banner and adds the unit to @For's the box.
        
        If @For is not provided, you will do a single for yourself.
        
        For a list of all avaiable banners do `..list banner`
        """
    ).add_field(
        name="..multi [@For] [amount] [banner]",
        value="""
        Same as single, but with a 5x or 11x Draw.
        
        If amount is more then 1, a menu button appears and you can navigate through the multis.
        Instead of a number you can also provide `rotation` or `rot` to do multis worth of 900 gems.
        """
    ).add_field(
        name="shaft [@For] [unit] [banner]",
        value="""
        Same as single / multi. Except it will do multis until you pull a SSR Unit.
        
        If a unit is provided it will do multis until you pull the desired unit.
        
        If the provided unit has different forms, and you want a specific one, make sure to provide a more detailed name.
        e.g. `Escanor` could be any Escanor, while `The One` could only be The One Escanor.
        Some units have small abbreviations as well, to check if the unit has a abbreviation do ..info <as detailed name as possible>
        """
    ).add_field(
        name="summon",
        value=f"""
        Create a menu emulating the GC Gacha Menu.
        
        >>> {e.LEFT_ARROW} - Go to the previous banner
        {e.NO_1} - Do a single on the selected banner
        {e.NO_10} or {e.NO_5} - Do a multi on the selected banner
        {e.WHALE} - Do a shaft on the selected banner
        {e.INFO} - Shows a list of all SSRs in selected Banner
        {e.RIGHT_ARROW} - Go to the next banner
        """
    ).add_field(
        name="banner [banner name]",
        value="""
        Shows a list of all SSRs in the provided banner
        """
    ).add_field(
        name="box [@Of]",
        value="""
        Show all units @Of has pulled so far.
        
        If @Of is not provided, it will displays your box
        """
    ).add_blank_field(
    ).add_field(
        name="stats [@Of] [type]",
        value="""
        Displays @Of's draw statistics.
        
        If @Of is not provided, you will be used.
        
        Allowed types are:
        > luck
        > ssrs
        > units
        > shafts
        """
    ).add_field(
        name="top [type]",
        value="""
        Displays the top 10 members in the provided type.
        
        If no type is provided the top 5 members in every type is being displayed
        
        Allowed types are:
        > luck
        > ssrs
        > units
        > shafts
        """
    ).add_blank_field(
    ).add_field(
        name="find <unit names>",
        value="""
        Displays all unit with the provided name in their own name
        
        e.g. `Escanor` would display the full name of all 3 escanors
        """
    ).add_field(
        name="list unit [criteria]",
        value="""
        Displays all units matching the given criteria.
        
        If no criteria is given, it will by default display all custom created units.
        """
    ).add_field(
        name="list banner",
        value="Displays a list of all available Banners in the bot at this moment."
    ).add_field(
        name="list tarot",
        value="Displays a menu with all Tarot Units in the bot."
    ).add_blank_field(
    ).add_field(
        name="demon",
        value="Please issue the command for more info"
    ).add_field(
        name="custom",
        value="Please issue the command for more info"
    ).add_blank_field(
    ).add_field(
        name="Criteria",
        value="""
        > race: `demons, giants, humans, fairies, goddess, unknown`
        > 
        > type: `blue, red, green`
        > 
        > grade: `r, sr, ssr`
        > 
        > event: `gc, slime, aot, kof, new year, halloween, festival, valentine, rezero`
        > 
        > affection: `sins, commandments, holy knights, catastrophes, archangels, none, custom added ones...`
        > 
        > name: name1, name2, name3, ..., nameN`
        
        If you want to define __multiple values append__ them with a `,` after each value
        > race: demon *,*giant
        If you want to use __multiple criterias append__ a `&` after each criteria
        > race: demon & grade: ssr
        """
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")


class Stats:
    no_summon_embed: ErrorEmbed = ErrorEmbed(
        error_message="No summons yet",
        description="Use `..multi`, `..single` or `..shaft`",
    )


class Unit:
    lookup_error: ErrorEmbed = ErrorEmbed(error_message="Can't find any unit which matches given criteria")


class Team:
    lookup_error: ErrorEmbed = ErrorEmbed(error_message="Can't find any team which matches given criteria")
    cooldown_error: ErrorEmbed = ErrorEmbed(error_message="Please wait before using another `..team`")


class PvP:
    cooldown_error: ErrorEmbed = ErrorEmbed(error_message="Please wait before using another `..pvp`")


class Affection:
    unmutable_error: ErrorEmbed = ErrorEmbed(error_message="This Affection can not be added/ edited/ removed!")
    exists_error: ErrorEmbed = ErrorEmbed(error_message="This Affection exists already!")
    help_embed: HelpEmbed = HelpEmbed(
        help_title="Help for Affection"
    ).add_field(
        name="add",
        value="""
        __Usage__:
        > `affection add <name>`
        
        Creates a new Affection
        \u200b
        """
    ).add_blank_field(
        True
    ).add_field(
        name="remove",
        value="""
        __Usage__:
        > `affection remove <name>`
        
        Deletes the Affection if you are the owner
        \u200b
        """
    ).add_field(
        name='edit',
        value="""
        __Usage__:
        > `affection edit "<name>" <new name>`
        
        Changes the name of the affection
        
        If you are the owner of the affection
        \u200b
        """
    ).add_blank_field(
        True
    ).add_field(
        name='transfer',
        value="""
        __Usage__:
        > `affection transfer "<name>" <@New Owner>`
        
        Transfers Ownership of the affection to another User
        
        Please mind that you do loose all permission to the affection!
        \u200b
        """
    ).add_field(
        name="list",
        value="Displays a list of all affections"
    ).add_blank_field(
        True
    ).add_field(
        name="help",
        value="Displays this help message"
    ).set_image(url="attachment://image.png")

    class Add:
        success: SuccessEmbed = SuccessEmbed(success_title="Affection added!")
        usage: ErrorEmbed = ErrorEmbed(
            error_message="Adding affection failed",
            description="""
            __Usage__:
            > `affection add <name>`
            """
        )

    edited: SuccessEmbed = SuccessEmbed(success_title="Affection edited!")
    removed: SuccessEmbed = SuccessEmbed(success_title="Affection removed!")


async def affection_help(ctx, content: str):
    return await ctx.send(
        content=content,
        file=await image_to_discord(i.affection_banner),
        embed=Affection.help_embed
)


CUSTOM_HELP_EMBED: Embed = discord.Embed(title=m.Custom.Help.title, colour=discord.Color.gold(),
                                         description=m.Custom.Help.desc)
CUSTOM_ADD_COMMAND_USAGE_EMBED: Embed = discord.Embed(title=m.Custom.Add.Error.title, colour=discord.Color.dark_red(),
                                                      description=m.Custom.Add.Error.desc)
CUSTOM_EDIT_COMMAND_USAGE_EMBED: Embed = discord.Embed(title=m.Custom.Edit.Error.title, colour=discord.Color.dark_red(),
                                                       description=m.Custom.Edit.Error.desc)
CUSTOM_EDIT_COMMAND_SUCCESS_EMBED: Embed = discord.Embed(title=m.Custom.Edit.Success.title,
                                                         colour=discord.Color.green(),
                                                         description=m.Custom.Edit.Success.desc)
CUSTOM_REMOVE_COMMAND_USAGE_EMBED: Embed = discord.Embed(title=m.Custom.Remove.Error.title,
                                                         colour=discord.Color.dark_red(),
                                                         description=m.Custom.Remove.Error.desc)
CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED: Embed = discord.Embed(title=m.success, colour=discord.Color.green(),
                                                           description=m.Custom.Remove.success)

DEMON_HELP_EMBED: Embed = discord.Embed(title=m.Demon.Help.title, colour=discord.Color.gold(),
                                        description=m.Demon.Help.desc)


class TourneyEmbeds:
    HELP: Embed = discord.Embed(title=m.Tourney.Help.title, colour=discord.Color.gold(),
                                description=m.Tourney.Help.desc)


LOADING_EMBED: Embed = discord.Embed(title=m.loading)
IMAGES_LOADED_EMBED: Embed = discord.Embed(title=m.loaded)
