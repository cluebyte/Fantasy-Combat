import move
from game.gamesrc.scripts import status_effects

class Combo(object):
    """
    Combo move holds all the information on what each combo moves
    positional costs are, additional effects, crit bonuses, etc.

    self.name (string) - name of the combo
    self.pos_vict (int) - positional points modifier for the victim of the combo. 
                          Of special note, the modifier for this is in the negative 
                          when we want to take positioning points away from the victim.
                          eg. pos_vict = -2 for a 2 pos penalty for getting hit with the
                          combo
    self.health_vict (int) - health points modifier for the victim of the combo
    self.bleed_vict (int) - bleed points modifier for the victim of the combo
    self.health_att (int) - health points modifier for the performer
    self.pos_att (int) - positional points modifier for the performer
    self.bleed_att (int) - bleed points modifier for the performer
    self.combat_effect(dict) - (key:val, target: val)
                                key (str): key of the status effect
                                target (str): vict, att, both
                                win (boolean): determines if effects are applied only on win
                                (False for either win or lose/null)
    self.pos_cost (int) - positional points cost of performing the combo
    self.crit_bonus (int) - crit chance modifier for performing the combo
    self.dam_multiplier (int) - damage multiplier for performing the combo
    self.legal_moves (list) - a list of all the legal moves that this combo can be performed under
    self.hard_dmg_range (tuple) - a hard damage range for the combo, which 
                                will ignore normal weapon damage
                                ranges. by default this is False.
    self.crit_chance (float) - crit chance increase for the move. This is
                            normally 0.
    self.bleed_multiplier - multiplies the damage to calculate how much bleed
                             is applied on hit
    self.no_pos (boolean) - no positional gain for the turn, only applies on
                             a  win
    self.active_str (string) - string for combat output when the user uses the
                                 combo, in active tense. eg. sounds a
                                barbaric war-cry
    self.suffix_str (string) - string for combat output when the user uses the
                                combo, in "-ing" form, eg. sounding a barbaric
                                war-cry
    self.win_str (string) - when the user wins the exchange, this string is 
                            used for combat output
    """
    def __init__(self):
        self.name = "undefined"
        self.pos_vict = 0
        self.health_vict = 0
        self.bleed_vict = 0
        self.health_att = 0
        self.pos_att = 0
        self.bleed_att = 0
        self.combat_effect = {"effect":
                            {"target": None, "repeats":None, "win":False}}
        self.pos_cost = 0
        self.dam_multiplier = 1.0
        self.legal_moves = []
        self.output_string = ""
        self.hard_dmg_range = False
        self.crit_chance = 0.0
        self.bleed_multiplier = 0.0
        self.no_pos = False
        self.win_str = "null"
        self.active_str = "null"
        self.suffix_str = "null"

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        # trying to see if it's the same on the string level
        if self.name == other.name:
            return True
        return

    def can_move(self, caller):
        """
        checks positional cost of the combo and whether
        the caller has enough positional points.
        """
        if self.pos_cost > caller.ndb.pos:
            msg = "You can't perform %s, you need more positioning!" % \
                    (self.name)
            return msg
        return

    def is_valid(self, move):
        """ 
        arguments: move - (move class)

        sets the conditions of what moves make this combo valid 
        to perform
        """
        if not move:
            return
        for valid_mv in self.legal_moves:
            if valid_mv == move:
                return
        move_list = ""
        for legal_move in self.legal_moves:
            if legal_move != self.legal_moves[-1]:
                move_list += str(legal_move) + ", "
            else:
                move_list += str(legal_move)
        msg = "You can't perform %s with %s. Legal moves are: %s." % \
                (self.name, move.name, move_list)
        return msg

class Dummy(Combo):
    def __init__(self):
        super(Dummy, self).__init__()
        self.name = ""

