from game.gamesrc.commands.command import MuxCommand
from game.gamesrc.combat import move
from game.gamesrc.combat import combo
import random

class CmdFlee(MuxCommand):
    """
    Usage: flee [!]

    Combat command that declares intention to flee. 
    For two rounds, they will only be able to defend unless 
    they stop their attempt to flee. Players attempting to flee 
    cannot use combos with defensive moves, and will be unable 
    to gain positioning while they try to flee. You must successfully 
    defend twice before you can leave combat.

    You need two positioning points to be able to attempt 
    fleeing at the time of your declaration to flee. 

    Use the 'flee' syntax by itself to initiate your attempt to flee. 
    Use 'flee !' to cancel your fleeing attempt. 
    """
    
    key = "flee"
    locks = "cmd:all()"
    def func(self):
        caller = self.caller
        combat_handler = caller.ndb.combat_handler
        dbref = caller.id
        pos_points = caller.ndb.pos
        if not combat_handler:
            caller.msg("You're not in combat. You can't do this.")
            return 
        if not self.args:
            if combat_handler.db.flee and dbref in combat_handler.db.flee.keys():
                string = "You're already attempting to flee. If you want to cancel your attempt to flee, "
                string += "type: 'flee !' to confirm. This is IRREVERSIBLE and resets your flee counter to 0."
                caller.msg(string)
        #need at least two positioning points to do this
        if pos_points >= 3:
            combat_handler.add_flee_char(caller)
            string = "You are now trying to flee combat. You may only use defensive moves and no combos "
            string += "for the next two turns. If you are successful in fending off all attacks in that time period, "
            string += "you will leave combat. Any moves or combos you inputted before you started fleeing have been "
            string += "deleted. You'll need to enter a new defensive move."
            caller.msg(string)
            combat_handler.msg_all("{M%s{n is now trying to flee combat!" % (caller.db.sdesc))
            # remove any turn actions and combo actions they tried before declaring intention to flee
            combat_handler.del_actions(caller)
            return
        else:
            string = "You don't have enough positioning to do that. You need at least three points to begin "
            string += "your fleeing attempt. The positional cost will be deducted after fleeing is successful. "
            string += "However, if you fail to preserve the positioning cost before you manage to flee, your flee "
            string += "will be cancelled, and you'll have to survive another two rounds."
            caller.msg(string)
            return
        if "!" in self.args:
            if combat_handler.db.flee and dbref in combat_handler.db.flee.keys():
                caller.msg("You have just cancelled your fleeing attempt. You may now resume normal combat.")
                combat_handler.del_flee_char(caller)
                combat_handler.msg_all("{M%s{n has ceased their attempt to flee the battlefield!" % (caller.db.sdesc))
                return
            else:
                caller.msg("You're not trying to flee. You can't cancel a fleeing attempt that doesn't exist.")
                return

class CmdCombatRescue(MuxCommand):     
    """ 
    Usage: rescue <target>

    Combat command that attempts to rescue someon if you have two positional
    points at least to use. You must be attacking the target that your 
    rescue-ee is, in order to rescue them. 
    
    You donot get normal positional bonuses for successfully winning this
    round while attempting to rescue.

    Use rescue without any arguments to cancel your rescue.
    """
    key = "rescue"
    aliases = "guard"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        pos_points = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        dbref = caller.id
        # Sanity checks.
        if not combat_handler:
            caller.msg("You're not in combat. You can't do this.")
            return 
        if not self.args:
            if combat_handler.db.rescuing and dbref in combat_handler.db.rescuing.keys():
                combat_handler.del_rescue(caller)
                caller.msg("Your rescue has been cancelled.")
            else:
                caller.msg("Who are you trying to rescue?")
            return
        if pos_points < 2:
            caller.msg("You don't have enough positional points to attempt doing that.")
            return
        self.args = self.args.strip()
        # Where is our victim?  First checks if it is the character name. If not, tries
        # finding it with the character's keywords.
        tgt = (caller.search(self.args, location=caller.location, quiet=True) 
            or caller.search(self.args, attribute_name="aliases", 
            location=caller.location, quiet=True))
        # Makes sure they can't attack ... nothing, and they can't attack themselves.
        if not tgt:
            caller.msg("You don't see that here. Aborting rescue.")
            return
        tgt = tgt[0]
        if tgt == caller:
            caller.msg("You can't rescue yourself!")
            return
        tgt_id = tgt.id
        # check if the player they're trying to rescue is attacking the same person that the caller is
        if dbref in pairs.keys() and\
            tgt_id in pairs.keys() and\
            pairs[dbref] == pairs[tgt_id]:
            combat_handler.add_rescue(char, tgt)
            attacker = pairs[dbref]
            string = "You will now attempt to rescue {M%s{n from {M%s{n. Keep in mind you must successfully "\
                    % (tgt.db.sdesc, attacker.db.sdesc)
            string += "win this round against your current combat target." 
            caller.msg()
        else:
            caller.msg("You can't rescue that person. You're not attacking the same person they are!")
            return

