import discord
import messages as m


class Help:
    class General:
        HELP_1 = discord.Embed(
            title=m.HELP_1_TITLE,
            description=m.HELP_1,
            colour=discord.Color.gold(),
        )
        HELP_2 = discord.Embed(
            title=m.HELP_2_TITLE,
            description=m.HELP_2,
            colour=discord.Color.gold(),
        ).set_footer(text=m.HELP_FOOTER)


UNIT_LOOKUP_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(), description=m.Unit.LOOKUP)

TEAM_LOOKUP_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(), description=m.Team.LOOKUP)
TEAM_COOLDOWN_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(), description=m.Team.COOLDOWN)

PVP_COOLDOWN_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(), description=m.PvP.COOLDOWN)

AFFECTION_UNMUTABLE_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(),
                                                description=m.Affection.Error.UNMUTABLE)
AFFECTION_HELP_EMBED = discord.Embed(title=m.Affection.Help.TITLE, colour=discord.Color.gold(),
                                     description=m.Affection.Help.DESC)

AFFECTION_ADDED_EMBED = discord.Embed(title=m.SUCCESS, colour=discord.Color.green(), description=m.Affection.ADD)
AFFECTION_EDITED_EMBED = discord.Embed(title=m.SUCCESS, colour=discord.Color.green(), description=m.Affection.EDIT)
AFFECTION_REMOVED_EMBED = discord.Embed(title=m.SUCCESS, colour=discord.Color.red(), description=m.Affection.REMOVE)

CUSTOM_HELP_EMBED = discord.Embed(title=m.Custom.Help.TITLE, colour=discord.Color.gold(),
                                  description="""
                                  `..custom create name:<name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
                                  `..custom remove name:<name>`
                                  `..custom edit name:<name> & type:[type] & grade:[grade] & owner:[@Owner] & updated_name:[updated name] & url:[url] & race:[race] & affection:[affection]`
                                  """)
CUSTOM_ADD_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom create", colour=discord.Color.dark_red(),
                                               description="""
                                               `..custom create name:<name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
                                               """)
CUSTOM_EDIT_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom edit", colour=discord.Color.dark_red(),
                                                description="""
                                               `..custom edit name:<name> & criteria:<value1> & criteria2:<value2>`

                                               **__Criteria__**:
                                               `type: <type>`,
                                               `grade: <grade>`,
                                               `url: <image url>`,
                                               `race: <race>`,
                                               `affection: <affection>`
                                               `updated_name: <new name>`
                                               """)
CUSTOM_EDIT_COMMAND_SUCCESS_EMBED = discord.Embed(title="Success", colour=discord.Color.green(),
                                                  description="Unit successfully edited!")
CUSTOM_REMOVE_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom remove", colour=discord.Color.dark_red(),
                                                  description="""
                                                  `..custom remove name:<name>`
                                                  """)
CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED = discord.Embed(title="Success", colour=discord.Color.green(),
                                                    description="Unit successfully removed!")

CROP_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                               description="..crop requires at least a url of a file to crop (..help for more)")

RESIZE_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                 description="..resize requires at least a url of a file to crop (..help for more)")

DEMON_HELP_EMBED = discord.Embed(title="Help for ..demon", colour=discord.Color.gold(),
                                 description="""
                                 `..demon offer <reds> <greys> <crimsons>` to offer demons (Click "OK" to claim)
                                 `..demon tag <grand cross friendcode> [name] [slot]` to create a profile
                                 `..demon info` to show your info
                                 """)

LOADING_EMBED = discord.Embed(title="Loading...")
IMAGES_LOADED_EMBED = discord.Embed(title="Images loaded!")