class Rampage(Combo):
    def __init__(self):
        super(Rampage, self).__init__()
        self.name = "rampage"
        self.health_vict = 4
        self.health_att = 4
        self.pos_cost = 2
        self.active_str = "sounds a barbaric battle-cry"
        self.suffix_str = "Sounding a barbaric battle-cry"
        self.win_str = "strikes $go $bo in a furious rampage"
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Feint(Combo):
    def __init__(self):
        super(Feint, self).__init__()
        self.name = "feint"
        self.health_vict = 1
        self.pos_att = 2
        self.pos_cost = 3
        self.active_str = "executes a fast, faux maneuever"
        self.suffix_str = "With a fast, faux maneuever"
        self.win_str = "delivers a second, powerful strike to $go once $o falls into their trap"
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Cleave(Combo):
    def __init__(self):
        super(Cleave, self).__init__()
        self.name = "cleave"
        self.pos_cost = 3
        self.bleed_multiplier = 0.5
        self.active_str = "attacks with a butcher's grace"
        self.suffix_str = "With a butcher's grace"
        self.win_str = "strikes true, spilling $go blood with a blow " +\
            "to the $bo"
        self.legal_moves = [move.low_cut, move.high_cut]

class Break(Combo):
    def __init__(self):
        super(Break, self).__init__()
        self.name = "break"
        self.pos_vict = 0
        self.pos_cost = 5
        self.health_vict = 4
        self.active_str = "aims to deliver a crushing blow"
        self.suffix_str = "With a crushing blow"
        self.win_str = {
            "success": 
            "crashes their weapon into $go $wo, breaking it in twain",
            "fail": 
            "crashes their weapon into $go $wo, nearly knocking them into the ground"}
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Daze(Combo):
    def __init__(self):
        super(Daze, self).__init__()
        self.name = "daze"
        self.pos_vict = -2
        self.health_vict = 2
        self.pos_cost = 2
        self.active_str = "leverages a brutish strategy"
        self.suffix_str = "Leveraging a brutish strategy"
        self.win_str = "strikes $go $bo, dazing them with the " +\
            "well-executed blow"
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Stun(Combo):
    def __init__(self):
        super(Stun, self).__init__()
        self.name = "stun"
        self.combat_effect = {"key":"stunned",
                                "target":"vict", "repeats":1, "win":True}
        self.active_str = "holds nothing back"
        self.suffix_str = "Holding nothing back"
        self.win_str = "crashes into $go $bo, stunning them with the " + \
                        "might of their fury"
        self.pos_cost = 3
        self.legal_moves = [move.slash, move.riposte]

class Disarm(Combo):
    def __init__(self):
        super(Disarm, self).__init__()
        self.name = "disarm"
        self.combat_effect = {"key": "disarmed",
                                "target":"vict", "repeats": 1, "win":True}
        self.active_str = "shows a staff-master's flare"
        self.suffix_str = "With a staff-master's flare"
        self.win_str = "disarms $go $wo with their perfect parry"
        self.pos_cost = 2
        self.legal_moves = [move.high_parry, move.low_parry]

class Beat(Combo):
    def __init__(self):
        super(Beat, self).__init__()
        self.name = "beat"
        self.combat_effect = {"key":"double damage",
                                "target":"att", "repeats": 1, "win":True}
        self.active_str = "simply turns their wrist"
        self.suffix_str = "With a simple turn of the wrist"
        self.win_str = "beats away $go $wo, putting them out of position"
        self.pos_cost = 2
        self.no_pos = True
        self.legal_moves = [move.high_parry, move.low_parry]

class Impale(Combo):
    def __init__(self):
        super(Impale, self).__init__()
        self.name = "impale"
        self.health_vict = 6
        self.bleed_multiplier = 0.5
        self.pos_cost = 5
        self.active_str = "has blood in their eyes"
        self.suffix_str = "With blood in their eyes"
        self.win_str = "viciously drives their longsword through $go $bo, " + \
            "impaling them"
        self.legal_moves = [move.thrust]

