import discord

HELP_EMBED_1 = discord.Embed(
    title="Help 1/2",
    description="""
                __*Commands:*__
                    `..unit` -> `Check Info`
                    `..team` -> `Check Info`
                    `..pvp <@Enemy>` -> `Check Info`
                    `..single [@For=You] [banner=banner 1]` 
                    `..multi [@For=You] [banner=banner 1]`
                    `..shaft [@For=You] [unit="Unit name"] [banner=banner 1]`
                    `..summon`
                    `..banner [banner=banner 1]`
                    `..stats <luck, ssrs, units, shafts>`
                    `..top <luck, ssrs, units, shafts>`
                    `..box [@Of=You]`
                    `..find <unit name>`
                    `..list unit [criteria=event: custom]` -> `for criteria check Info`
                    `..list banner`
                    `..demon` -> `Execute for more Info`
                    `..custom` -> `Execute for more Info`
                            """,
    colour=discord.Color.gold(),
)

HELP_EMBED_2 = discord.Embed(
    title="Help 2/2",
    description="""
    __*Info:*__
                    You can use different attributes to narrow down the possibilities:
                     `race:` demons, giants, humans, fairies, goddess, unknown
                     `type:` blue, red, green
                     `grade:` r, sr, ssr
                     `event:` gc, slime, aot, kof, new year, halloween, festival, valentine
                     `affection:` sins, commandments, holy knights, catastrophes, archangels, none, custom added ones...
                     `name:` name1, name2, name3, ..., nameN

                    If you want to define e.g. __multiple races append__ them with a `,` after each race
                    If you want to use __multiple attributes append__ a `&` after each attribute

                    `<>`, that means you **have to provide** this argument
                    `[]`, that means you **can provide** this argument
                    `=` inside a argument means, whatever comes after the equals is the **default value**
    
    __Examples:__
                    `..unit` ~ returns a random unit
                    `..unit race: demons, giants & type: red` ~ returns a random red demon or red giant
                    `..team` ~ returns a random pvp team
                    `..team race: demons` ~ returns a random pvp team with only demons
                    `..single part two` ~ does a single summon on the Part 2 banner
                    `..multi race two` ~ does a 5x summon on the Demon/Fairy/Goddess banner
                    `..multi banner two` ~ does a 11x summon on the most recent banner                    
                    `..shaft` ~ does a 11x summon until you get a SSR
                    `..shaft race two` ~ does a 5x summon on the Demon/Fairy/Goddess banner until you get a SSR
                    `..custom create name:[Demon Slayer] Tanjiro & type: red & grade; sr & url: <URL to image> & race: human` ~ Creates a Red SR Tanjiro
    """,
    colour=discord.Color.gold(),
).set_footer(text="Ping `Helix Sama#0001` for additional help!")

UNIT_LOOKUP_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                        description="Can't find any unit which meets those requirements")

TEAM_LOOKUP_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                        description="Can't find any team which meets those requirements")
TEAM_COOLDOWN_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                          description="Please wait before using another ..team")

PVP_COOLDOWN_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                         description="Please wait before using another ..pvp")

SUMMON_THROTTLE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                            description="Please don't summon more then 5x at once")

AFFECTION_UNMUTABLE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                description="This Affection can not be added/removed!")
AFFECTION_HELP_EMBED = discord.Embed(title="Help for ..affection", colour=discord.Color.gold(),
                                     description="""
                                     `..affection <action> <name>`

                                     *__actions__*: 
                                     `add <name>`,
                                     `remove <name>`,
                                     `edit <name> name: <new name>`, 
                                     `transfer <name> owner: @<new owner>`,
                                     `list`,
                                     `help`
                                      """)
AFFECTION_ADDED_EMBED = discord.Embed(title="Success", colour=discord.Color.green(), description="Affection added!")
AFFECTION_EDITED_EMBED = discord.Embed(title="Success", colour=discord.Color.green(), description="Affection edited!")
AFFECTION_REMOVED_EMBED = discord.Embed(title="Success", colour=discord.Color.red(), description="Affection removed!")

CUSTOM_HELP_EMBED = discord.Embed(title="Help for ..custom", colour=discord.Color.gold(),
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
