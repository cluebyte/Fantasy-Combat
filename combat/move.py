from ev import logger

# This is the module that contains all of the combat move objects in the game. 
# There should only need to be one move set in existence that the game uses
# which is reflected in the variable CLASSIC_MATRIX. But perhaps later with
# magic and archery, we'll have more moves players can do. 

class Move(object):
    """
    Each move has the following attributes:

    self.name (string) - name of the move
    self.lose_list (list) - list of moves the move loses against
    self.null_list (list) - list of moves the move is null against
    self.win_list (list) - list of mvoes the move wins against
    self.move_type (string) -  what kind of move is it? defensive or offensive?
    """
    def __init__(self, name, aliases):
        self.name = name
        self.lose_list = []
        self.win_list = []
        self.null_list = []
        self.aliases = aliases
        self.move_type = "null"
        self.bonus_pos = 0
        self.bonus_dmg = 0
        self.bonus_ble = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not other:
            return
        return self.name == other.name

    def is_valid(self, caller):
        # need to search all scripts on the player that is a status effect and sees if it's on the ban list
        # if it is, can't perform the move. If you can't perform the move, it returns a string. If you can,
        # it returns None.
        scripts = caller.scripts.all()
        if not scripts:
            return
        for script in scripts:
            if script.db.no_combat_moves:
                if script.db.no_combat_moves != True and self in script.db.no_combat_moves:
                    msg = "You can't perform this move because of the %s effect." % (script.key)
                    return msg
                elif script.db.no_combat_moves == True:
                    msg = "You can't perform this move because of the %s effect." % (script.key)
                    return msg
        return

class MoveWrapper(object):
    """
    This is a wrapper that changes the aesthetic strings of a move.

    The following are its attributes:

    move_name (class Move) - the hard-coded move name this is supposed to be
                        a wrapper for
    suffix_str (string) - the "-ing" form of the string, eg. swinging high
    active_str (string) - the active tense form of the string eg. swings high
    win_str (dict) - in the form of 
                    {"default": "lands a blow to $go $bo", 
                    "thrust": "knocks aside the attack"}
    null_str (dict) - in the form of above:
                    {"default": "but neither fighter seems to gain any ground 
                    against the other",
                     "high cut": "But both fighters clash high"}
    Notes about symbols:
    $o - opponent's sdesc
    $go - opponent's gender
    $s - self sdesc
    $gs - self's gender
    $ws - self's weapon 
    $wo - opponent's weapon
    $bo - opponent's body part
    $bs - self's body part
    """
    def __init__(self, move_name):
        self.move_name = move_name
        self.suffix_str = "nulling"
        self.active_str = "null"
        self.null_str = {"default": "but, neither fighter seems to gain " + \
            "any ground against the other" }
        self.win_str = {"default": "lands a blow to $go $bo"}

    def find_win_move(self, move_name):
        """
        Find the move argument and see if it matches any strings we have for
        win_str. If no matches are found, we return the default.
        """
        for (win_move_str, win_string) in self.win_str.items():
            if move_name.name == win_move_str:
                return win_string
        return self.win_str["default"]

    def find_null_move(self, move_name):
        """
        Find the move argument in null_str. If it doesn't exist, we return
        the default of self.null_str. If a match is found, we return the string
        of that instead.
        """
        for (null_move_str, null_string) in self.null_str.items():
            if move_name.name == null_move_str:
                return null_string
        return self.null_str["default"]

    def __str__(self):
        return self.move_name
        
#############################################
# MOVE INIT SECTION
#############################################
thrust = Move("thrust", ["th"])
high_cut = Move("high cut", ["hc"])
low_cut = Move("low cut", ["lc"]) 
slash = Move("slash", ["sl"]) 
riposte = Move("riposte", ["ri"]) 
dodge = Move("dodge", ["do"]) 
high_parry = Move("high parry", ["hp"]) 
low_parry = Move("low parry", ["lp"]) 
duck = Move("duck", ["du"]) 
disengage = Move("disengage", ["di"])
pass_turn = Move("pass", [])

thrust.win_list = [thrust, high_cut, low_cut, slash, duck, pass_turn]
thrust.lose_list = [riposte, dodge, high_parry, low_parry, disengage]
thrust.move_type = "offensive"

high_cut.win_list = [low_cut, slash, riposte, dodge, low_parry, disengage, pass_turn]
high_cut.lose_list = [thrust, high_parry, duck]
high_cut.null_list = [high_cut]
high_cut.move_type = "offensive"

low_cut.win_list = [high_cut, slash, riposte, dodge, high_parry, duck, disengage, pass_turn]
low_cut.lose_list = [thrust, low_parry]
low_cut.null_list = [low_cut]
low_cut.move_type = "offensive"

slash.win_list = [high_parry, low_parry, duck, slash, pass_turn]
slash.lose_list = [thrust, high_cut, low_cut, riposte, dodge]
slash.null_list = [disengage]
slash.bonus_dmg = 4
slash.move_type = "offensive"

riposte.win_list = [thrust, slash, pass_turn]
riposte.lose_list = [high_cut, low_cut]
riposte_null_list = [riposte, dodge, high_parry, low_parry, duck, disengage]
riposte.move_type = "offensive"

dodge.win_list = [thrust, slash, high_parry, low_parry, pass_turn]
dodge.lose_list = [high_cut, low_cut]
dodge.null_list = [riposte, dodge, duck, disengage]
dodge.move_type = "defensive"

high_parry.win_list = [thrust, high_cut, pass_turn]
high_parry.lose_list = [low_cut, slash, dodge, duck]
high_parry.null_list = [high_parry, low_parry, riposte, disengage]
high_parry.move_type = "defensive"