class Skewer(Combo):
    def __init__(self):
        super(Skewer, self).__init__()
        self.name = "skewer"
        self.combat_effect = {"off-balance":
                            {"target": "vict", "repeats":2, "win": True}}
        self.bleed_multiplier = 1.0
        self.pos_cost = 5
        self.active_str = "charges bravely"
        self.suffix_str = "Charging bravely"
        self.win_str = "wickedly drives their spear through $go $bo, " + \
                        "skewering them"

class Trip(Combo):
    def __init__(self):
        super(Trip, self).__init__()
        self.name = "trip"
        self.pos_cost = 3
        self.combat_effect = {"stumbled":
                                {"target":"vict", "repeats": 1, "win": True}}
        self.active_str = "moves trepidatiously"
        self.suffix_str = "Trepidatiously"
        self.win_str = "protects themselves long enough to use their " + \
                        "spear's shaft to trip up $go $bo, " + \
                        "causing them to stumble"   

class Clash(Combo):
    def __init__(self):
        super(Clash, self).__init__()
        self.name = "clash"
        self.pos_vict = -2
        self.pos_att = 2
        self.pos_cost = 2
        self.active_str = "makes use of their greatsword's weight"
        self.suffix_str = "Making use of the weight of their greatsword"
        self.win_str = "knocks the attack well wide with superior force"
        self.legal_moves = [move.high_parry, move.low_parry]

class Stagger(Combo):
    def __init__(self):
        super(Stagger, self).__init__()
        self.name = "stagger"
        self.pos_cost = 5
        self.active_str = "shows their staggering strength"
        self.suffix_str = "With staggering strength"
        self.win_str = "delivers a bold blow that brutally " + \
            "bashes $go in their $bo"
        self.combat_effect = {"off-balance": 
                            {"target":"vict", "repeats": 1, "win": True},
                            "double damage": 
                            {"target": "att", "repeats": 1, "win": True},
                            "dazed":
                            {"target":"vict", "repeats": 1, "win": True}}
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Rage(Combo):
    def __init__(self):
        super(Rage, self).__init__()
        self.name = "rage"
        self.pos_cost = 5
        self.active_str = "unleashes an ear-shattering cry"
        self.suffix_str = "With an ear-shattering cry"
        self.win_str = "twists their face into an ugly mask, " + \
            "the veins in their forehead swelling with wrath"
        self.combat_effect = {"butcher's edge": 
                            {"target": "att", "repeats":3, "win": True}}
        self.legal_moves = [move.low_parry, move.high_parry, move.dodge, 
                            move.disengage, move.duck]

class Smash(Combo):
    def __init__(self):
        super(Smash, self).__init__()
        self.name = "smash"
        self.combat_effect = {"key":"off-balance",
                                "target":"att", "repeats": 3, "win":True}
        self.pos_cost = 3
        self.dam_multiplier = 2.0
        self.active_str = "strikes with unyielding power"
        self.suffix_str = "With unyielding power"
        self.win_str = "smashes their greatsword into $go $bo with " +\
                        "barbaric strength"
        self.legal_moves = [move.thrust, move.high_cut,
                            move.low_cut, move.slash, move.riposte]

class Sweep(Combo):
    def __init__(self):
        super(Sweep, self).__init__()
        self.name = "sweep"
        self.pos_vict = -2
        self.combat_effect = {"key":"knocked down",
                                "target":"vict", "repeats": 1, "win":True}
        self.pos_cost = 3
        self.active_str = "strikes baitingly"
        self.suffix_str = "With a baiting blow"
        self.win_str = "first strikes $go $bo, then spins their $ws low " + \
            "to sweep their feet out from underneath them"
        self.legal_moves = [move.thrust, move.high_cut, 
                            move.low_cut, move.slash, move.riposte]

