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
        self.set_thumbnail(url="https://cdn.discordapp.com/avatars/456276194581676062/dda3dc4e7a35fbe4afef3488054363cc.webp?size=256")
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
    )

    pvp_help: HelpEmbed = HelpEmbed(help_title="PvP Help", description="For *criteria* please check bottom").add_field(
        name="Unit",
        value="""__Usage__:
> `unit [criteria]`
```Displays a random unit matching the provided criteria```"""
    ).add_blank_field().add_field(
        name="Team",
        value="""__Usage__:
> `team [criteria]`
```Displays a random team matching the provided criteria
        
If you don't own a unit, click on the number below the message```"""
    ).add_blank_field().add_field(
        name="PvP",
        value="""__Usage__:
> `pvp <@Enemy> [criteria]`
```Create 2 random teams.
        
Each player gets to reroll units he doesn't obtain.```"""
    ).add_blank_field().add_field(
        name="Tarot",
        value="""__Usage__:
> `tarot`
```Custom Rule Set PvP Mode created by 
    Jeremy Hex#0364
        
For ruleset do:``` ```yaml\n..tarot rules```"""
    ).add_blank_field().add_field(
        name="Criteria",
        value="""
        > **race**: `demons, giants, humans, fairies, goddess, unknown`
        > **type**: `blue, red, green`
        > **grade**.: `r, sr, ssr`
        > **event**: `gc, slime, aot, kof, new year, halloween, festival, valentine, rezero`
        > **affection**: `sins, commandments, holy knights, catastrophes, archangels, none, custom added ones...`
        > **name**: `name1, name2, name3, ..., nameN`
        
        
        If you want to define __multiple values append__ them with a `,` after each value
        > `race: demon, giant`
        
        For races: In case you want a team with e.g. 2 demons and 2 giants
        > `race: demon*2, giants*2`
        
        If you want to use __multiple criterias append__ a `&` after each criteria
        > `race: demon & grade: ssr`.
        """
    )

    draw_help: HelpEmbed = HelpEmbed(help_title="Draw Help").add_field(
        name="Single",
        value="""__Usage__:
> `single [@For] [banner]`
```Emulates a single draw on the given banner and adds the unit to @For's the box.
        
If @For is not provided, you will do a single for yourself.
        
For a list of all available banners do:``` ```yaml\n..list banner``` 
"""
    ).add_blank_field().add_field(
        name="Multi",
        value="""__Usage__:
> `multi [@For] [amount] [banner]`
```Same as single, but with a 5x or 11x Draw.
        
If amount is more then 1, a menu button appears and you can navigate through the multis.
Instead of a number you can also provide "rotation" or "rot" to do multis worth of 900 gems.```"""
    ).add_blank_field().add_field(
        name="Shaft",
        value="""__Usage__:
> `shaft [@For] [unit] [banner]`        
```Same as single / multi. Except it will do multis until you pull a SSR Unit.
        
If a unit is provided it will do multis until you pull the desired unit.
        
If the provided unit has different forms, and you want a specific one, make sure to provide a more detailed name. 
    e.g. "Escanor" could be any Escanor, while "The One" could only be The One Escanor.

Some units have small abbreviations as well, to check if the unit has a abbreviation do:``` ```yaml
..info <as detailed name as possible>```"""
    ).add_blank_field().add_field(
        name="Summon",
        value=f"""__Usage__:
> `summon`
```Create a menu emulating the GC Gacha Menu.``` ```yaml
{e.LEFT_ARROW} - Go to the previous banner
        
{e.NO_1} - Do a single on the selected banner
        
{e.NO_10} or {e.NO_5} - Do a multi on the selected banner
        
{e.WHALE} - Do a shaft on the selected banner
        
{e.INFO} - Shows a list of all SSRs in selected Banner
        
{e.RIGHT_ARROW} - Go to the next banner```"""
    ).add_blank_field().add_field(
        name="Banner",
        value="""__Usage__:
> `banner [banner name] `
```Shows a list of all SSRs in the provided banner```"""
    ).add_blank_field().add_field(
        name="Box",
        value="""__Usage__:
> `box [@Of]`
```Show all units @Of has pulled so far.
        
If @Of is not provided, it will display your box```"""
    )

    stats_help: HelpEmbed = HelpEmbed(help_title="Stats Help").add_field(
        name="Stats",
        value="""__Usage__:
> `stats [@Of] [type]`
```Displays @Of's draw statistics.
        
If @Of is not provided, you will be used.```"""
    ).add_blank_field().add_field(
        name="Top",
        value="""__Usage__:
> `top [type]`
```Displays the top 10 members in the provided type.
        
If no type is provided the top 5 members in every type is being displayed```"""
    ).add_blank_field().add_field(
        name="Types",
        value="""```yaml
 luck
 ssrs
 units
 shafts```"""
    )

    list_help: HelpEmbed = HelpEmbed(help_title="List Help").add_field(
        name="Find",
        value="""__Usage__:
> `find <unit name 1>, <unit name 2>`
```Displays all unit with the provided name in their own name
        
e.g. "Escanor" would display the full name of all 3 Escanors```"""
    ).add_blank_field().add_field(
        name="List of units",
        value="""__Usage__:
> `list unit [critera]`
```Displays all units matching the given criteria.
        
If no criteria is given, it will by default display all custom created units.```"""
    ).add_blank_field().add_field(
        name="List of banners",
        value=""""__Usage__:
> `list banner`
```Displays a list of all available Banners in the bot at this moment.```"""
    ).add_blank_field().add_field(
        name="list tarot",
        value="""__Usage__:
> `list tarot`
```Displays a menu with all Tarot Units in the bot.```"""
    )

    demon_help: HelpEmbed = HelpEmbed(
        help_title="Demon Help",
        description="In case you claim demons from someone you don't share a server with you can reply to the offer message to message the person."
    ).add_field(
        name="Offer",
        value="""__Usage__:
> `demon offer <reds> <greys> <crimsons> [additional messages]`
```Offers demons to all registered demon channels.
        
If you click "Ok" the offer gets deleted.```"""
    ).add_blank_field().add_field(
        name="Friendcode",
        value="""__Usage__:
> `demon code [@Of]`
```Displays the first registered Friendcode of "@Of"
        
If "@Of" is not provided, your own code will be shown```"""
    ).add_field(
        name="Creating Profile",
        value="""__Usage__:
> `demon tag <grand cross friendcode> [name]`
```Registers a new profile in the bot, linked to you.
        
If you have multiple account please provide the account name after the friendcode```"""
    ).add_blank_field().add_field(
        name="Accounts",
        value="""__Usage__:
> `demon info [@Of]`
```Shows all Profiles of "@Of"```"""
    ).set_image(url="attachment://image.png")

    @staticmethod
    async def send_demon_help(ctx, content: str):
        return await ctx.send(
            content=content,
            file=await image_to_discord(i.demon_banner),
            embed=Help.demon_help
        )

    custom_help: HelpEmbed = HelpEmbed(help_title="Custom Help").add_field(
        name="Affections",
        value="""```affection```"""
    ).add_blank_field().add_field(
        name="Units",
        value="""```custom```"""
    )