low_parry.win_list = [thrust, low_cut, pass_turn]
low_parry.lose_list = [high_cut, slash, dodge, duck]
low_parry.null_list = [riposte, high_parry, low_parry, disengage]
low_parry.move_type = "defensive"

duck.win_list = [high_cut, high_parry, low_parry, pass_turn]
duck.lose_list = [thrust, low_cut, slash]
duck.null_list = [riposte, dodge, duck, disengage]
duck.move_type = "defensive"

disengage.win_list = [thrust, pass_turn]
disengage.lose_list = [high_cut, low_cut]
disengage.null_list = [slash, riposte, dodge, high_parry, low_parry, duck, disengage]
disengage.move_type = "defensive"
disengage.bonus_pos = 2

pass_turn.lose_list = [thrust, high_cut, low_cut, slash, riposte, dodge, high_parry, low_parry, duck, disengage]
pass_turn.null_list = [pass_turn]
pass_turn.move_type = "defensive"

# Hold onto our classic combat matrix in a list.
CLASSIC_MATRIX = [thrust, high_cut, low_cut, slash, riposte, dodge,
                high_parry, low_parry, duck, disengage]
##############################################
# DEFAULT WRAPPER
##############################################

thrust_wrapper = MoveWrapper(thrust)
high_cut_wrapper = MoveWrapper(high_cut)
low_cut_wrapper = MoveWrapper(low_cut)
slash_wrapper = MoveWrapper(slash)
riposte_wrapper = MoveWrapper(riposte)
dodge_wrapper = MoveWrapper(dodge)
high_parry_wrapper = MoveWrapper(high_parry)
low_parry_wrapper = MoveWrapper(low_parry)
duck_wrapper = MoveWrapper(duck)
disengage_wrapper = MoveWrapper(disengage)
pass_wrapper = MoveWrapper(pass_turn)

thrust_wrapper.suffix_str = "lunging forward"
thrust_wrapper.active_str = "lunges forward"

high_cut_wrapper.suffix_str = "swinging high"
high_cut_wrapper.active_str = "swings high"
high_cut_wrapper.win_str = {"default": "lands a blow to $go $bo"}
high_cut_wrapper.null_str = {
    "default": "but, neither fighter seems to gain any ground " + \
    "against the other",
    "high cut": "but, both fighters clash high, their weapons ringing " + \
    "soundly when they meet."}

low_cut_wrapper.suffix_str = "swinging low"
low_cut_wrapper.active_str = "swings low"
low_cut_wrapper.null_str = {
    "default": "but, neither fighter seems to gain any ground " + \
    "against the other",
    "low cut": "but, both fighters clash low, their weapons ringing " + \
    "soundly when they meet."}

slash_wrapper.suffix_str = "wildly slashing"
slash_wrapper.active_str = "wildly slashes"
slash_wrapper.win_str = {"default": "lands a mighty blow to $go $bo"}

riposte_wrapper.suffix_str = "preparing for a counter-attack"
riposte_wrapper.active_str = "prepares for a counter-attack"
riposte_wrapper.win_str = {
    "default": "parries and counters with a blow to $go $bo"}

dodge_wrapper.suffix_str = "dodging aside"
dodge_wrapper.active_str = "dodges aside"
dodge_wrapper.win_str = {
    "default": "manages to avoid the attack",
    "high parry": "manages to slip behind $go guard",
    "low parry": "manages to slip behind $go guard"}

high_parry_wrapper.suffix_str = "blocking high"
high_parry_wrapper.active_str = "blocks high"
high_parry_wrapper.win_str = {"default": "knocks aside the attack"}

low_parry_wrapper.suffix_str = "blocking low"
low_parry_wrapper.active_str = "blocks low"
low_parry_wrapper.win_str = {"default": "knocks aside the attack"}

duck_wrapper.suffix_str = "dropping low"
duck_wrapper.active_str = "drops low"
duck_wrapper.win_str = {
    "default": "manages to duck beneath the attack",
    "high parry": "manages to duck beneath $go guard",
    "low parry": "manages to duck beneath $go guard"}

disengage_wrapper.suffix_str = "rolling their wrist to disengage"
disengage_wrapper.active_str = "rolls their wrist to disengage"
disengage_wrapper.win_str =  {
    "default": "nimbly flicks away $go attack"}

pass_wrapper.suffix_str = "doing little of note"
pass_wrapper.active_str = "does little of note"
pass_wrapper.null_str = {
    "default": "but, neither fighter seems to gain " + \
            "any ground against the other",
    "pass": "and there is a lull in the battle"}

# this is the default aesthetics wrapper for melee matrix moves
CLASSIC_WRAPPER = [thrust_wrapper, high_cut_wrapper, low_cut_wrapper,
                    slash_wrapper, riposte_wrapper, dodge_wrapper,
                    high_parry_wrapper, low_parry_wrapper, duck_wrapper,
                    disengage_wrapper, pass_wrapper]

#################################################################
# BARE HANDED WRAPPER
#################################################################
high_cut_bare_wrapper = MoveWrapper(high_cut)
high_cut_bare_wrapper.suffix_str = "swinging high"
high_cut_bare_wrapper.active_str = "swings high"
high_cut_bare_wrapper.null_str = {
    "default": "but, neither fighter seems to gain any ground " + \
    "against the other",
    "high cut": "but, both fighters strike high, and neither " + \
    "gains any advantage"}

# if our fool doesn't have a weapon, we use this instead
BAREHANDED_WRAPPER = [thrust_wrapper, high_cut_bare_wrapper, low_cut_wrapper,
                    slash_wrapper, riposte_wrapper, dodge_wrapper,
                    high_parry_wrapper, low_parry_wrapper, duck_wrapper,
                    disengage_wrapper, pass_wrapper]