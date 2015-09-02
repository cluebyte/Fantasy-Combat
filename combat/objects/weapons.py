from game.gamesrc.scripts import traits
from game.gamesrc.combat import move
from game.gamesrc.objects.object import Object

QUALITY_DICT = {1: "poor", 2: "ordinary", 3: "good", 4: "master"}

class Weapon(Object):
    """
    This is the base weapon object.

    There are seven total weapon types in the FRPI Engine.

    1) Axes
    2) Maces
    3) Longswords
    4) Greatswords
    5) Staves
    6) Daggers
    7) Spears

    All weapons in the game will inherit from these seven types.
    Each weapon has its own unique combo abilities as well as strengths
    and weaknesses. These will be defined in the combat mechancis system,
    with their own unique command sets.

    By default, every weapon should have:
        damage (tuple range) - range that the weapon can hit in raw damage
        damage_bonus (int) - damage bonus amount, goes up with quality. 
            poor has no bonus.
        size (int) - weapon size, smallest is 1, biggest is 4.
        hands (int) - how many hands it takes to wield this weapon. 
                      1 is one handed, 2 is two handed, 3 is either one or 
                      two-handed.
        status_effects (list of strings) - list of status effect script keys
                                        that this weapon applies at_wield.
        skill_affects (dictionary) - dictionary of skill_affects that this
                                        weapon applies at_wield.
        pos_mods (dictionary) - dictionary such as val:(move1, move2), 
                                eg. val:("high parry", "low parry"), 
                                1:("dodge", "duck", "disengage", 
                                    "high parry", "low parry")

    """

    def at_object_creation(self):
        # default poor quality
        self.db.quality = 1
        # status effects when this weapon is wielded
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default desc.
        self.db.desc = "This is a basic weapon prototype. This should NOT be loaded! It's a superclass."
        # Prototype weapon damage range. 1-2 is default
        self.db.damage = (1, 2)
        # Bonus damage
        self.db.damage_bonus = self.db.quality - 1
        # Default hands value. Valid values should be:
        # 1 = one handed only
        # 2 = two handed only
        # 3 = can be gripped in one hand or two
        self.db.hands = 1
        self.db.status_effects = None
        # skill affects when this weapon is wielded
        self.db.skill_affects = None
        # trait that the player must have to make use of this weapon
        # to its full potential.
        self.db.trait = None
        # positional mods that this weapon has. 
        self.db.pos_mods = {0: "all"}
        # default damage type
        self.db.dmg_type = None
        # if this weapon can be dual-wielded, it will give the hand that it can be dual wielded in
        # such as 'main' or 'both'
        self.db.dual_wield = False
        self.db.broken = False
        self.db.weapon_type = "null"
        self.db.crit_chance = 0.20
        self.db.move_wrapper = move.CLASSIC_WRAPPER

    def break_weapon(self):
        """
        sets the weapon to being broken
        """
        self.db.broken = True
        self.db.old_damage = self.db.damage
        self.db.damage = (1, 3)

    def repair_weapon(self):
        """
        sets the weapon to being repaired
        """
        self.db.broken = False
        self.db.damage = self.db.old_damage
        del self.db.old_damage

    def at_wield(self, char):
        """
        Hook for when the weapon is wielded.
        Useful for adding command sets.
        """
        pass
    def at_remove(self, char):
        """
        Hook for when the weapon is wielded.
        Useful for adding command sets.
        """
        pass

class Fists(Weapon):
    """
    Placeholder weapon for when players aren't using anything to defend themselves.
    """
    def at_object_creation(self):
        super(Fists, self).at_object_creation()
        self.db.sdesc = "rockin' hard fists"
        self.db.ldesc = "Bruce Lee kinda fists are here."
        self.db.damage = (1, 3)
        self.db.weapon_type = "fists"
        self.db.hands = 2
        self.db.dmg_type = "blunt"

class Longsword(Weapon):
    """
    Base sword object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Longsword, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default sword desc
        self.db.desc = "This is a basic longsword object " +\
            "inherited from weapon."
        # Default sword damage
        self.db.damage = (4, 7)
        # hands value
        self.db.hands = 1
        self.db.dmg_type = "edge"
        self.db.damage_bonus = self.db.quality - 1
        self.db.trait = "LongswordTrait"
        self.db.weapon_type = "longsword"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetLongsword")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetLongsword")
    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a beat, feint, and impale with this weapon. " +\
            "See 'help longsword techniques' for more information."
        return eval_str


class Greatsword(Weapon):
    """
    Base greatsword object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Greatsword, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default sword desc
        self.db.desc = "This is a basic greatsword object inherited from weapon."
        # Default sword damage
        self.db.damage = (4, 11)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 2
        self.db.dmg_type = "edge"
        self.db.trait = "GreatswordTrait"
        self.db.pos_mods = {-1:[move.high_parry, move.low_parry]}
        self.db.crit_chance = 0.25
        self.db.weapon_type = "greatsword"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetGreatsword")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetGreatsword")

    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a clash, smash, and break with this weapon. " +\
            "See 'help greatsword techniques' for more information. " + \
            "Inherently, this weapon has a -1 pos mod for low/high parry wins."
        return eval_str