class CmdCombatStrike(MuxCommand):    
    """ 
    Usage: strike <target>     

    Combat command that attempts to shift targets if you have two positional
    points at least to use. You forgo your turn if you try to shift targets.
    You may type strike  without any arguments to cancel attempting to shift
    targets. This command will succeed given you aren't knocked unconscious or
    die in the turn that you're attempting to shift targets.

    """

    key = "strike"
    aliases = "shift"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        pos_points = caller.ndb.pos
        dbref = caller.id
        combat_handler = caller.ndb.combat_handler
        if not combat_handler:
            caller.msg("You're not in combat. You can't do this.")
            return 
        if not self.args:
            if combat_handler.db.shifting and \
            dbref in combat_handler.db.shifting.keys():
                caller.msg("Your attempted target shift has been cancelled.")
                combat_handler.del_shifting_char(caller)
            else:
                caller.msg("Who are you trying to shift your attention to" +
                " in combat?")
        if pos_points < 2:
            caller.msg("You don't have enough positional points to attempt" +
            " doing that.")
            return
        self.args = self.args.strip()
        # Where is our victim?  First checks if it is the character 
        # name. If not, tries finding it with the character's keywords.
        tgt = (caller.search(self.args, location=caller.location, quiet=True) 
            or caller.search(self.args, attribute_name="aliases", 
            location=caller.location, quiet=True))
        if not tgt:
            caller.msg("You don't see that person here. Aborting shifting" +
                " targets.")
            return
        tgt = tgt[0]
        if tgt == caller:
            caller.msg("You can't attack yourself!")
            return
        if tgt == pairs[dbref]:
            caller.msg("You're already attacking this target. Invalid " +
                "strike argument.")
            return
        combat_handler.del_actions(caller)
        combat_handler.add_shifting_char(caller, tgt)
        caller.msg("You will now attempt to shift targets to {M%s{n, giving up your turn this round." % (tgt.db.sdesc))
        

