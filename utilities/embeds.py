import discord
import utilities.messages as m


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

CUSTOM_HELP_EMBED = discord.Embed(title=m.Custom.Help.TITLE, colour=discord.Color.gold(), description=m.Custom.Help.DESC)
CUSTOM_ADD_COMMAND_USAGE_EMBED = discord.Embed(title=m.Custom.Add.Error.TITLE, colour=discord.Color.dark_red(),
                                               description=m.Custom.Add.Error.DESC)
CUSTOM_EDIT_COMMAND_USAGE_EMBED = discord.Embed(title=m.Custom.Edit.Error.TITLE, colour=discord.Color.dark_red(),
                                                description=m.Custom.Edit.Error.DESC)
CUSTOM_EDIT_COMMAND_SUCCESS_EMBED = discord.Embed(title=m.Custom.Edit.Success.TITLE, colour=discord.Color.green(),
                                                  description=m.Custom.Edit.Success.DESC)
CUSTOM_REMOVE_COMMAND_USAGE_EMBED = discord.Embed(title=m.Custom.Remove.Error.TITLE, colour=discord.Color.dark_red(),
                                                  description=m.Custom.Remove.Error.DESC)
CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED = discord.Embed(title=m.SUCCESS, colour=discord.Color.green(),
                                                    description=m.Custom.Remove.SUCCESS)

CROP_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(),
                                               description=m.Crop.USAGE)

RESIZE_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title=m.ERROR, colour=discord.Color.dark_red(),
                                                 description=m.Resize.USAGE)

DEMON_HELP_EMBED = discord.Embed(title=m.Demon.Help.TITLE, colour=discord.Color.gold(),
                                 description=m.Demon.Help.DESC)


class TourneyEmbeds:
    HELP = discord.Embed(title=m.Tourney.Help.TITLE, colour=discord.Color.gold(), description=m.Tourney.Help.DESC)


LOADING_EMBED = discord.Embed(title=m.LOADING)
IMAGES_LOADED_EMBED = discord.Embed(title=m.LOADED)
