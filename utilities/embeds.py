import discord
from discord import Embed

import utilities.messages as m


class Help:
    class General:
        HELP_1: Embed = discord.Embed(
            title=m.help_1_title,
            description=m.help_1,
            colour=discord.Color.gold(),
        )
        HELP_2: Embed = discord.Embed(
            title=m.help_2_title,
            description=m.help_2,
            colour=discord.Color.gold(),
        ).set_footer(text=m.help_footer)


UNIT_LOOKUP_ERROR_EMBED: Embed = discord.Embed(title=m.error, colour=discord.Color.dark_red(),
                                               description=m.Unit.lookup)

TEAM_LOOKUP_ERROR_EMBED: Embed = discord.Embed(title=m.error, colour=discord.Color.dark_red(),
                                               description=m.Team.lookup)
TEAM_COOLDOWN_ERROR_EMBED: Embed = discord.Embed(title=m.error, colour=discord.Color.dark_red(),
                                                 description=m.Team.cooldown)

PVP_COOLDOWN_ERROR_EMBED: Embed = discord.Embed(title=m.error, colour=discord.Color.dark_red(),
                                                description=m.PvP.cooldown)

AFFECTION_UNMUTABLE_ERROR_EMBED: Embed = discord.Embed(title=m.error, colour=discord.Color.dark_red(),
                                                       description=m.Affection.Error.unmutable)
AFFECTION_HELP_EMBED: Embed = discord.Embed(title=m.Affection.Help.title, colour=discord.Color.gold(),
                                            description=m.Affection.Help.desc)

AFFECTION_ADDED_EMBED: Embed = discord.Embed(title=m.success, colour=discord.Color.green(), description=m.Affection.add)
AFFECTION_EDITED_EMBED: Embed = discord.Embed(title=m.success, colour=discord.Color.green(),
                                              description=m.Affection.edit)
AFFECTION_REMOVED_EMBED: Embed = discord.Embed(title=m.success, colour=discord.Color.red(),
                                               description=m.Affection.remove)

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