class CmdCombatMove(MuxCommand):
    """
    Usage: thrust/high cut/slash/riposte/dodge/high parry/low parry/ 
            duck/disengage
    Alternatively: th, hc, sl, ri, do, hp, lp, du, or di.

    You can use any of the combat moves after combat has been engaged
    via the "attack" command. You may change your attack before the end of a
    round, but doing so will remove any techniques that you have also entered
    that round.

    Below is the table for what moves beat which:

      +----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      |    |  {GTH{n |  {GHC{n |  {GLC{n |  {GSL{n |  {GRP{n | {GDO{n  |  {GHP{n |  {GLP{n |  {GDU{n |  {GDI{n |
      +----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CTH{n |  {rBo{n |  {CTH{n |  {CTH{n |  {CTH{n |  {GRP{n |  {GDO{n |  {GHP{n |  {GLP{n |  {CTH{n |  {GDI{n |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CHC{n |  {GTH{n |  Nu |  {rBo{n |  {CHC{n |  {CHC{n |  {CHC{n |  {GHP{n |  {CHC{n |  {GDU{n |  {CHC{n |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CLC{n |  {GTH{n |  {rBo{n |  Nu |  {CLC{n |  {CLC{n |  {CLC{n |  {CLC{n |  {GLP{n |  {CLC{n |  {CLC{n |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CSL{n |  {GTH{n |  {GHC{n |  {GLC{n |  {rBo{n |  {GRP{n |  {GDO{n |  {CSL{n |  {CSL{n |  {CSL{n |  Nu |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CRP{n |  {CRP{n |  {GHC{n |  {GLC{n |  {CRP{n |  Nu |  Nu |  Nu |  Nu |  Nu |  Nu |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CDO{n |  {CDO{n |  {GHC{n |  {GLC{n |  {CDO{n |  Nu |  Nu |  {CDO{n |  {CDO{n |  Nu |  Nu |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CHP{n |  {CHP{n |  {CHP{n |  {GLC{n |  {GSL{n |  Nu |  {GDO{n |  Nu |  Nu |  {GDU{n |  Nu |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CDU{n |  {GTH{n |  {CDU{n |  {GLC{n |  {GSL{n |  Nu |  Nu |  {CDU{n |  {CDU{n |  Nu |  Nu |
      |----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
      | {CDI{n |  {CDI{n |  {GHC{n |  {GLC{n |  Nu |  Nu |  Nu |  Nu |  Nu |  Nu |  Nu |
      +----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+

    Key:

    TH: Thrust [Offensive]      DO: Dodge [Defensive]
    HC: High Cut [Offensive]    HP: High Parry [Defensive]
    LC: Low Cut [Offensive]     LP: Low Parry [Defensive]
    SL: Slash [Offensive]       DU: Duck [Defensive]
    RP: Riposte [Offensive]     DI: Disengage [Defensive]

    Bo: Both - Both win the exchange
    Nu: Null - Neither win the exchange
    """
    key = "move"
    aliases = ["thrust", "th",
              "high cut", "hc", 
              "low cut", "lc",
              "slash", "sl", 
              "riposte", "ri", 
              "dodge", "do", 
              "high parry", "hp", 
              "low parry", "lp", 
              "duck", "du", 
              "disengage", "di",
              "pass"]

    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        cmdstring = self.cmdstring.strip()
        combat_handler = caller.ndb.combat_handler
        dbref = caller.id
        if not combat_handler:
            caller.msg("You're not in combat. You can't do this.")
            return 
        if combat_handler.db.turn_combos[dbref]:
            combat_handler.del_actions(caller)
        if cmdstring in ("attack"):
            string = "What move do you want to do? You can either thrust, high cut, slash,"
            string += " riposte, dodge, high parry, low parry, duck, or disengage, or use their"
            string += " abbreviations: th, hc, sl, ri, do, hp, lp, du, or di. You may also 'pass'"
            string += " to give up your turn."
            caller.msg(string)
            return
        # normally pass is not in the classic matrix, so we add it in here so
        # players have an option of passing the turn if they so choose.
        legal_moves = move.CLASSIC_MATRIX[:]
        legal_moves.append(move.pass_turn)
        for combat_move in legal_moves:
            if cmdstring in combat_move.name or cmdstring in combat_move.aliases:
                string = combat_move.is_valid(caller)
                if string:
                    caller.msg(string)
                    combat_handler.add_action(caller, move.pass_turn)
                    return
                if combat_move == combat_handler.db.turn_actions[dbref]["previous_move"]:
                    string = "You already did %s in the previous turn. You can't do it again for this turn!" % (combat_move.name)
                    caller.msg(string)
                    return
                string = "You prepare to %s." % (combat_move)
                caller.msg(string)
                combat_handler.add_action(caller, combat_move)
                return
        caller.msg("What did you want to do? Invalid input.")
        return

