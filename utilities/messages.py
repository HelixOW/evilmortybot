HELP_1_TITLE = "Help 1/2"

HELP_1 = """
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
        """

HELP_2_TITLE = "Help 2/2"

HELP_2 = """
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
        """

HELP_FOOTER = "Feel free to ask questions!"

SUCCESS = "Success"
ERROR = "Error"

class Unit:
    LOOKUP = "Can't find any unit which meets those requirements"


class Team:
    LOOKUP = "Can't find any team which meets those requirements"
    COOLDOWN = "Please wait before using another ..team"


class PvP:
    COOLDOWN = "Please wait before using another ..pvp"


class Affection:
    class Error:
        UNMUTABLE = "This Affection can not be added/ edited/ removed!"

    class Help:
        TITLE = "Help for ..affection"
        DESC = """
`..affection add <name>` 
    Creates a new Affection

`..affection remove <name>`
    Deletes the Affection if you are the owner
    
`..affection edit "<name>" <new name>`
    Changes the name of the Affection
    
`..affection transfer "<name>" <@New Owner>`
    Transfers Ownership of the affection to another User
    Please mind that you do loose all permission to the affection!
    
`..affection list`
    Displays a list of all affections

`..affection help`
    Displays this help message
        """

    ADD = "Affection added!"
    EDIT = "Affection edited!"
    REMOVE = "Affection removed!"


class Custom:
    class Help:
        TITLE = "Help for ..custom"