class Stats:
    no_summon_embed: ErrorEmbed = ErrorEmbed(
        error_message="No summons yet",
        description="Use `multi`, `single` or `shaft` command",
    )


class Unit:
    @staticmethod
    def lookup_error(criteria: str):
        return ErrorEmbed(f"Can't find any unit which matches `{criteria}`")


class Team:
    cooldown_error: ErrorEmbed = ErrorEmbed(error_message="Please wait before using another `..team`")

    @staticmethod
    def lookup_error(criteria: str):
        return ErrorEmbed(f"Can't find any team which matches `{criteria}`")


class PvP:
    cooldown_error: ErrorEmbed = ErrorEmbed(error_message="Please wait before using another `..pvp`")


class Affection:
    _help: HelpEmbed = HelpEmbed("Help for Affection").add_field(
        name="add",
        value="""
        __Usage__:
        > `affection add <name>`
```Creates a new Affection```"""
    ).add_blank_field().add_field(
        name="remove",
        value="""
        __Usage__:
        > `affection remove <name>`
```Deletes the Affection if you are the owner```"""
    ).add_blank_field().add_field(
        name='edit',
        value="""
        __Usage__:
        > `affection edit "<name>" <new name>`
```Changes the name of the affection
        
If you are the owner of the affection```"""
    ).add_blank_field().add_field(
        name='transfer',
        value="""
        __Usage__:
        > `affection transfer "<name>" <@New Owner>`
```Transfers Ownership of the affection to another User
        
Please mind that you do loose all permission to the affection!```"""
    ).add_blank_field().add_field(
        name="list",
        value="```Displays a list of all affections```"
    ).add_blank_field(True).add_field(
        name="help",
        value="```Displays this help message```"
    ).set_image(url="attachment://image.png")

    @staticmethod
    def unmutable(affection_name: str):
        return ErrorEmbed(f"Affection `{affection_name}` can not be added/ edited/ removed!")

    @staticmethod
    def exists(affection_name: str):
        return ErrorEmbed(f"Affection `{affection_name}` exists already!")

    @staticmethod
    def not_existing(affection_name: str):
        return ErrorEmbed(f"Affection `{affection_name}` doesn't exist!")

    @staticmethod
    def wrong_owner(affection_name: str):
        return ErrorEmbed(f"Affection `{affection_name}` wasn't created by you!")

    @staticmethod
    async def send_help(ctx, content: str):
        return await ctx.send(
            content=content,
            file=await image_to_discord(i.affection_banner),
            embed=Affection._help
        )

    class Add:
        usage: ErrorEmbed = ErrorEmbed(
            error_message="Adding affection failed",
            description="""
            __Usage__:
            > `affection add <name>`
            """
        )

        @staticmethod
        def success(affection_name: str):
            return SuccessEmbed(f"Affection `{affection_name}` added!")

    class Edit:
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection edit "<name>" <new name>`
            """
        )

        @staticmethod
        def success(old_affection_name: str, new_affection_name: str):
            return SuccessEmbed(f"Changed Affection `{old_affection_name}` to `{new_affection_name}`!")

    class Remove:
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection remove <name>`
            """
        )

        @staticmethod
        def success(affection_name: str):
            return SuccessEmbed(f"Affection `{affection_name}` removed!")

    class Transfer:
        usage: ErrorEmbed = ErrorEmbed(
            error_message="""
            __Usage__:
            > `affection transfer "<name>" <@New Owner>`
            """
        )

        @staticmethod
        def success(affection_name: str, owner: str):
            return SuccessEmbed(f"Affection `{affection_name}` transfered to *{owner}*")


class Custom:
    _help: HelpEmbed = HelpEmbed("Help for Custom").add_field(
        name="Create",
        value="""__Usage__:
> `custom create name: <name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
```Creates a new (custom) Unit

Defaultly race is "unknown" & affection is "none"```"""
    ).add_blank_field().add_field(
        name="Remove",
        value="""__Usage__:
> `custom remove name: <name>`
```Removes the unit (if you are it's owner)```"""
    ).add_blank_field().add_field(
        name="Edit",
        value="""__Usage__:
> `..custom edit name:<name> & type:[type] & grade:[grade] & owner:[@Owner] & updated_name:[updated name] & url:[url] & race:[race] & affection:[affection]`
```Changes attributes of the Unit (if you are it's owner)

You **__don't__** need to provide criteria if you don't want to edit it!```
            
**__Criteria__**:
    *type: <type>*
        The (new) type of the Unit: `red`, `green` or `blue`
                
    *grade: <grade>*
        The (new) grade of the Unit: `r`, `sr`, `ssr`    
                
    *url: <image url>*
        The (new) url to the image of the Unit: `any valid url with .png or .jpg`
                
    *race: <race>*
        The (new) race of the Unit: `demon, giant, human, god, fairy, unknown`
                
    *affection: <affection>*
        The (new) affection of the Unit: `do ..affection list`
                
    *updated_name: <new name>*
        The new name of the Unit: `Any Text`"""
    ).set_image(url="attachment://image.png")
    _missing: ErrorEmbed = ErrorEmbed("Missing argument!")
    _wrong_owner: ErrorEmbed = ErrorEmbed(error_message="Affection is not yours!")

    @staticmethod
    def missing(arguments: str):
        return ErrorEmbed(f"Missing `{arguments}`")

    @staticmethod
    def wrong_owner(unit_name: str):
        return ErrorEmbed(f"Unit `{unit_name}` wasn't created by you!")

    @staticmethod
    async def send_help(ctx, content: str):
        return await ctx.send(
            content=content,
            file=await image_to_discord(i.custom_banner),
            embed=Custom._help
        )

    class Edit:
        @staticmethod
        def success(unit_name: str, edited_fields: str):
            return SuccessEmbed(f"Changed `{edited_fields}` for *{unit_name}*")

        @staticmethod
        def nothing_changed(unit_name: str):
            return SuccessEmbed(f"Nothing changed for `{unit_name}`")

    class Remove:
        @staticmethod
        def success(unit_name: str):
            return SuccessEmbed(f"Removed Unit `{unit_name}` successfully")


class Tourney:
    help: Embed = discord.Embed(title=m.Tourney.Help.title, colour=discord.Color.gold(),
                                description=m.Tourney.Help.desc)


def loading(title: str = "Loading..."):
    return DefaultEmbed(title=title).set_thumbnail(
        url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/loading.gif")