class CmdLongswordCombo(MuxCommand):
    """
    The following combo moves are available for longswords:

    Beat(cost: 2): Doubles damage for next round on a successful parry vs
    attack. 
    Feint(cost: 3): On a failed attack vs defense, the attack instead succeeds
    and scores +1 damage and you
    regain +2 positioning. On a trade vs another attack (ex: thrust/thrust),
    only your opponent scores. On a successful attack, nobody scores.
    Impale(cost: 5): On a successful thrust attack, you deal +4 damage and
    your opponent receives half of damage inflicted as bleed.

    Usage:
        lscombo 
        beat
        feint
        impale

    The syntax "lscombo" is to show you which combos are available to longswords. You must be in combat to use these commands.

    """
    key = "lscombo"
    aliases = ["beat", "feint", "impale"]
    help_category = "Combat"
    
    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.longsword_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("lscombo"):
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a beat, feint, or impale, if you have the positional points."
            caller.msg(string)
            return
        # found our legal combo, break the for loop
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        # if there was a chosen combo ...
        if chosen_combo:
            # check if they have the positioning to even do this
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            # if they haven't selected a move, we'll try and do a random legal
            # move on behalf of the caller so they can perform the combo.
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                # if we find that all of the moves are banned, then the command complains
                # and returns
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                # remove all of the banned moves from our legal move list
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                # if any moves are remaining, we choose a random move
                # and force them to execute that command
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            # grab the current move again
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            # double check again if the move can be done with this combo
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            # if we didn't return at any point, it's time to add the combo
            # to our combat handler
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What did you want to do? You can perform a beat, feint,"
            string += "or impale with a longsword, as long as you have the positioning."
            caller.msg(string)
            return