class Axe(Weapon):
    """
    Base axe object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Axe, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default axe desc
        self.db.desc = "This is an axe object inherited from weapon."
        # Default axe damage
        self.db.damage_bonus = self.db.quality - 1
        self.db.damage = (4, 7)
        # hands value
        self.db.hands = 1
        self.db.dmg_type = "edge"
        self.db.dual_wield = "main"
        self.db.trait = "AxeTrait"
        self.db.weapon_type = "axe"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetAxe")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetAxe")

    def at_eval(self):
        eval_str = "This is an %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a rampage, cleave, and break with this weapon." +\
            " See 'help axe techniques' for more information."
        return eval_str

class Battleaxe(Axe):
    """
    Base axe object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Axe, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default axe desc
        self.db.desc = "This is an axe object inherited from weapon."
        # Default axe damage
        self.db.damage_bonus = self.db.quality - 1
        self.db.damage = (4, 11)
        # hands value
        self.db.hands = 2
        self.db.dmg_type = "edge"
        self.db.dual_wield = "main"
        self.db.trait = "AxeTrait"
        self.db.pos_mods = {-8:
            [move.high_parry, move.low_parry, move.disengage]}
        self.db.crit_chance = 0.25
        self.db.weapon_type = "battleaxe"

    def at_eval(self):
        eval_str = "This is an %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a rampage, cleave, and break with this weapon." +\
            " See 'help axe techniques' for more information. " + \
            "Inherently, this weapon gains no positioning on high/low " + \
            "parry or disengage wins."
        return eval_str

class Mace(Weapon):
    """
    Base mace object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Mace, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default mace desc
        self.db.desc = "This is a basic mace object inherited from weapon."
        # Default mace damage
        self.db.damage = (4, 7)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 1
        self.db.dmg_type = "blunt"
        self.db.dual_wield = "main"
        self.db.trait = "MaceTrait"
        self.db.weapon_type = "mace"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetMace")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetMace")

    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a daze, stun, and break with this weapon. " +\
            "See 'help mace techniques' for more information."
        return eval_str

class Warhammer(Mace):
    """
    Warhammer weapon, inherited from mace.
    """
    def at_object_creation(self):
        super(Warhammer, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default mace desc
        self.db.desc = "This is a basic mace object inherited from weapon."
        # Default mace damage
        self.db.damage = (4, 11)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 2
        self.db.dmg_type = "blunt"
        self.db.dual_wield = False
        self.db.pos_mods = {-1:[move.high_parry, move.low_parry]}
        self.db.trait = "MaceTrait"
        self.db.crit_chance = 0.25
        self.db.weapon_type = "warhammer"
        
    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a daze, stun, and break with this weapon. " +\
            "See 'help mace techniques' for more information. " +\
            "Inherently this weapon has a -1 positioning mod for all " +\
            "parries."
        return eval_str


class Stave(Weapon):
    """
    Base stave object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Stave, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default stave desc
        self.db.desc = "This is a basic stave object inherited from weapon."
        # Default stave damage
        self.db.damage = (4, 9)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 2
        self.db.dmg_type = "blunt"
        self.db.trait = "StaveTrait"
        self.db.pos_mods = {1:[move.high_parry, move.low_parry]}
        self.db.crit_chance = 0.25
        self.db.weapon_type = "stave"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetStave")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetStave")

    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a disarm, sweep, or flurry with this weapon. " +\
            "See 'help stave techniques' for more information. " +\
            "Inherently, this weapon has a +1 pos mod to high/low parry wins."
        return eval_str

class Dagger(Weapon):
    """
    Base dagger object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Dagger, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default dagger desc
        self.db.desc = "This is a basic dagger object inherited from weapon."
        # Default dagger damage
        self.db.damage = (3, 6)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 1
        self.db.dmg_type = "pierce"
        self.db.dual_wield = "both"
        self.db.trait = "DaggerTrait"
        self.db.pos_mods = {1:[move.dodge, move.duck]}
        self.db.weapon_type = "dagger"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetDagger")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetDagger")

    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a circle, twist, or backstab with this weapon." +\
            " See 'help dagger techniques' for more information. " +\
            "Inherently, this weapon has +1 pos mod to dodge/duck " +\
            "wins."
        return eval_str

class Spear(Weapon):
    """
    Base spear object, inherited from weapon.
    """
    def at_object_creation(self):
        super(Spear, self).at_object_creation()
        # default sdesc
        self.db.sdesc = "a basic weapon prototype"
        #default ldesc
        self.db.ldesc = "A basic weapon prototype is here."
        # Default spear desc
        self.db.desc = "This is a basic spear object inherited from weapon."
        # Default spear damage
        self.db.damage = (4, 7)
        self.db.damage_bonus = self.db.quality - 1
        # hands value
        self.db.hands = 1
        self.db.dmg_type = "pierce"
        self.db.trait = "SpearTrait"
        self.db.pos_mods = {-1:[move.high_parry, move.low_parry]}
        self.db.weapon_type = "spear"

    def at_wield(self, char):
        char.cmdset.add("CmdSetCombat.CmdSetSpear")

    def at_remove(self, char):
        char.cmdset.delete("CmdSetSpear")

    def at_eval(self):
        eval_str = "This is a %s type weapon. " % (self.db.weapon_type) + \
            " You estimate it'd do " +\
            "about %i to %i " % (self.db.damage[0], self.db.damage[1]) + \
            "damage on average. " + \
            "It's of %s quality. " % (QUALITY_DICT[self.db.quality]) + \
            "You can perform a counter, sweep, or impale with this weapon. " +\
            "See 'help spear techniques' for more information. " +\
            "Inherently, this weapon has a -1 pos mod to high/low parry wins."
        return eval_str

class LongSpear(Spear):
    def at_object_creation(self):
        super(LongSpear, self).at_object_creation()
        self.db.sdesc = "a basic longspear prototype"
        self.db.ldesc = "A basic longspear prototype is here."
        self.db.ldesc = "This is a basic long spear inherited from weapon."
        self.db.hands = 2
        self.db.damage = (4, 11)
        self.db.crit_chance = 0.25
        self.db.weapon_type = "longspear"