"""

Template for Characters

Copy this module up one level and name it as you like, then
use it as a template to create your own Character class.

To make new logins default to creating characters
of your new type, change settings.BASE_CHARACTER_TYPECLASS to point to
your new class, e.g.

settings.BASE_CHARACTER_TYPECLASS = "game.gamesrc.objects.mychar.MyChar"

Note that objects already created in the database will not notice
this change, you have to convert them manually e.g. with the
@typeclass command.

"""
from ev import Character as DefaultCharacter
from game.gamesrc.world import body
from ev import logger
from ev import tickerhandler
from game.gamesrc.combat import wounds
from ev import create_script
from src.utils import utils, evtable
import re
from game.gamesrc.combat import move

MAX_HEALTH = 80
MAX_BLEED = MAX_HEALTH

class Character(DefaultCharacter):
    """
    The Character is like any normal Object (see example/object.py for
    a list of properties and methods), except it actually implements
    some of its hook methods to do some work:

    at_basetype_setup - always assigns the default_cmdset to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(player) -  when Player disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before Player re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room

    """

    def at_object_creation(self):
        """
        Called only at initial creation. 

        * Static health/stamina because there's no such things as stats/skills.

        * Ch_state refers to what state they exist in on the game.
        0 = dead
        1 = alive
        2 = suspended

        * Boolean approved value refers to whether they've been approved for play.
        Default value is False.

        """
        ####################################################################
        # Stats
        ####################################################################
        self.db.state = 1 # 1 is alive, 2 is unconscious, 3 is dead
        self.db.max_health = MAX_HEALTH
        self.db.health = MAX_HEALTH
        self.db.max_bleed = self.db.max_health
        self.db.move_wrapper = move.BAREHANDED_WRAPPER
        # Current weight of items held
        self.db.curr_weight = 0
        # Encumbrance limit
        self.db.max_weight = 300
        # wielding
        self.db.wielding = {"main": None, "off": None}
        self.db.holding = []
        self.db.holding_capacity = 2
        # wounds
        self.db.wounds = []
        # character approved status - default is not approved
        self.db.ch_approved = False
        # sdesc/ldesc/keywords
        self.db.sdesc = "an entity"
        self.db.ldesc = "An entity is here, not formed into being yet."
        self.db.race = "Raceless"
        # Body holds information to what wearlocs are available to the character
        self.db.settings = {"stance": "balanced"}
        # and information about what could be worn over what (layered clothing)
        self.db.body = body.human_body
        # Initiate what they're wearing, which should be nothing.
        self.db.equipped = {}
        self.db.sex = "sexless"
        self.db.default_weapon = {
                                "name": "fists",
                                "min": 1, 
                                "max": 3,
                                "type": "blunt",
                                "dmg_bonus": 0,
                                "crit": 0.0,
                                "hands": 1,
                                "quality": 1}
        for part in self.db.body:
            self.db.equipped[part.name] = {}
            if part.armor:
                self.db.equipped[part.name]["armor"] = None
            if part.clothing:
                self.db.equipped[part.name]["clothing"] = None

    def aliasify(self):
        """
        This is used to generate a list of aliases based on our key.
        This is particularly useful for objects that we need to generate
        aliases or 'keywords' for so we can reference them.
        """
        # generate a list of keywords for our alias
        pre_aliases = self.db.sdesc.split(" ")
        old_aliases = self.aliases.all()
        new_aliases = [alias.strip().lower() for alias in pre_aliases
                       if alias.strip() and not 
                       re.match("(\b[aA][n]|\b[tT]he|^[aA]$)", alias)]
        old_aliases.extend(new_aliases)
        aliases = list(set(old_aliases))
        self.aliases.add(aliases)

    def announce_move_from(self, destination):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.

        destination - the place we are going to.
        """
        if not self.location:
            return
        name = self.name
        loc_name = ""
        loc_name = self.location.name
        dest_name = destination.name
        string = "\n%s is leaving %s, heading for %s.\n"
        self.location.msg_contents(string % (name, loc_name, dest_name), exclude=self)

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this
        point we are standing in the new location.

        source_location - the place we came from
        """

        name = self.name
        if not source_location and self.location.has_player:
            # This was created from nowhere and added to a player's
            # inventory; it's probably the result of a create command.
            string = "You now have %s in your possession." % name
            self.location.msg(string)
            return

        src_name = "nowhere"
        loc_name = self.location.name
        if source_location:
            src_name = source_location.name
        string = "\n%s arrives to %s from %s.\n"
        self.location.msg_contents(string % (name, loc_name, src_name), exclude=self)
    #def msg(self, text=None, from_obj=None, sessid=0, pers=False, 
    #        **kwargs):
        """
        Overloaded msg method that properly capitalizes all the messages
        the character gets. It makes sure that if there's a color code,
        it properly capitalizes it anyways.
        """
        """
        if pers:
            # to do, replacing any mentions of sdescs with you/yours
            # and also replacing any mentions of his/her/its with your
            # if it follows the sdesc.
            
            # replaces any mentions of sdesc's with your
            text = text.replace("{M" + self.db.sdesc + "{n's", "your")
            # replaces any mentions of sdesc with you
            text = text.replace("{M" + self.db.sdesc + "{n", "you")
            split_str = text.split(" ")
            indices = []
            for x in range(len(split_str)):
                match = re.match("(you[rs]*)", split_str[x])
                if match:
                    indices.append(x)
            for index in indices:
                if index == 0:
                    split_str[index] = "{M%s{n" % \
                        (split_str[index].capitalize())
                elif split_str[index] == split_str[-1]:
                    split_str[index] = "{M%s{n" % \
                        (split_str[index])
                else:
                    try:
                        prev_ind = index - 1
                        if split_str[prev_ind][-1] in "s" and \
                            "ss" not in split_str[prev_ind][-2:]:
                            split_str[prev_ind] = split_str[prev_ind][0:-1]
                    except:
                        pass
            text = " ".join(split_str)

            rtn = re.split('([.!?] *)', text)

            for x in range(len(rtn)):
                if rtn[x].startswith("{") and len(rtn[x]) > 3:
                    rtn[x] = rtn[x][0:1] + rtn[x][2].capitalize() + rtn[x][3:]
                elif len(rtn[x]) > 1:
                    rtn[x] = rtn[x][0].capitalize() + rtn[x][1:]
                else:
                    rtn[x] = rtn[x].capitalize()
            if rtn:
                text = "".join(rtn)
            """
        #self.dbobj.msg(text=text, from_obj=from_obj, sessid=sessid, **kwargs)

    def return_appearance(self, pobject):
        string = ""
        if not pobject:
            return
        # get and identify all objects
        visible = (con for con in self.contents 
                    if con != pobject and con.access(pobject, "view"))
        exits, users, things = [], [], []
        for con in visible:
            key = con.key
            if con.destination:
                exits.append(key)
            elif con.has_player:
                if con.ndb.combat_handler:
                    vict_sdesc = con.ndb.combat_handler.pairs[con].db.sdesc
                    users.append("{M%s{n is currently {Rfighting{n {M%s{n!" % (con.db.sdesc.capitalize(), vict_sdesc)) 
                else:
                    users.append(" {M%s{n" % (con.db.sdesc))
        # get description, build string
        desc = self.db.desc
        char_wounds = [char_wound for char_wound in self.db.wounds if
            isinstance(char_wound, wounds.Wound)]
        if desc:
            string += "%s\n" % desc
        if char_wounds:
            string += "\n{M%s{n suffers from the following wounds: " % (self.db.sdesc.capitalize())
            wound_str = ""
            for char_wound in char_wounds:
                if not char_wounds[-1] == char_wound:
                    wound_str += str(char_wound) + ", "
                else:
                    wound_str += str(char_wound) + "."
            string += wound_str + "\n"
        if exits:
            string += "\n{wExits:{n " + ", ".join(exits) + "\n"
        if self.db.holding:
            h_table = evtable.EvTable(border=None)
            things = [item.db.sdesc for item in self.db.holding if item]
            for thing in things:
                h_table.add_row("{w(holding in hand){n " + "{G%s{n" % (thing))
            string += "\n\n%s" % (h_table) 
        items = [item for (part, item) in self.db.equipped.items() if 
            item["armor"] or item["clothing"]]
        if self.db.wielding.values():
            w_table = evtable.EvTable(border=None)
            mwielding_str = None
            owielding_str = None
            if self.db.wielding["main"] and \
                self.db.wielding["main"].db.hands > 1:
                mwielding_str = "(wielding in both hands) {G%s{n" % \
                    (self.db.wielding["main"].db.sdesc)
            elif self.db.wielding["main"]:
                mwielding_str = "(wielding in main-hand) {G%s{n" % \
                    (self.db.wielding["main"].db.sdesc)
            if self.db.wielding["main"] and self.db.wielding["main"].db.broken:
                mwielding_str += " {R(broken){n"
            if self.db.wielding["off"]:
                owielding_str = "(wielding in off-hand) {G%s{n" % \
                    (self.db.wielding["off"].db.sdesc)
            if self.db.wielding["off"] and self.db.wielding["off"].db.broken:
                owielding_str += " {R[broken]{n"
            if mwielding_str:
                w_table.add_row(mwielding_str)
            if owielding_str:
                w_table.add_row(owielding_str)
            table_str = "\n%s" % (w_table)
            string += table_str
        if any(items):
            e_table = evtable.EvTable(border=None)
            # need to get the actual order that the items should be in
            # when the equipped table is put together
            # eg. head, torso, arms, hands, legs, feet
            body_order = [
                (self.db.body[self.db.body.index(bodypart)].order_vis,
                bodypart) for bodypart in self.db.equipped.keys()]
            # sort the body order now
            body_order = sorted(body_order, key=lambda body_o: body_o[0])
            # we only want the bodypart now, not the number since it's ordered
            body_order = [part[1] for part in body_order]
            for part in body_order:
                if self.db.equipped[part]["armor"]:
                    e_table.add_row("(worn over %s)" % (part) + " {G%s{n" % 
                        (self.db.equipped[part]["armor"].db.sdesc))
                elif self.db.equipped[part]["clothing"]:
                    e_table.add_row("(worn on %s)" % (body_part) + " {G%s{n" %
                        (self.db.equipped[part]["clothing"].db.sdesc))
            table_str = "\n%s\n" % (e_table)
            string += table_str
        else:
            string += "\n{M%s{n is naked." % (self.db.sdesc.capitalize())
        if users:
            string += "\n{wYou see:{n " + ", ".join(users)
        return string

    def add_wound(self, location=None, damage=0, bleed=0, dmg_type=None):
        """
        Adds wounds to a character, based on damage, bleed, and damage type.
        """
        if damage == 0 and bleed > 0:
            wound = wounds.BloodlossWound(bleed, self)
        elif damage > 0:
            wound = wounds.Wound(location, damage, bleed, dmg_type, self)
        self.db.wounds.append(wound)
        new_health = self.db.health - damage
        self.set_health(new_health)
        if bleed > 0 and not self.ndb.combat_handler:
            tickerhandler.add(self, 30, hook_key="at_bleed_tick")
        if not self.ndb.combat_handler:
            tickerhandler.add(self, 3600, hook_key="at_heal_tick")

    def get_health_percent(self):
        """
        Gets the character's current health percentage, as a float.
        """
        hp = self.db.health * 1.0
        max_hp = self.db.max_health
        return hp / max_hp

    def prompt(self):
        """
        Custom prompt method we use for characters.
        """
        hp_percentage = self.get_health_percent()
        bleed = False
        for wound in self.db.wounds:
            if wound.bleed > 0:
                bleed = True
        if hp_percentage >= .90:
            hp = "{G%i{n" % (hp)
        elif hp_percentage >= .75:
            hp = "{W%i{n" % (hp)
        elif hp_percentage >= .50:
            hp = "{w%i{n" % (hp)
        elif hp_percentage >= .25:
            hp = "{Y%i{n" % (hp)
        else:
            hp = "{R%i{n" % (hp)
        prompt = "\n< HP: %s" % (hp)
        if bleed:
            prompt += ", {RBleeding{n > "
        else:
            prompt += " > "
        if self.ndb.combat_handler:
            pos_points = self.ndb.pos
            if pos_points == 8:
                pos_points = "%i" % (pos_points)
            elif pos_points >= 5:
                pos_points = "{G%i{n" % (pos_points)
            elif pos_points >= 3:
                pos_points = "{C%i{n" % (pos_points)
            elif pos_points == 2:
                pos_points = "{Y%i{n" % (pos_points)
            else:
                pos_points = "{R%i{n" % (pos_points)
            prompt += "< Pos: %s > " % (pos_points)
            opp = self.ndb.combat_handler.db.pairs[self]
            prompt += "/ \n{M%s{n: " % (opp.db.sdesc)
            o_hp_percentage = (opp.db.health * 1.0) / opp.db.max_health 
            if o_hp_percentage >= .90:
                o_hp_level = "{GUninjured{n"
            elif o_hp_percentage >= .75:
                o_hp_level = "Hurt"
            elif o_hp_percentage >= .50:
                o_hp_level = "{YInjured{n"
            elif o_hp_percentage >= .25:
                o_hp_level = "{YVery Injured{n"
            else:
                o_hp_level = "{RAlmost Dead{n"
            prompt += "< %s > " % (o_hp_level)

            if opp.ndb.pos == 8:
                o_pos = "Perfect"
            elif opp.ndb.pos >= 5:
                o_pos = "{GGreat{n"
            elif opp.ndb.pos >= 3:
                o_pos = "{CModerate{n"
            elif opp.ndb.pos == 2:
                o_pos = "{YMinor{n"
            else:
                o_pos = "{RPoor{n"
            prompt += "< Pos: %s > " % (o_pos)
            prompt += "\n"
        return prompt

    def genderize_str(self, arg=0):
        """
        Returns a proper gender string depending on the arg.

        0 - possessive eg. his/her/its
        1 - pronoun eg. he/she/it
        2 - him/her/it
        """
        if arg == 0:
            if self.db.sex == "male":
                return "his"
            elif self.db.sex == "female":
                return "her"
            else:
                return "its"
        elif arg == 1:
            if self.db.sex == "male":
                return "he"
            elif self.db.sex == "female":
                return "she"
            else:
                return "it"
        elif arg == 2:
            if self.db.sex == "male":
                return "him"
            elif self.db.sex == "female":
                return "her"
            else:
                return "it"

    def get_holding_count(self):
        """
        Gets the count of how many objects this character
        is holding.
        """
        hold_count = 0
        for item in self.db.wielding.values():
            if item and item.attributes.get("hands"):
                hold_count += item.db.hands
        for item in self.db.holding:
            if item:
                hold_count += 1
        return hold_count

    def at_heal_tick(self, **kwargs):
        """
        Heals wounds every tick. 
        """
        total_dmg = 0
        copy_wounds = list(self.db.wounds)
        if not copy_wounds:
            self.stop_heal()
            return
        for i in range(len(copy_wounds)):
            new_dam = copy_wounds[i].damage - 3
            self.db.wounds[i].damage = new_dam
            if not self.db.wounds[i].is_valid():
                self.db.wounds.remove(copy_wounds[i])
        for wound in self.db.wounds:
            total_dmg += wound.damage
        new_health = self.db.max_health - total_dmg
        self.set_health(new_health)

    def at_bleed_tick(self, divisor=2, **kwargs):
        """
        Bleeds the character every tick. Halves bleed every tick by default.
        If divisor argument is set to 0, we do not reduce bleed damage.
        """
        total_dmg = 0
        copy_wounds = list(self.db.wounds)
        string = ""
        bleed_list = []
        for i in range(len(copy_wounds)):
            if copy_wounds[i].bleed > 0:
                total_dmg += copy_wounds[i].bleed
                # add to bleed list so we can output about what they're
                # bleeding from
                bleed_list.append(self.db.wounds[i])
                # check if divisor is 0. If it is, we don't divide.
                # That'd cause a bad error
                if divisor != 0:
                    self.db.wounds[i].at_bleed_tick(divisor)
                # if it's internal bleeding, we remove that here
                # manually
                if isinstance(copy_wounds[i], wounds.BloodlossWound):
                    self.db.wounds.remove(self.db.wounds[i])
        bleed = False
        new_health = self.db.health - total_dmg
        self.set_health(new_health)
        # check if bleed is true
        for wound in self.db.wounds:
            if wound.bleed > 0:
                bleed = True
        # if bleed is false, that means they stopped bleeding
        if total_dmg > 0 and not bleed:
            self.stop_bleed()
            string = "\n{RYou stop bleeding dangerously.{n\n"
            self.msg(string, prompt=self.prompt())
            to_room_str = "\n{M%s{n" % (self.db.sdesc.capitalize()) + \
                " no longer seems to be bleeding dangerously.\n"
            self.location.msg_contents(to_room_str, exclude=self)
        # if bleed is true, tell 'em they're bleeding and all that
        elif total_dmg > 0:
            string = "\n{RYou continue to bleed from your injuries.{n\n"
            self.msg(string, prompt=self.prompt())
            bleed_str = [str(wound) for wound in bleed_list]
            bleed_str = ", ".join(bleed_str)
            to_room_str = "\n{M%s{n continues to bleed from: %s.\n" % \
                (self.db.sdesc.capitalize(), bleed_str)
            self.location.msg_contents(to_room_str, exclude=self)

    def start_heal(self):
        """
        Starts the heal tick. 
        """
        tickerhandler.add(self, 60 * 60, hook_key="at_heal_tick")


    def start_bleed(self):
        """
        Starts the bleed tick.
        """
        tickerhandler.add(self, 30, hook_key="at_bleed_tick")

    def stop_heal(self):
        """
        Removes the heal tick from the character.
        """
        tickerhandler.remove(self, 60 * 60)

    def stop_bleed(self):
        """
        Removes the bleed tick from the character.
        """
        tickerhandler.remove(self, 30)

    def check_uncon(self):
        """
        Check to see if the character would fall unconscious.
        """
        if self.db.health < 0:
            return True
        return False

    def set_uncon(self):
        """
        Sets the character unconscious.
        """
        self.db.state = 2
        string = "You have fallen unconscious!"
        self.msg(string)

    def check_dead(self):
        """
        Checks if the player would die. If they fall in the negative
        of over 10 percent of their max health, then they will die.
        """
        # see how far they are from dying
        if self.db.health < 0:
            health = abs(self.db.health)
            if health > round(self.db.health * 0.1, 0):
                return True
        return
    def set_dead(self):
        """
        Sets the character to dead. Stop all scripts on this character
        when they die.
        """
        self.db.state = 3
        self.scripts.all.stop()
        string = "You have died. Well, that's unfortunate."
        self.msg(string)

    def get_health(self):
        """ Hook to return the character's health."""
        return self.db.health

    def get_bleed(self):
        """ Getter method for getting character's bleed."""
        return self.db.bleed

    def get_max_weight(self):
        """ Getter method for getting max encumbrance limit for character."""
        return self.db.max_weight

    def get_cur_weight(self):
        """ Getter method for getting current encumbrance limit for character."""
        return self.db.weight

    def set_health(self, health):
        """ Setter method for health. """
        if health > self.db.max_health:
            self.db.health = self.db.max_health
        else:
            self.db.health = health

    def set_bleed(self, bleed):
        """ Setter method for bleed."""
        if bleed > self.db.max_bleed:
            self.db.bleed = self.db.max_bleed
        else:
            self.db.bleed = bleed

    def set_max_weight(self, max_weight):
        """ Setter method for max weight."""
        self.db.max_weight = max_weight
    def set_cur_weight (self, cur_weight):
        """ Setter method for current weight."""
        self.db.cur_weight = cur_weight

    def set_pos(self, new_pos):
        if new_pos > 8:
            self.ndb.pos = 8
        elif new_pos < 0:
            self.ndb.pos = 0
        else:
            self.ndb.pos = new_pos