from ev import create_script
from ev import search_script
from ev import Script
from ev import logger
from game.gamesrc.combat import move
from game.gamesrc.combat import resolve_combat
from game.gamesrc.combat import combo
import random

COMBAT_ROUND_TIMEOUT = 40
ROOM_DEPTH = 3
STATUS_STORAGE = search_script("StatusStorage")
STATUS_STORAGE = STATUS_STORAGE[0]

class CombatHandler(Script):
    """
    This implements the combat handler.
    """
    # standard Script hooks 
    def at_script_creation(self):
        # Called when script is first created
        random_key = "combat_handler_%i" % random.randint(1, 1000)
        while search_script(random_key):
            random_key = "combat_handler_%i" % random.randint(1, 1000)
        self.key = random_key
        self.desc = "handles combat"
        self.interval = COMBAT_ROUND_TIMEOUT
        self.start_delay = True
        self.persistent = True   
        self.db.origin_location = None
        self.db.rooms = []
        self.db.exits = []
        # store all combatants - {dbref1:character}
        self.db.characters = {}
        # store all combat pairs - {attacker1:victim1, attacker2:victim2}
        self.db.pairs = {}
        # store all moves for each turn
        # character.id:{move:char_move, previous_move:prev_move}
        self.db.turn_actions = {}
        # stores all combos for each character - character.id:combo
        self.db.turn_combos = {}
        # stores any flee attempts for each character - character.id:count
        self.db.flee_count = {}
        # shifting targets - character.id:desired new target
        self.db.shifting = {}
        # rescuing targets - character.id:desired rescuee
        self.db.rescuing = {}
        # characters that are requesting a stop - character:target
        self.db.stop_requests = {}
        # add status effects for the turn - 
        # character.id: {effect1:eff1_duration, effect2:eff2_duration}
        self.db.turn_effects = {}

    def _init_character(self, character):
        # This initializes handler back-reference and 
        # combat cmdset on a character"
        character.ndb.combat_handler = self
        character.cmdset.add("CmdSetCombat.CmdSetCombat")
        character.ndb.pos = 0
        # remove bleeding tick
        character.stop_bleed()
        # remove healing tick
        character.stop_heal()
        # we essentially delete all status effects on the player at
        # the start of combat and reinitialize them without an actual 
        # interval, so we force_repeat them manually at the end of each round. 
        # We restore all status effects as well when combat ends,
        # with their proper intervals and repeats.
        try:
            scripts = character.scripts.all()
            for script in scripts:
                if script.db.is_status_effect:
                    repeats = script.remaining_repeats()
                    next_repeat = script.time_until_next_repeat()
                    script.stop()
                    if repeats > 1:
                        create_script(script, obj=character,
                            repeats=repeats, interval=COMBAT_ROUND_TIMEOUT)
                    # if there was more than 15 seconds remaining 
                    # on the tick, we add it again with a single repeat
                    elif next_repeat > 15:
                        create_script(script, obj=character,
                            repeats=1, interval=COMBAT_ROUND_TIMEOUT)
        except:
            pass

    def _cleanup_character(self, character):
        # Remove character from handler and clean it 
        # of the back-reference and cmdset"
        dbref = character.id 
        character.cmdset.delete("CmdSetCombat")
        if character in self.db.pairs.keys():
            del self.db.pairs[character]
        if dbref in self.db.turn_actions.keys():
            del self.db.turn_actions[dbref]
        if dbref in self.db.turn_combos.keys():
            del self.db.turn_combos[dbref] 
        if dbref in self.db.turn_effects.keys():  
            del self.db.turn_effects[dbref]
        if dbref in self.db.characters.keys():
            del self.db.characters[dbref]
        del character.ndb.combat_handler
        if character.ndb.pos:
            del character.ndb.pos
        # add bleeding tick if they're bleeding
        try:
            for wound in character.db.wounds:
                if wound.bleed > 0:
                    character.start_bleed()
                    break
        except:
            pass
        # add healing tick
        character.start_heal()
        # we unpause all status effects and let them run normally. codedly,
        # this means removing all of the status effects on the character,
        # then reinitializing them with the standard interval, 
        # with repeats intact.
        try:
            for script in character.scripts.all():
                if script.db.is_status_effect:
                    next_repeat_sec = script.time_until_next_repeat()
                    repeats = script.remaining_repeats()
                    script.stop()
                    if repeats > 1 and next_repeat_sec > 20:
                        create_script(script, obj=character, 
                            repeats=repeats, interval=30)
        except:
            pass

    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to 
        all characters as well as re-assign the cmdset.
        """
        for character in self.db.characters.values():
            self._init_character(character)
        #self.combat_state()

    def at_stop(self):
        """
        Called just before the script is stopped/destroyed.
        """
        logger.log_infomsg("stopping the combat handler.")
        if any(self.db.characters):
            try:
                for character in list(self.db.characters.values()):
                # note: the list() call above disconnects listing 
                # from database
                    self._cleanup_character(character)
            except:
                pass

    def at_repeat(self):
        """
        This is called every self.interval seconds or when force_repeat 
        is called (because everyone has entered their commands).
        """
        # set all combos that are empty to the dummy combo value
        for (dbref, char_combo) in self.db.turn_combos.items():
            if not char_combo:
                self.db.turn_combos[dbref] = combo.Dummy()
        self.process_stances()
        # hook in AI move stuff here
        self.end_turn()
        #self.combat_state()

    # Combat-handler methods
    def add_character(self, character, target):
        # Add combatant to handler"
        dbref = character.id
        self.db.characters[dbref] = character
        self.db.pairs[character] = target
        # move, combo, previous_move        
        self.db.turn_actions[dbref] = {"move":None, "previous_move":None}
        self.db.turn_combos[dbref] = None
        self.db.turn_effects[dbref] = {}
        self._init_character(character)

    def remove_character(self, character):
        # Remove combatant from handler"
        if character.id in self.db.characters.keys():
            self._cleanup_character(character)
        if len(self.db.characters) < 2:
            self.msg_all("The battle has died down.\n", False)
            self.stop()
        elif not self.db.characters:
            self.stop()

    def msg_all(self, message, prompt=True):
        # Send message to all combatants
        last_room = None
        for character in self.db.characters.values():
            if prompt:
                character.msg(message, 
                    prompt=character.prompt())
            else:
                character.msg(message)
            if character.location != last_room:
                last_room = character.location
                opp = self.db.pairs.get(character)
                character.location.msg_contents(message, exclude=[character,
                     opp])

    def combat_state(self):
        """
        This makes the surrounding area with a 3-depth recursion in all
        directions (using the exit) a "battleground", which means that
        standard movement is delayed in time with the round pulse.

        TO DO: Add in a script to the affected rooms to prevent certain
        commands from being done.
        """
        # make the surrounding area a battleground
        exits = (con for con in self.db.origin_location.contents
                 if con.destination)
        for exit in exits:
            if self.db.origin_location not in self.db.rooms:
                self.db.rooms.append(self.db.origin_location)
            if exit not in self.db.exits:
                self.db.exits.append(exit)
            exit.ndb.combat_handler = self
            self.recurse_room_state(exit, ROOM_DEPTH)

    def recurse_room_state(self, exit, count):
        """
        Our actual recursion for the combat_state, which will keep
        calling the function until the count is 0. Default recursion
        is 3, for a 3-depth recursion on all exits in every directions
        that's a standard cardinal direction. Non-standard exits do not
        recurse.
        """

        exits = (con for con in exit.destination.contents if con.destination)
        for exit in exits:
            if exit not in self.db.exits:
                self.db.exits.append(exit)
            if exit.destination not in self.db.rooms:
                self.db.rooms.append(exit.destination)
            exit.ndb.combat_handler = self
            # if the exit isn't a standard exit name, the recursion
            # ends here
            if exit.key not in \
                ("north", "east", "south", "west", "up", "down"):
                return
            # as long as the count is greater than 0, then
            # we recursively call the function again on the exit
            # to branch out and make more exits part of our
            # "battleground"
            if count > 0:
                self.recurse_room_state(exit, count - 1)

    def get_opponent(self, character):
        return self.db.pairs.get(character, None)

    def add_action(self, character, action):
        """
        Called by combat commands to register an action with the handler.

         action - string identifying the action, like "hit" or "parry"
         character - the character performing the action

        Actions are stored in dictionaries in the format of:

        character.id: [action, previous_action]
        """
        dbref = character.id
        # making sure we keep the information of the previous move
        previous_move = self.db.turn_actions[dbref]["previous_move"]
        self.db.turn_actions[dbref]["move"] = action
        self.db.turn_actions[dbref]["previous_move"] =  previous_move

    def add_combo(self, character, char_combo):
        """
        Called by combat commands to register a char_combo with the handler.

         char_combo - actual char_combo class, defined in move.py, 
         like "rampage", "flurry"
         character - the character performing the action

        char_combos are stored in dictionaries in the format of:

        character.id: char_combo
        """
        dbref = character.id
        self.db.turn_combos[dbref] = char_combo

    def add_shifting_char(self, char, new_target):
        """
        Adds someone to the shifting dict, which keeps track of who's trying to
        shift targets this turn.
        """
        dbref = char.id
        self.db.shifting[dbref] = new_target
        char.scripts.add("game.gamesrc.scripts.status_effects.ShiftTarget")

    def switch_target(self, char, new_target):
        """
        Switches the character's previous target with the
        new target. It deletes the dbref in the shifting dict as well.
        """
        dbref = char.id
        del_shifting_char(char)
        del self.db.pairs[char]
        self.db.pairs[char] = new_target

    def del_shifting_char(self, char):
        """
        Deletes the given character from the shifting dict, such
        as when a player stops trying to shift targets or when they
        successfully do so.
        """
        if self.db.shifting[dbref]:
            del self.db.shifting[dbref]
        char.scripts.stop("game.gamesrc.scripts.status_effects.ShiftTarget")

    def add_flee_char(self, char):
        """
        Adds a character to the fleeing dict with a count of 0.
        """
        dbref = char.id
        self.db.flee_count[dbref] = 0
        char.scripts.add("game.gamesrc.scripts.status_effects.Flee")

    def add_flee_count(self, char):
        """
        Increases the flee count for the given character,
        or adds the character to the flee dict. It will not
        add up past 2.
        """
        dbref = char.id
        if dbref not in self.db.flee_count.keys():
            add_flee_char(char)
        else:
            self.db.flee_count[dbref] += 1
        if self.db.flee_count[dbref] > 2:
            self.db.flee_count[dbref] = 2

    def add_status_effect(self, char, status_effect, repeats=None):
        """
        Add status effect to the combat handler to add at the end of the turn.
        """
        logger.log_infomsg("Calling the status effect function.")
        dbref = char.id
        self.db.turn_effects[dbref][status_effect] = repeats
        logger.log_infomsg("The turn_effect dict is now %s for %s" %\
            (self.db.turn_effects[dbref], char.db.sdesc))

    def del_flee_char(self, char):
        """
        Deletes the character from the flee dict, such as when
        a character successfully flees or stops trying to flee.
        """
        dbref = char.id
        if self.db.flee_count[dbref]:
            del self.db.flee_count[dbref]
        char.scripts.delete("game.gamesrc.scripts.status_effects.Flee")

    def add_rescue(self, char, rescuee):
        """
        Adds a rescue attempt to our combat handler.

        Char is the rescuer, and rescuee is the rescue-ee. 
        """ 
        dbref = char.id
        self.db.rescuing[dbref] = rescuee
        char.scripts.add("game.gamesrc.scripts.status_effects.Rescue")

    def rescue_tgt(self, char, tgt):
        """
        Processes the rescue attempt, assuming it was a success.
        This function does not check for a success, it assumes
        the checks were already done before it was called.
        """
        # get the attacker and then delete who they're attacking
        # in combat
        attacker = self.db.pairs[tgt]
        del combat_handler.db.pairs[attacker]
        # make their new target our rescue-er
        combat_handler.db.pairs[attacker] = char
        # process and delete the rescue attempt from our handler
        self.del_rescue(char)

    def del_rescue(self, char):
        """
        Deletes a rescue attempt from the combat handler.
        """
        dbref = char.id
        if self.db.rescuing[dbref]:
            del self.db.rescuing[dbref]
        char.scripts.delete("game.gamesrc.scripts.status_effects.Rescue")

    def del_actions(self, char):
        """
        Deletes any existing moves or combos for the character.
        """
        dbref = char.id
        previous_move = self.db.turn_actions[dbref]["previous_move"]
        self.db.turn_actions[dbref] = {"move":None, 
            "previous_move": previous_move}
        self.db.turn_combos[dbref] = None

    def add_stop_request(self, character, target):
        """
        Adds a stop request to the combat handler.
        """
        self.db.stop_requests[character] = target

    def del_stop_request(self, character):
        """
        Removes a stop request from the combat handler.
        """
        if character in self.db.stop_requests.keys():
            del self.db.stop_requests[character]

    def process_stances(self):
        """
        At the end of the turn, if players haven't chosen a move,
        the system will choose something for them based on their stance.
        """
        # set all turns that are empty to pass_turn
        for character in self.db.characters.values():
            dbref = character.id
            if not self.db.turn_actions[dbref]["move"]:
                stance = character.db.settings["stance"]
                banned_moves = self.find_banned_moves(character)
                tgt = self.db.pairs[character]
                chosen_move = self.stance_chooser(character, 
                    stance, banned_moves, tgt)
                self.db.turn_actions[dbref]["move"] = chosen_move

    # stance rules, in the form of {stance:{tgt_move:banned_move}}
    # so we check the target move, if it matches up, then we ban 
    # banned_move from our available moves list.
    STANCE_RULES = {
    "offensive": {move.thrust: move.riposte, 
    move.high_parry: move.slash, move.low_parry: move.slash},
    "defensive": {move.high_cut: move.duck, move.low_cut: move.low_parry, 
    move.high_cut: move.high_parry, move.thrust:move.dodge}}

    def stance_chooser(self, character, chosen_stance, banned_moves, target):
        """
        Chooses a move based on the given stance, and the banned moves.
        If there's any banned moves, then we automatically revert to
        complete randomization. If not random, we choose moves based on
        our target's previous move. 

        In short, our rules for selecting moves are:

        * defensive knows to never duck after high cut, low parry after low
        cut, high parry after high cut, or dodge after thrust - ONLY DOES
         DEFENSIVE MOVES
        * offensive knows to never riposte after thrust or slash after either
        low or high parry - ONLY DOES OFFENSIVE MOVES
        * balanced knows both
        * randomizer always kicks in for status effects, stances don't matter
         when you're status effect'd up
        """
        # if it ever returns that all moves are banned, naturally we pass.
        # there's nothing our stance AI can do.
        if banned_moves == "all":
            return move.pass_turn
        previous_move = self.db.turn_actions[character.id]["previous_move"]
        # classic moves will be the holder for all moves our character
        # can actually do
        classic_moves = move.CLASSIC_MATRIX[:]
        # remove our previous move from the list of available moves
        if previous_move and previous_move != move.pass_turn:
            classic_moves.remove(previous_move)
        # if banned moves existed, that means we had status effects
        # that banned out moves. If this is the case, we totally
        # randomize our move selection.
        if banned_moves:
            for banned_move in banned_moves:
                if banned_move in classic_moves:
                    classic_moves.remove(banned_move)
            if classic_moves:
                random_move = random.choice(classic_moves)
                return random_move
            else:
                return move.pass_turn
        # grab our previous move that our target did
        tgt_move = self.db.turn_actions[target.id]["previous_move"]
        if not tgt_move:
            tgt_move = move.pass_turn
        # it's time to get rid of any moves that don't meet the criteria
        # of any of our stances. That means that for offensive/defensive,
        # they only perform offensive/defensive moves, so it makes sense
        # to get rid of all of our available offensive/defensive moves.
        if chosen_stance == "offensive":
            for c_move in list(classic_moves):
                if c_move.move_type == "defensive":
                    classic_moves.remove(c_move)
            for (t_move, ban_move) in self.STANCE_RULES["offensive"].items():
                if t_move == tgt_move and ban_move in classic_moves:
                    classic_moves.remove(ban_move)
            return random.choice(classic_moves)
        if chosen_stance == "defensive":
            for c_move in list(classic_moves):
                if c_move.move_type == "offensive":
                    classic_moves.remove(c_move)
            for (t_move, ban_move) in self.STANCE_RULES["defensive"].items():
                if t_move == tgt_move and ban_move in classic_moves:
                    classic_moves.remove(ban_move)
            return random.choice(classic_moves)
        # if the stance was neither defensive nor offensive,
        # because it was 'balanced' or it wasn't found,
        # then we use balanced by default
        else:
            # balanced knows both rules of offensive/defensive
            for (t_move, ban_move) in self.STANCE_RULES["offensive"].items():
                if t_move == tgt_move and ban_move in classic_moves:
                    classic_moves.remove(ban_move)
            for (t_move, ban_move) in self.STANCE_RULES["defensive"].items():
                if t_move == tgt_move and ban_move in classic_moves:
                    classic_moves.remove(ban_move)
            return random.choice(classic_moves)

    def find_banned_moves(self, character):
        """
        Find all the banned moves that a character might have.
        """
        banned_move = []
        for script in character.scripts.all():
            if script.db.no_combat_moves and script.db.no_combat_moves == True:
                banned_move = "all"
                return banned_move
            if script.db.no_combat_moves:
                for move in script.db.no_combat_moves:
                    if move not in banned_move:
                        banned_move.append(move)
        return banned_move

    def process_stop_requests(self):
        """
        At the end of the turn, it processes stop requests.
        If a pair agrees to withdraw from combat, it will succeed
        at the end of the turn so long as nobody else is attacking
        either of the pair. If someone else is attacking one of the pair,
        the attacked character will not withdraw from combat and randomly
        shift targets to one of the characters still attacking them.
        """
        stop_requests = dict(self.db.stop_requests)
        stops = {}
        for (att, tgt) in stop_requests.items():
            # if a stop request matches with the other, then we have a pair
            # that agrees on a stop.
            if (att in stop_requests.values() and\
                tgt in stop_requests.values() and\
                stop_requests[tgt].id == att.id) and\
            (tgt not in stops.values() or att not in stops.values()):
                # check who's still attacking our pair
                att_attackers = [target for (attacker, target)
                    in self.db.pairs.items() if target.id == att.id and
                    attacker.id != tgt.id]
                tgt_attackers = [target for (attacker, target)
                    in self.db.pairs.items() if target.id == tgt.id and
                    attacker.id != att.id]
                # add these guys to our stop dict, just so we don't 
                # do it twice per pair as we iterate
                stops[att] = tgt
                att.msg("You cease combat with {M%s{n.\n" % (tgt.db.sdesc))
                tgt.msg("You cease combat with {M%s{n.\n" % (att.db.sdesc))
                # delete the outstanding stop rqeuests
                self.del_stop_request(att)
                self.del_stop_request(tgt)
                # If they aren't being attacked by anyone else, 
                # then withdraw them from combat. 
                if att_attackers:
                    new_tgt = random.choice(att_attackers)
                    att.msg("You are still being attacked," + 
                        " and you turn your attention to {M%s{n!" % \
                            (new_tgt.db.sdesc))
                    new_tgt.msg("{M%s{n shifts their attention on you," % \
                            (att.db.sdesc) +
                        "as they disengage in combat with {M%s{n." % \
                            (tgt.db.sdesc))
                    self.db.pairs[att] = new_tgt
                else:
                    att.msg("No one else is attacking you, and" +
                             " you withdraw from combat.")
                    att.location.msg_contents("{M%s{n withdraws from combat" %\
                        (att.db.sdesc.capitalize()) + 
                        " as they cease combat with {M%s{n." % \
                            (tgt.db.sdesc), exclude=att)
                    self.remove_character(att)
                if tgt_attackers:
                    new_tgt = random.choice(tgt_attackers)
                    tgt.msg("You are still being attacked," + 
                            " and you turn your attention to {M%s{n!" % \
                            (new_tgt.db.sdesc))
                    new_tgt.msg("{M%s{n shifts their" % (tgt.db.sdesc) + 
                        "attention on you, as they disengage " + 
                        "in combat with {M%s{n." % \
                                    (att.db.sdesc))
                    self.db.pairs[tgt] = new_tgt
                else:
                    tgt.msg("No one else is attacking you," + 
                                " and you withdraw from combat.")
                    tgt.location.msg_contents("{M%s{n withdraws" % \
                        (tgt.db.sdesc.capitalize()) +
                    " from combat as they cease combat with {M%s{n." % \
                            (att.db.sdesc), exclude=tgt)
                    self.remove_character(tgt)

    def at_add_status_tick(self):
        """
        Combat tick for the turn. Adds any pending status effects.
        """
        for character in self.db.characters.values():
            dbref = character.id
            if self.db.turn_effects[dbref]:
                for (effect, duration) in self.db.turn_effects[dbref].items():
                    exist = None
                    repeats = 0
                    exist = character.scripts.get(effect)
                    if exist:
                        if exist.remaining_repeats():
                            repeats = exist.remaining_repeats()
                        exist.db.quiet_mode = True
                        exist.stop()
                    if duration:
                        create_script(STATUS_STORAGE.get_effect(effect),
                         obj=character, interval=COMBAT_ROUND_TIMEOUT, 
                         repeats=(duration + repeats))
                    else:
                        create_script(STATUS_STORAGE.get_effect(effect), 
                        obj=character, interval=COMBAT_ROUND_TIMEOUT)

    def at_bleed_tick(self):
        """
        Bleed tick for all characters.
        """
        for character in self.db.characters.values():
            character.at_bleed_tick()

    def end_turn(self):
        """
        This resolves all actions by calling the rules module. 
        It then resets everything and starts the next turn.
        """
        self.at_bleed_tick()
        self.process_stop_requests()
        resolve_combat.resolve_combat(self.db.characters,
            self.db.turn_actions, self.db.turn_combos, self.db.pairs, self)
        # reset counters before next turn
        self.at_add_status_tick()
        for (dbref, character) in self.db.characters.items():
            # 0 is the index for the character's move
            previous_move = self.db.turn_actions[dbref]["move"]
            self.db.turn_actions[dbref] = {"move":None, 
                "previous_move":previous_move}
            self.db.turn_combos[dbref] = None
            self.db.turn_effects[dbref] = {}
        logger.log_infomsg("End turn.")