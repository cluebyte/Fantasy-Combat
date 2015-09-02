import random

edge_list = ["cut", "gash"]
pierce_list = ["piercing", "gutting", "hole", "stab"]
blunt_list = ["crush", "contusion", "bruising"]

class Wound(object):
    """
    Wound object that players will be inflicted with when they receive damage.
    """
    def __init__(self, location, damage, bleed, damage_type, char):
        self.location = location
        self.damage = damage
        self.bleed = bleed
        self.damage_type = damage_type
        self.max_health_char = char.db.max_health * 1.0

    def is_valid(self):
        if self.damage < 1:
            return False
        return True

    def at_bleed_tick(self, divisor):
        """
        Halves bleed by divisor argument. If bleed is less than 2,
        set bleed to 0.
        """
        if self.bleed > 0:
            self.bleed = round(self.bleed / divisor, 0)
        if self.bleed < 2:
            self.bleed = 0

    def __str__(self):
        if self.damage_type == "edge":
            dmg_type = random.choice(edge_list)
        elif self.damage_type == "pierce":
            dmg_type = random.choice(pierce_list)
        elif self.damage_type == "blunt":
            dmg_type = random.choice(blunt_list)
        percentage = self.damage / self.max_health_char
        if percentage > .40:
            wound_str = "mortal"
        elif percentage > .30:
            wound_str = "terrible"
        elif percentage > .20:
            wound_str = "severe"
        elif percentage > .15:
            wound_str = "moderate"
        elif percentage > .10:
            wound_str = "minor"
        elif percentage > 0:
            wound_str = "small"
        if self.bleed > 0:
            bleed_percentage = self.bleed / self.max_health_char
            if bleed_percentage > .40:
                bleed_str = "hemmorrhaging"
            elif bleed_percentage > .30:
                bleed_str = "gushing"
            elif bleed_percentage > .20:
                bleed_str = "splurting"
            elif bleed_percentage > .15:
                bleed_str = "dripping"
            elif bleed_percentage > .10:
                bleed_str = "oozing"
            else:
                bleed_str = "trickling"
            string = "a {R%s{n %s %s on the %s" % (bleed_str, 
                wound_str, dmg_type, self.location)
        else:
            string = "a %s %s on the %s" % (wound_str, dmg_type, self.location)
        return string

    def __repr__(self):
        return self.__str__()

class BloodlossWound(Wound):
    """
    Special kind of bloodloss that doesn't show a visible wound.
    It will bleed out as normal, but binding won't help.
    """
    def __init__(self, bleed, char):
        self.bleed = bleed
        self.max_health_char = char.db.max_health * 1.0

    def is_valid(self):
        if self.bleed < 0:
            return 
        return True

    def __str__(self):
        bleed_percentage = self.bleed / self.max_health_char
        if bleed_percentage > .40:
            bleed_str = "hemmorrhaging"
        elif bleed_percentage > .30:
            bleed_str = "gushing"
        elif bleed_percentage > .20:
            bleed_str = "splurting"
        elif bleed_percentage > .15:
            bleed_str = "dripping"
        elif bleed_percentage > .10:
            bleed_str = "oozing"
        elif bleed_percentage > 0:
            bleed_str = "trickling"
        string = "{R%s{n internal bloodloss" % (bleed_str)
        return string

    def __repr__(self):
        return self.__str__()
