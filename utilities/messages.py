help_1_title: str = "Help 1/2"

help_1: str = """
__*Commands:*__
    `..unit` -> `Check Info`
    `..team [amount=1]` -> `Check Info`
    `..pvp <@Enemy>` -> `Check Info`
    `..tarot` -> `Check Info`
    `..single [@For=You] [banner=banner 1]` 
    `..multi [@For=You] [amount=1] [banner=banner 1]`
    `..shaft [@For=You] [unit="Unit name"] [banner=banner 1]`
    `..summon`
    `..banner [banner=banner 1]`
    `..stats <luck, ssrs, units, shafts>`
    `..top <luck, ssrs, units, shafts>`
    `..box [@Of=You]`
    `..find <unit name>`
    `..list unit [criteria=event: custom]` -> `for criteria check Info`
    `..list banner`
    `..list tarot`
    `..demon` -> `Execute for more Info`
    `..custom` -> `Execute for more Info`
        """

help_2_title: str = "Help 2/2"

help_2: str = """
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

help_footer: str = "Feel free to ask questions!"

success: str = "Success"
error: str = "Error"

loading: str = "Loading..."
loaded: str = "Images loaded!"


class Unit:
    lookup: str = "Can't find any unit which meets those requirements"


class Team:
    lookup: str = "Can't find any team which meets those requirements"
    cooldown: str = "Please wait before using another ..team"


class PvP:
    cooldown: str = "Please wait before using another ..pvp"


class Affection:
    class Error:
        unmutable: str = "This Affection can not be added/ edited/ removed!"

    class Help:
        title: str = "Help for ..affection"
        desc: str = """
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

    add: str = "Affection added!"
    edit: str = "Affection edited!"
    remove: str = "Affection removed!"


class Custom:
    class Help:
        title: str = "Help for ..custom"
        desc: str = """
        `..custom create name:<name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
            Creates a new (custom) Unit
        
        `..custom remove name:<name>`
            Removes the Unit (if you are the owner of it)
        
        `..custom edit name:<name> & type:[type] & grade:[grade] & owner:[@Owner] & updated_name:[updated name] & url:[url] & race:[race] & affection:[affection]`
            Changes attributes of the Unit (if you are the owner of it)
        """

    class Add:
        class Error:
            title: str = "Error with ..custom create"
            desc: str = """
            `..custom create name:<name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
            """

    class Edit:
        class Error:
            title: str = "Error with ..custom edit"
            desc: str = """
            `..custom edit name:<name> & criteria:<value1> & criteria2:<value2>`
            
            You **__don't__** need to provide criteria if you don't want to edit it!
            
            **__Criteria__**:
                `type: <type>`
                    The (new) type of the Unit: `red`, `green` or `blue`
                
                `grade: <grade>`
                    The (new) grade of the Unit: `r`, `sr`, `ssr`    
                
                `url: <image url>`
                    The (new) url to the image of the Unit: `any valid url with .png or .jpg`
                
                `race: <race>`
                    The (new) race of the Unit: `demon, giant, human, god, fairy, unknown`
                
                `affection: <affection>`
                    The (new) affection of the Unit: `do ..affection list`
                
                `updated_name: <new name>`
                    The new name of the Unit: `Any Text`
            """

        class Success:
            title: str = "Success"
            desc: str = "Unit successfully edited!"

    class Remove:
        class Error:
            title: str = "Error with ..custom remove"
            desc: str = """
            `..custom remove name:<name>`
            """

        success: str = "Unit successfully removed!"


class Demon:
    class Help:
        title: str = "Help for ..demon"
        desc: str = """
        `..demon offer <reds> <greys> <crimsons>`
            Offers Demons
            If you click "Ok" the offer gets deleted.
                                 
        `..demon code [@Of]`
            Displays the first registered Friendcode of @Of
                                 
        `..demon tag <grand cross friendcode> [name]` to create a profile
            Registers a new profile in the bot, linked to you.
            If you have multiple account please provide the account name after the friendcode
                                 
        `..demon info [@Of]` to show your info
            Shows all Profiles of @Of
        """


class Tourney:
    class Help:
        title: str = "Help for ..tournament"
        desc: str = """
        `..tourney signup <GC Friendcode> <Team CC> <1. Unit> <2. Unit> <3. Unit> <4. Unit>`
            Singup for the Tournament.
            Please provide your Team CC like the following (e.g. `249.5`)
            Please provide the Units with their IDs (use ..find)
        
        `..tourney challenge <@Enemy>`
            Challenges someone registered in the tournament.
            Fails if the enemy has lower CC then you.
            
        `..tourney accept <@Enemy>`
            Accepts a challenge
            
        `..tourney decline <@Enemy>`
            Declines a challenge
        
        `..tourney challengers`
            Shows all your current challengers
            
        `..tourney report <@Winner> <@Looser>`
            Reports the result of your last PvP match
        
        `..tourney top`
            Shows the users with the most won PvP matches
            
        `..tourney stats [@Of]`
            Shows your own / @Of's match history and other useful information
            
        `..tourney cc <new cc>`
            Updates your cc
            
        `..tourney code <new friend code>`
            Updates your friend code
            
        `..tourney team <Unit ID 1> <Unit ID 2> <Unit ID 3> <Unit ID 4>`
            Updates your team
        """