class Flurry(Combo):
    def __init__(self):
        super(Flurry, self).__init__()
        self.name = "flurry"
        self.health_vict = 6
        self.pos_cost = 5
        self.combat_effect = {"key":"off-balance",
                                "target":"vict", "repeats": 2, "win":True}
        self.effect_repeats = 2
        self.active_str = "attacks repeatedly"
        self.suffix_str = "Again and again"
        self.win_str = "breaks through $go guard and lands a ruthless " +\
            "blow to their $bo"
        self.legal_moves = [move.thrust, move.high_cut, 
                            move.low_cut, move.slash, move.riposte]

class Counter(Combo):
    def __init__(self):
        super(Counter, self).__init__()
        self.name = "counter"
        self.pos_att = 2
        self.combat_effect = {"key":"weakened",
                                "target":"vict", "repeats": 1, "win":True}
        self.pos_cost = 2
        self.active_str = "spins their spear with two deft motions"
        self.suffix_str = "With two deft motions"
        self.win_str = "beats $go attack and counter-thrusts hard " +\
            "into their $bo"
        self.legal_moves = [move.riposte]

class Circle(Combo):
    def __init__(self):
        super(Circle, self).__init__()
        self.name = "circle"
        self.pos_att = 2
        self.pos_cost = 2
        self.active_str = "steps nimbly"
        self.suffix_str = "With nimble footwork"
        self.win_str = "manages to circle behind $po"
        self.combat_effect = {"key":"prepared",
                                "target":"att", "repeats": 1, "win":True}
        self.legal_moves = [move.dodge]

class Twist(Combo):
    def __init__(self):
        super(Twist, self).__init__()
        self.name = "twist"
        self.pos_cost = 3
        self.bleed_multiplier = 0.5
        self.active_str = "stabs viciously"
        self.suffix_str = "With a vicious stab"
        self.win_str = "drives their dagger into $go $bo and mercilessly " + \
            "twists the blade"
        self.legal_moves = [move.thrust]

class Backstab(Combo):
    def __init__(self):
        super(Backstab, self).__init__()
        self.name = "backstab"
        self.pos_att = 0
        self.pos_cost = 5
        self.active_str = "takes a precise step"
        self.suffix_str = "With a calculating step"
        self.win_str = "drives their dagger into $go $bo from behind, " + \
            "blindsiding $po with the backstab"
        self.legal_moves = [move.dodge, move.duck]
        self.hard_dmg_range = {"min":8, "max":24}
        self.no_pos = True

class ShieldBash(Combo):
    def __init__(self):
        super(ShieldBash, self).__init__()
        self.name = "shield bash"
        self.combat_effect = {"key":"knocked down",
                                "target":"vict", "repeats":2, "win":True}
        self.pos_cost = 2
        self.pos_vict = -2
        self.active_str = "pulls their weight behind their shield"
        self.suffix_str = "Pulling their weight behind their shield"
        self.win_str = "drives forward with their shield, deflecting " +\
            " $go attack and crashing into $po full force"
        self.legal_moves = [move.high_parry, move.low_parry]

# each weapon gets their own instance of the combo
rampage = Rampage()
cleave = Cleave()
break_combo = Break()
daze = Daze()
stun = Stun()
disarm = Disarm()
feint = Feint()
ls_impale = Impale()
skewer = Skewer()


clash = Clash()
smash = Smash()
sweep = Sweep()
flurry = Flurry()
circle = Circle()
twist = Twist()
backstab = Backstab()
counter = Counter()
shield_bash = ShieldBash()
beat = Beat()
stagger = Stagger()
rage = Rage()

longsword_combos = [feint, beat, ls_impale]
axe_combos = [rampage, cleave, rage]
mace_combos = [daze, stun, break_combo]
greatsword_combos = [clash, smash, stagger]
stave_combos = [disarm, sweep, flurry]
dagger_combos = [circle, twist, backstab]
spear_combos = [counter, sweep, skewer]
shield_combos = [shield_bash]

tech_list = [longsword_combos, axe_combos, mace_combos, greatsword_combos,
            stave_combos, dagger_combos, spear_combos, shield_combos]