class CmdAxeCombo(MuxCommand):
    """
    The following combos are available for axes:
    - Rampage(cost: 2): Anyone dealing damage to you, or receiving damage from
    you this turn, adds +4 damage.
    - Cleave(cost: 3): On a successful high/low cut, opponent receives half of
    damage inflicted as bleed.
    - Break(cost: 5): Attempt to shatter an opponent's shield or weapon on an
    unsuccessful attack vs parry, so long as the object does not have the
    "unbreakable" trait.
    On Successful Roll: Shatter
    On Unsuccessful Roll: Reduce opponent's positioning to 0

    Usage:
        axecombo - to see all available axe combos
        rampage
        cleave
        break
    """
    key = "axecombo"
    aliases = ["rampage", "cleave", "break"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.axe_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("axecombo"):
            string = "What kind of technique do you want to perform? With an axe, you can "
            string += "perform a rampage, cleave, or break, if you have the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What kind of technique do you want to perform? With an axe, you can "
            string += "perform a rampage, cleave, or break, if you have the positional points."
            caller.msg(string)
            return

class CmdMaceCombo(MuxCommand):
    """
    The following combos are available for maces:
    - Daze(cost: 2): On a successful attack, opponent receives +2 damage and
    loses 2 positioning.
    - Stun(cost: 3): Stun an opponent for one round on a successful
     slash/riposte attack. Opponent automatically loses the next round.
    - Break(cost: 5): Attempt to shatter an opponent's shield or weapon on an
    unsuccessful attack vs parry, so long as the object does not have the
    "unbreakable" trait.
    On Successful Roll: Shatter
    On Unsuccessful Roll: Reduce opponent's positioning to 0

    Usage:
        macecombo - to see all available mace combos
        daze
        stun
        break
    """
    key = "macecombo"
    aliases = ["daze", "stun", "break"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.mace_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("macecombo"):
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a daze, stun, or break, if you have the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What did you want to do? You can perform a beat, feint,"
            string += "or impale with a longsword, as long as you have the positioning."
            caller.msg(string)
            return

class CmdShieldCombo(MuxCommand):
    """
    The following combos are available for shields:

    - Shield Bash(cost: 2) Knock an opponent to the ground for one round on a
    successful parry. Opponents lose 2 positioning and may only use 
    Duck/Riposte/Low Cut in the following round while they stand, and receive 
    +2 damage to all attacks next round.

    Usage:
        bash
        shield bash
    """
    key = "shieldcombo"
    aliases = ["bash", "shield bash"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.shield_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("shieldcombo"):
            string = "What kind of technique do you want to perform? With a shield, you can "
            string += "perform a shield bash, if you have the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What did you want to do? You can perform a shield bash, "
            string += "as long as you have the positioning."
            caller.msg(string)
            return


class CmdGreatswordCombo(MuxCommand):
    """
    The following combos are available for greatswords:

    - Clash(cost: 2) With a successful parry, you gain +2 positioning 
    and your opponent loses 2 positioning.
    - Smash(cost: 3) If you score with an attack, you deal double damage this
    turn, but are unable to gain positioning for the next three rounds.
    - Break(cost: 5) Attempt to shatter an opponent's shield or weapon on 
    an unsuccessful attack vs parry, so long as the object does not have the
    "unbreakable" trait.
    On Successful Roll: Shatter
    On Unsuccessful Roll: Reduce opponent's positioning to 0

    Usage: gscombo
           clash
           smash
           break
    """

    key = "greatswordcombo"
    aliases = ["gscombo", "clash", "smash", "break"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.greatsword_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("gscombo"):
            string = "What kind of technique do you want to perform? With a greatsword, you can "
            string += "perform a clash, smash, or break, if you have the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What kind of technique do you want to perform? With a greatsword, you can "
            string += "perform a clash, smash, or break, if you have the positional points."
            caller.msg(string)
            return


class CmdStaveCombo(MuxCommand):
    """
    The following combos are available for staves:
    - Disarm(cost: 2): Disarm an opponent for one round on a successful parry
    vs attack. Opponent may only use Thrust/Dodge/Duck in the following 
    round while they retrieve their weapon.
    - Sweep(cost: 3): Knock an opponent to the ground for one round on a
     successful attack. Opponents lose 2 positioning and may only use
    Duck/Riposte/Low Cut in the following round while they stand, and receive
    +2 damage to all attacks next round.
    - Flurry(cost: 5): On a successful attack, you deal +6 damage. Also winds
    the opponent, stopping any positioning gain for two rounds.

    Usage:
        stavecombo - to see all combos available to staves
        disarm
        sweep
        flurry
    """
    key = "stavecombo"
    aliases = ["disarm", "sweep", "flurry"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        cmdstring = self.cmdstring
        legal_combos = combo.stave_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        combat_handler = caller.ndb.combat_handler
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("stavecombo"):
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a sweep, disarm, or flurry, if you have the positional points."
            caller.msg(string)
            return
        opp = caller.ndb.combat_handler.get_opponent(caller)
        if opp and not any(opp.db.wielding) and cmdstring in "disarm":
            caller.msg("You can't disarm an unarmed opponent!")
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a sweep, disarm, or flurry, if you have the positional points."
            caller.msg(string)
            return

class CmdDaggerCombo(MuxCommand):
    """
    The following combos are available to daggers:
    - Circle(cost: 2) On a successful Dodge, you gain +2 to positioning 
    (total of 5), and next round you deal +2 damage on a successful attack.
    - Twist(cost: 3) On a successful Thrust, opponent receives half damage
     inflicted as bleed.
    - Backstab(cost: 5) On a successful Dodge or Duck, you deal 8-24 damage
    - armor bonuses. You gain no positioning for the round.
                        
    Usage:
        daggercombo - to see all dagger combos
        circle 
        backstab
        twist
    """
    key = "daggercombo"
    aliases = ["circle", "twist", "backstab"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.dagger_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("daggercombo"):
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a circle, twist, or backstab, if you have the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat, let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the compatible moves "
                    string += "can be performed right now with that combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What kind of technique do you want to perform? With a longsword, you can "
            string += "perform a circle, twist, or backstab, if you have the positional points."
            caller.msg(string)
            return

class CmdSpearCombo(MuxCommand):
    """
    The following combos are available to spears:
    - Counter(cost: 2): On a successful Riposte, you gain +2 positioning and
    your opponent cannot use attacks next turn.
    - Sweep(cost: 3): Knock an opponent to the ground for one round on 
    a successful attack.
    Opponents lose 2 positioning and may only use Duck/Riposte/Low Cut in
    the following round while they stand, and receive +2 damage to all attacks
    next round.
    - Impale(cost: 5): On a successful thrust attack, you deal +4 damage
    and your opponent receives half of damage inflicted as bleed.

    Usage:
        spearcombo
        counter
        sweep
        impale
    """
    key = "spearcombo"
    aliases = ["counter", "sweep", "impale"]
    help_category = "Combat"

    def func(self):
        caller = self.caller
        dbref = caller.id
        pos = caller.ndb.pos
        combat_handler = caller.ndb.combat_handler
        cmdstring = self.cmdstring
        legal_combos = combo.spear_combos
        chosen_combo = None
        if not caller.ndb.combat_handler:
            caller.msg("You can't perform techniques out of combat.")
            return
        cur_move = combat_handler.db.turn_actions[dbref]["move"]
        if cmdstring in ("spearcombo"):
            string = "What kind of technique do you want to perform? With a" +\
            "spear, you can perform counter, sweep, or impale, if you have" +\
            "the positional points."
            caller.msg(string)
            return
        for char_combo in legal_combos:
            if cmdstring == char_combo.name:
                chosen_combo = char_combo
                break
        if chosen_combo:
            if chosen_combo.can_move(caller):
                string = chosen_combo.can_move(caller)
                caller.msg(string)
                return
            if not cur_move:
                legal_moves = chosen_combo.legal_moves
                banned_moves = combat_handler.find_banned_moves(caller)
                if banned_moves == "all":
                    caller.msg("You can't do anything right now in combat,"+ \
                        " let alone a combo.")
                    return
                for ban_move in banned_moves:
                    if ban_move in legal_moves:
                        legal_moves.remove(ban_move)
                prev_move = combat_handler.db.turn_actions[caller.id]["previous_move"]
                if prev_move in legal_moves:
                    legal_moves.remove(prev_move)
                if legal_moves:
                    legal_move = random.choice(legal_moves)
                    caller.execute_cmd(str(legal_move))
                else:
                    string = "There is no way you can do that. None of the" + \
                    " compatible moves can be performed right now with that" +\
                    " combo."
                    caller.msg(string)
                    return
            cur_move = combat_handler.db.turn_actions[dbref]["move"]
            if chosen_combo.is_valid(cur_move):
                string = chosen_combo.is_valid(cur_move)
                caller.msg(string)
                return
            combat_handler.add_combo(caller, chosen_combo)
            string = "You prepare to do the technique: %s." % (chosen_combo)
            caller.msg(string)
            return
        else:
            string = "What kind of technique do you want to perform? With a" + \
            "spear, you can perform counter, sweep, or impale, if you have" + \
            "the positional points."
            caller.msg(string)
            return

class CmdStopCombat(MuxCommand):
    """
    Stops combat between two combatants if both sides agree. This
    automatically works if whoever you're targeting isn't targetting you
    in turn. If whoever you're fighting is targeting you also, both sides
    must type 'stop' before combat stops between the pair. You may also
    type stop again to cancel your stop request.

    Usage: 
        stop
    """
    key = "stop"
    locks="cmd:all()"
    help_category="Combat"

    def func(self):
        caller = self.caller
        combat_handler = caller.ndb.combat_handler
        if not combat_handler:
            caller.msg("You're not in combat. You can't do this.")
            return 
        tgt = combat_handler.db.pairs[caller]
        if caller in combat_handler.db.stop_requests.keys():
            tgt = combat_handler.db.stop_requests[caller]
            caller.msg("You cancel your stop request.")
            tgt.msg("{M%s{n cancels their stop request with you." % \
                (caller.db.sdesc))
            combat_handler.del_stop_request(caller)
            return
        caller.msg("You gesture for a stop to combat with {M%s{n." % \
            (tgt.db.sdesc))
        string = "\n\n{M%s{n " % (caller.db.sdesc[0].capitalize() + \
            caller.db.sdesc[1:])
        string += "gestures for a stop in combat with you. "
        string += "If you are not attacking them, they will " 
        string += "automatically stop attacking you when the round resolves.\n"
        tgt.msg(string)
        combat_handler.add_stop_request(caller, tgt)