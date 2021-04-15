import discord
from discord import Embed
from utilities.units import image_to_discord

import utilities.messages as m
import utilities.reactions as e
import utilities.images as i


class DefaultEmbed(Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.dark_teal()
        self.set_footer(text="© Heⅼіх Sama#0578",
                        icon_url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")


class ErrorEmbed(Embed):
    def __init__(self, error_message: str = "\u200b", **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.dark_red()
        self.set_author(
            name="Error: " + error_message,
            icon_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/error.png"
        )

    def set_title(self, error_title: str):
        self.set_author(
            name="Error: " + error_title,
            icon_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/error.png"
        )
        return self


class HelpEmbed(DefaultEmbed):
    def __init__(self, help_title: str, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.gold()
        self.set_author(
            name=help_title,
            icon_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/help.png"
        )
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
    def __init__(self, success_title="\u200b", **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.green()
        self.set_title(success_title)

    def set_title(self, success_title: str):
        self.set_author(
            name=success_title,
            icon_url="https://media.discordapp.net/attachments/818474483743588392/828791636069974066/success.png"
        )
        return self


class DrawEmbed(DefaultEmbed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.colour = discord.Colour.dark_teal()
        self.set_footer(text="© Heⅼіх Sama#0578",
                        icon_url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")
        self.set_image(url="attachment://image.png")


class Help:
    general_help: HelpEmbed = HelpEmbed(
        help_title="General Help",
        description="*Commands* (Either starts with `..`, `k> ` or `d> `)"
    ).add_field(
        name="PvP",
        value="```help pvp```"
    ).add_field(
        name="Draw",
        value="```help draw```"
    ).add_field(
        name="Stats",
        value="```help stats```"
    ).add_field(
        name="Demon",
        value="```help demon```"
    ).add_field(
        name="Custom",
        value="```help custom```"
    ).add_field(
        name="List",
        value="```help list```"
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")

    pvp_help: HelpEmbed = HelpEmbed(help_title="PvP Help").add_field(
        name="unit [criteria]",
        value="""```Displays a random unit matching the provided criteria
        
Please check criteria down below```"""
    ).add_field(
        name="team [criteria]",
        value="""```Displays a random team matching the provided criteria
        
If you don't own a unit, click on the number below the message
        
Please check criteria down below```
        \u200b"""
    ).add_field(
        name="pvp <@Enemy> [criteria]",
        value="""```Create 2 random teams.
        
Each player gets to reroll units he doesn't obtain.
        
Please check criteria down below```"""
    ).add_field(
        name="tarot",
        value="""```Custom Rule Set PvP Mode created by 
    Jeremy Hex#0364
        
For ruleset do:``` ```yaml\n..tarot rules```"""
    ).add_blank_field().add_field(
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
        > name: `name1, name2, name3, ..., nameN`
        
        
        If you want to define __multiple values append__ them with a `,` after each value
        > `race: demon, giant`
        
        For races: In case you want a team with e.g. 2 demons and 2 giants
        > `race: demon*2, giants*2`
        
        If you want to use __multiple criterias append__ a `&` after each criteria
        > `race: demon & grade: ssr`
        """
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")

    draw_help: HelpEmbed = HelpEmbed(help_title="Draw Help").add_field(
        name="single [@For] [banner]",
        value="""```Emulates a single draw on the given banner and adds the unit to @For's the box.
        
If @For is not provided, you will do a single for yourself.
        
For a list of all available banners do:``` ```yaml\n..list banner``` 
        """
    ).add_blank_field().add_field(
        name="multi [@For] [amount] [banner]",
        value="""```Same as single, but with a 5x or 11x Draw.
        
If amount is more then 1, a menu button appears and you can navigate through the multis.
Instead of a number you can also provide "rotation" or "rot" to do multis worth of 900 gems.```"""
    ).add_blank_field().add_field(
        name="shaft [@For] [unit] [banner]",
        value="""```Same as single / multi. Except it will do multis until you pull a SSR Unit.
        
If a unit is provided it will do multis until you pull the desired unit.
        
If the provided unit has different forms, and you want a specific one, make sure to provide a more detailed name. 
    e.g. "Escanor" could be any Escanor, while "The One" could only be The One Escanor.

Some units have small abbreviations as well, to check if the unit has a abbreviation do:``` ```yaml
..info <as detailed name as possible>```"""
    ).add_blank_field().add_field(
        name="summon",
        value=f"""```Create a menu emulating the GC Gacha Menu.``` ```yaml
{e.LEFT_ARROW} - Go to the previous banner
        
{e.NO_1} - Do a single on the selected banner
        
{e.NO_10} or {e.NO_5} - Do a multi on the selected banner
        
{e.WHALE} - Do a shaft on the selected banner
        
{e.INFO} - Shows a list of all SSRs in selected Banner
        
{e.RIGHT_ARROW} - Go to the next banner```"""
    ).add_blank_field().add_field(
        name="banner [banner name]",
        value="""```Shows a list of all SSRs in the provided banner```"""
    ).add_blank_field().add_field(
        name="box [@Of]",
        value="""```Show all units @Of has pulled so far.
        
If @Of is not provided, it will display your box```"""
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")

    stats_help: HelpEmbed = HelpEmbed(help_title="Stats Help").add_field(
        name="stats [@Of] [type]",
        value="""```Displays @Of's draw statistics.
        
If @Of is not provided, you will be used.
        
Allowed types are:``` ```yaml
 luck
 ssrs
 units
 shafts```"""
    ).add_field(
        name="top [type]",
        value="""```Displays the top 10 members in the provided type.
        
If no type is provided the top 5 members in every type is being displayed
        
Allowed types are:``` ```yaml
 luck
 ssrs
 units
 shafts```"""
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")


    list_help: HelpEmbed = HelpEmbed(help_title="List Help").add_field(
        name="find <unit names>",
        value="""```Displays all unit with the provided name in their own name
        
e.g. "Escanor" would display the full name of all 3 Escanors```"""
    ).add_field(
        name="list unit [criteria]",
        value="""```Displays all units matching the given criteria.
        
If no criteria is given, it will by default display all custom created units.```"""
    ).add_field(
        name="list banner",
        value="```Displays a list of all available Banners in the bot at this moment.```"
    ).add_field(
        name="list tarot",
        value="```Displays a menu with all Tarot Units in the bot.```"
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")

    demon_help: HelpEmbed = HelpEmbed(
        help_title="Demon Help",
        description="In case you claim demons from someone you don't share a server with you can reply to the offer message to message the person."
    ).add_field(
        name="demon offer <reds> <greys> <crimsons> [additional messages]",
        value="""```Offers demons to all registered demon channels.
        
If you click "Ok" the offer gets deleted.```
\u200b"""
    ).add_blank_field(True).add_field(
        name="demon code [@Of]",
        value="""```Displays the first registered Friendcode of "@Of"
        
If "@Of" is not provided, your own code will be shown```
\u200b"""
    ).add_field(
        name="demon tag <grand cross friendcode> [name]",
        value="""```Registers a new profile in the bot, linked to you.
        
If you have multiple account please provide the account name after the friendcode```"""
    ).add_blank_field(True).add_field(
        name="demon info [@Of]",
        value="""```Shows all Profiles of "@Of"```"""
    ).set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")

    custom_help: HelpEmbed = HelpEmbed(
        help_title="Custom Help"
    ).add_field(
        name="custom",
        value="```Please issue the command for more info```"
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
    not_existing_error: ErrorEmbed = ErrorEmbed(error_message="This Affection doesn't exist!")
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

    @staticmethod
    async def send_help(ctx, content: str):
        return await ctx.send(
            content=content,
            file=await image_to_discord(i.affection_banner),
            embed=Affection.help_embed
        )

    class Add:
        _success: SuccessEmbed = SuccessEmbed()
        usage: ErrorEmbed = ErrorEmbed(
            error_message="Adding affection failed",
            description="""
            __Usage__:
            > `affection add <name>`
            """
        )

        @staticmethod
        def success(affection_name: str):
            Affection.Add._success.set_title(f"Affection `{affection_name}` added!")

    class Edit:
        _success: SuccessEmbed = SuccessEmbed(success_title="Affection edited!")
        _wrong_owner: ErrorEmbed = ErrorEmbed()
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection edit "<name>" <new name>`
            """
        )

        @staticmethod
        def success(affection_name: str):
            Affection.Edit._success.set_title(f"Affection `{affection_name}` edited!")

        @staticmethod
        def wrong_owner(affection_name: str):
            Affection.Edit._wrong_owner.set_title(affection_name)

    class Remove:
        success: SuccessEmbed = SuccessEmbed(success_title="Affection removed!")
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection remove <name>`
            """
        )

    class Transfer:
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection transfer "<name>" <@New Owner>`
            """
        )

        @staticmethod
        def success():
            pass


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


LOADING_EMBED: DefaultEmbed = discord.Embed(title=m.loading).set_thumbnail(url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/loading.gif")
IMAGES_LOADED_EMBED: DefaultEmbed = discord.Embed(title=m.loaded)
