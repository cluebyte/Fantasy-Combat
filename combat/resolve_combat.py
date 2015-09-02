from ev import logger
from game.gamesrc.combat.objects import armor
import random
from game.gamesrc.combat.objects import weapons
from game.gamesrc.combat import combo
from game.gamesrc.combat import move
from ev import search_script

# constants
WEAP_MAX_QUALITY = 4
WEAP_MIN_QUALITY = 1
ARMOR_MAX_QUALITY = 4
ARMOR_MIN_QUALITY = 1
# base move type positional gains for winning the round
OFFENSIVE_POS_GAIN = 1
DEFENSIVE_POS_GAIN = 2
# no trait penalty
NO_TRAIT_PENALTY = 1

STATUS_STORAGE = search_script("StatusStorage")
STATUS_STORAGE = STATUS_STORAGE[0]

def resolve_combat(characters, moves, combos, pairs, combat_handler):
    """
    Our magical combat resolver that applies damage, stamina drain, 
    bleed, and status effects on players based on the information the 
    combat script feeds us. We take the characters, actions, combos, 
    and pairs dict to do all our resolving.

    Damage/bleed is calculated separately from positional modifiers 
    (due to the complicated nature of pos gain), and applied using 
    its own dict (with the help of stat_dict). Positional modifier 
    calculatio has its own method that it uses, adding on 
    move/combo bonuses and stat_dict.

    Important to note that only damage taken and bleed taken matters 
    for the damage calculation method.

    It does not apply anything else, such as health regen or anything 
    of the sort (that'd be very confusing  to apply health_regen 
    in the actual damage calculation).
    """

    # Run through every pair and figure out outcomes. We first have 
    # to match up pairs so we can easily generate output as 
    # a series of "exchanges" between each combatant.
    logger.log_infomsg("We've made it into the resolve combat function.")
    parsed_pairs = pairify(pairs)
    logger.log_infomsg("Current combo dict %s" % (combos))
    for pair in parsed_pairs:
        # set some preliminary variables just so we have some defaults
        p_one_attacking = False
        p_two_attacking = False
        p_one_combo = None
        p_two_combo = None
        p_one = pair[0]
        p_two = pair[1]
        # check which players are actually attacking
        if pairs[p_one] == p_two:
            p_one_attacking = True
        if pairs[p_two] == p_one:
            p_two_attacking = True
        # if they're attacking, their combo counts
        if p_one_attacking:
            p_one_combo = combos[p_one.id]
        if p_two_attacking:
            p_two_combo = combos[p_two.id]
        logger.log_infomsg("p_one combo: %s - p_two_combo: %s" % (p_one_combo, p_two_combo))
        p_one_move = moves[p_one.id]["move"]
        p_two_move = moves[p_two.id]["move"]
        # Now we see who wins.
        winner = determine_outcome(p_one, p_one_move, p_one_combo,
            p_one_attacking, p_two, p_two_move, p_two_combo, p_two_attacking)
        logger.log_infomsg("Calling round results.")
        calc_round_results(p_one, p_one_attacking, p_two, p_two_attacking,
            moves, combos, winner)
        # send them an empty message so they see the prompt
        combat_handler.msg_all("")

def calc_round_results(char1, char1_attacking, char2, char2_attacking,
        move_dict, combo_dict, winner):
    """
    Calculates all the combat_stats for the pair. We assume here that char1
    is the attacker, and char2 is the defender. 

    The dicts we accept should be in the format of:

    mod_dict = {"dam_gain":0, "pos_gain":0, "health_regen":0, "bleed":0,
                "weap_q_mod":0, "armor_q_mod":0, "bleed_vuln":0,
                "shield_q_mod":0, "dam_vuln": 0 "pos_vuln":0, "bleed_vuln":0}

    The dicts we receive have already been parsed for status effects/traits.
    The only thing now that we need to do is calculate combo bonuses, and any
    outstanding weapon boosts because of the quality mod from the dict.
    We call calc_round_pos and calc_round_dam to calculate positional points
    and round damage. We then actually modify stats.
    """
    p_one_move = move_dict[char1.id]["move"]
    p_two_move = move_dict[char2.id]["move"]
    p_one_combo = combo_dict[char1.id]
    p_two_combo = combo_dict[char2.id]
    combat_handler = char1.ndb.combat_handler
    break_weapon = None
        # If winner is null, just run combat ticks 
        # as normal for all status effects and then end the turn.
    if winner == "null":
        dmg_dict1 = calc_round_dam(char1, char2, move_dict, combo_dict, False)
        dmg_dict2 =  calc_round_dam(char2, char1, move_dict, combo_dict, False)
        break_weapon = calc_round_pos(char1, char2, dmg_dict1["weapon"],
            dmg_dict2["weapon"], move_dict, combo_dict, dmg_dict1, dmg_dict2,
            winner)
        string = combat_output(char1, p_one_move, p_one_combo,
            char1_attacking, dmg_dict1, char2, p_two_move, p_two_combo,
            char2_attacking, dmg_dict2, winner)
        combat_handler.msg_all(string, False)
        apply_status(char1, "null", p_one_move, p_one_combo)
        apply_status(char2, "null", p_two_move, p_two_combo)
        check_special_status(char1, combat_handler)
        check_special_status(char2, combat_handler)
    # If winner is both, we have to calculate damage, 
    # bleed, positional points, and the like, 
    # then status effect combat_ticks.
    if winner == "both":
        dmg_dict1 = calc_round_dam(char1, char2, move_dict, combo_dict)
        dmg_dict2 =  calc_round_dam(char2, char1, move_dict, combo_dict)
        break_weapon = calc_round_pos(char1, char2, dmg_dict1["weapon"],
            dmg_dict2["weapon"], move_dict, combo_dict,
            dmg_dict1, dmg_dict2, winner)
        string = combat_output(char1, p_one_move, p_one_combo,
            char1_attacking, dmg_dict1, char2, p_two_move, p_two_combo,
            char2_attacking, dmg_dict2, winner)
        combat_handler.msg_all(string, False)
        personal_combat_msg(char1, char2, dmg_dict1, move_dict, combo_dict)
        personal_combat_msg(char2, char1, dmg_dict2, move_dict, combo_dict)
        apply_status(char1, "win", p_one_move, p_one_combo)
        apply_status(char2, "win", p_two_move, p_two_combo)
        check_special_status(char1, combat_handler)
        check_special_status(char2, combat_handler)
    # If winner is either p_one or p_two, calculate damage, 
    # bleed, positional points, and the like for the victim, 
    # then do combat ticks.
    if winner == "p_one":
        dmg_dict1 = calc_round_dam(char1, char2, move_dict, combo_dict)
        dmg_dict2 =  calc_round_dam(char2, char1, move_dict, combo_dict, False)
        break_weapon = calc_round_pos(char1, char2, dmg_dict1["weapon"], 
            None, move_dict, combo_dict, dmg_dict1, None, winner)
        string = combat_output(char1, p_one_move, p_one_combo,
            char1_attacking, dmg_dict1, char2, p_two_move, p_two_combo,
            char2_attacking, dmg_dict2, winner, break_weapon)
        combat_handler.msg_all(string, False)
        personal_combat_msg(char1, char2, dmg_dict1, move_dict, combo_dict)
        apply_status(char1, "win", p_one_move, p_one_combo)
        apply_status(char2, "lose", p_two_move, p_two_combo)
        check_special_status(char1, combat_handler, True)
        check_special_status(char2, combat_handler)
    if winner == "p_two":
        dmg_dict1 = calc_round_dam(char1, char2, move_dict, combo_dict, False)
        dmg_dict2 = calc_round_dam(char2, char1, move_dict, combo_dict)
        break_weapon = calc_round_pos(char1, char2, None, dmg_dict2["weapon"],
            move_dict, combo_dict, None, dmg_dict2, winner)
        string = combat_output(char1, p_one_move, p_one_combo,
            char1_attacking, dmg_dict1, char2, p_two_move, p_two_combo,
            char2_attacking, dmg_dict2, winner, break_weapon)
        combat_handler.msg_all(string, False)
        personal_combat_msg(char2, char1, dmg_dict2, move_dict, combo_dict)
        apply_status(char1, "lose", p_one_move, p_one_combo)
        apply_status(char2, "win", p_two_move, p_two_combo)
        check_special_status(char1, combat_handler)
        check_special_status(char2, combat_handler, True)

def apply_status(char, win_type, char_move, char_combo):
    """
    Applies any outstanding stats to the character based on status effects.
    """
    # force regen ticks
    if run_combat_tick(char, "health_regen", win_type, char_move, 
        char_combo) > 0:
        char.msg("Your wounds rapidly close.")
        tick = run_combat_tick(char, "health_regen", win_type, char_move, 
            char_combo)
        for i in range(0, tick):
            char.at_heal_tick()
    # add internal bleeding if applicable
    if run_combat_tick(char, "bleed", win_type, char_move, 
        char_combo) > 0:
        char.msg("You bleed internally.")
        char.add_wounds(None, 0, run_combat_tick(char, "bleed", win_type,
            char_move, char_combo), None)

def has_trait(char, obj):
    """
    Boolean method that determines whether the character in 
    question has the weapon/shield trait of the weapon argument.
    """
    if not obj:
        return
    if not obj.db.trait:
        return
    trait = obj.db.trait
    scripts = char.scripts.all()
    if char.scripts.get(trait):
        return True
    return

def check_break(att, vict, move_dict, combo_dict):
    """
    We need to check if the loser tried to use break
    on a successful attack vs. parry. If they did, we'll do break stuff.
    """
    att_move = move_dict[att.id]["move"]
    att_combo = combo_dict[att.id]
    vict_move = move_dict[vict.id]["move"]
    if vict_move.name in ("high parry", "low parry") and\
        att_move.move_type == "offensive" and att_combo.name == "break":
        return break_weapon(att, vict)
    return

def calc_round_pos(char1, char2, char1_weapon, char2_weapon, move_dict,
    combo_dict, dmg_dict1, dmg_dict2, winner):
    """
    Calculates the round position bonus based on character
    moves, and combos, and stat dicts.
    """
    pos1 = 0
    pos2 = 0
    char1_move = move_dict[char1.id]["move"]
    char2_move = move_dict[char2.id]["move"]
    char1_combo = combo_dict[char1.id]
    char2_combo = combo_dict[char2.id]
    win_char = None
    win_pos = 0
    lose_pos = 0
    break_weapon = None
    if winner == "both":
        # calculate bonus positional gains from moves
        pos1 += char1_move.bonus_pos
        pos2 += char2_move.bonus_pos
        # add bonus gains from combos
        pos1 += char1_combo.pos_att
        pos1 += char2_combo.pos_vict
        pos2 += char2_combo.pos_att
        pos2 += char1_combo.pos_vict
        # add bonus from status effects if any
        pos1 += run_combat_tick(char1, "pos_gain", "win", 
                char1_move, char1_combo)
        pos1 += run_combat_tick(char1, "pos_vuln", "win", 
                char1_move, char1_combo)
        pos2 += run_combat_tick(char2, "pos_gain", "win", 
                char2_move, char2_combo)
        pos2 += run_combat_tick(char2, "pos_vuln", "win", 
                char2_move, char2_combo)
        if dmg_dict1["crit"] and dmg_dict1["bodypart"]:
            pos2 += dmg_dict1["bodypart"].crit_bonus_pos
        if dmg_dict2["crit"] and dmg_dict2["bodypart"]:
            pos1 += dmg_dict2["bodypart"].crit_bonus_pos
        # offensive positional gain
        if has_trait(char1, char1_weapon):
            pos1 += OFFENSIVE_POS_GAIN
        if has_trait(char2, char2_weapon):
            pos2 += OFFENSIVE_POS_GAIN
        if char2_combo.no_pos:
            pos2 = 0
        if char1_combo.no_pos:
            pos1 = 0
        char1_combo_cost = char1_combo.pos_cost + \
                run_combat_tick(char1, "tech_pos_mod", "win", char1_move,
                char1_combo)
        char2_combo_cost = char2_combo.pos_cost + \
                run_combat_tick(char2, "tech_pos_mod", "win", char2_move,
                char2_combo)
    # null is easy, we just add any status effect pos bonuses
    # and call it a day
    elif winner == "null":
        pos1 += run_combat_tick(char1, "pos_gain", "null", 
                char1_move, char1_combo)
        pos2 += run_combat_tick(char2, "pos_gain", "null", 
                char2_move, char2_combo)
        char1_combo_cost = char1_combo.pos_cost + \
                run_combat_tick(char1, "tech_pos_mod", "lose", char1_move,
                char1_combo)
        char2_combo_cost = char2_combo.pos_cost + \
                run_combat_tick(char2, "tech_pos_mod", "lose", char2_move,
                char2_combo)
    # we do something else if the winner is either player
    # we set some variables to refer to each by
    elif winner == "p_one":
        win_char = char1
        lose_char = char2
        lose_combo = char2_combo
        lose_move = char2_move
        win_move = char1_move
        win_combo = char1_combo
        win_dmg_dict = dmg_dict1
        win_weapon = char1_weapon
        char1_combo_cost = char1_combo.pos_cost + \
                run_combat_tick(char1, "tech_pos_mod", "win", char1_move,
                char1_combo)
        char2_combo_cost = char2_combo.pos_cost + \
                run_combat_tick(char2, "tech_pos_mod", "lose", char2_move,
                char2_combo)
    elif winner == "p_two":
        win_char = char2
        lose_char = char1
        lose_combo = char1_combo
        lose_move = char1_move
        win_move = char2_move
        win_combo = char2_combo
        win_dmg_dict = dmg_dict2
        win_weapon = char2_weapon
        char1_combo_cost = char1_combo.pos_cost + \
                run_combat_tick(char1, "tech_pos_mod", "lose", char1_move,
                char1_combo)
        char2_combo_cost = char2_combo.pos_cost + \
                run_combat_tick(char2, "tech_pos_mod", "win", char2_move,
                char2_combo)
    # now the real logic starts if the eventuality was either player
    # this is done to prevent repeating the same section of code twice
    if win_char:
        trait = has_trait(win_char, win_weapon)
        #############################
        # OFFENSIVE/DEFENSIVE BONUSES
        #############################
        if win_move.move_type == "offensive":
            if trait:
                win_pos += OFFENSIVE_POS_GAIN
            else:
                win_pos += OFFENSIVE_POS_GAIN - NO_TRAIT_PENALTY
        else:
            # or it was defensive
            # add in shield possible bonuses
            for wielding in win_char.db.wielding.values():
                if wielding and \
                wielding.is_typeclass("game.gamesrc.combat.objects.armor.Shield") \
                and not wielding.db.broken:
                    shield = wielding
                    break
                else:
                    shield = None
            shield_bonus = 0
            if (shield and has_trait(win_char, shield) and
                win_move.name in ("high parry", "low parry")):
                shield_bonus = shield.db.quality + \
                        run_combat_tick(lose_char, "shield_q_mod", "lose",
                        lose_move, lose_combo) - 1
                if shield_bonus > 3:
                    shield_bonus = 3
            if trait:
                win_pos += DEFENSIVE_POS_GAIN + shield_bonus
            else: 
                win_pos += DEFENSIVE_POS_GAIN + shield_bonus - NO_TRAIT_PENALTY
        ###############################
        # OFFENSIVE/DEFENSIVE BONUS END
        ###############################
        win_pos += win_move.bonus_pos
        win_pos += win_combo.pos_att
        lose_pos += win_combo.pos_vict
        lose_pos += run_combat_tick(lose_char, "pos_gain", "lose", 
                lose_move, lose_combo)
        lose_pos += run_combat_tick(lose_char, "pos_vuln", "lose", 
                lose_move, lose_combo)
        if win_dmg_dict["crit"]:
            lose_pos += win_dmg_dict["bodypart"].crit_bonus_pos
            # get all the weapons the wielder is using
        weapons = [weapon for weapon in win_char.db.wielding.values() 
        if weapon and weapon.db.damage]
        highest_pos = -100 # default low amount to compare pos mods
        pos_mod = False
        # positional mods inherent to the weapon
        if weapons:
            for weapon in weapons:
                for (val, cond_move) in weapon.db.pos_mods.items():
                # cond_move is the string of the move that triggers 
                # the positional mod. We compare the vals to
                # the highest pos, which is -100 by default.
                # This means only the highest positional modifier will
                # apply.
                    if cond_move == "all" and highest_pos < val:
                        highest_pos = val
                        pos_mod = True
                    elif win_move in cond_move and highest_pos < val:
                        highest_pos = val
                        pos_mod = True
        if pos_mod:
            win_pos += highest_pos
        break_weapon = check_break(lose_char, win_char, move_dict, combo_dict)
        if break_weapon == "fail":
            win_pos = 0
        elif break_weapon:
            break_weapon.break_weapon()
        if win_combo.no_pos:
            win_pos = 0
        # set our values to the appropriate character based on our
        # calculations
        if win_char == char1:
            pos1 = win_pos
            pos2 = lose_pos
        else:
            pos2 = win_pos
            pos1 = lose_pos
    # if any status effects have enforced no positioning for the turn, 
    # then we set the positioning to 0 and call it a day
    for effect in char1.scripts.all():
        if effect.db.no_combat_position:
            pos1 = 0
            break
    for effect in char2.scripts.all():
        if effect.db.no_combat_position:
            pos2 = 0
            break
    # final calculations
    char1_final_pos = char1.ndb.pos + pos1 - char1_combo_cost
    char2_final_pos = char2.ndb.pos + pos2 - char2_combo_cost
    char1.set_pos(char1_final_pos)
    char2.set_pos(char2_final_pos)
    return break_weapon

def check_special_status(char, combat_handler, winner = None):
    """
    Checks whether the combatant was trying to rescue, flee, or shift targets
    at the time, and processes that accordingly with the round. 
    """
    RESCUE_COST = 2
    FLEE_COST = 3
    SHIFT_COST = 2
    scripts = char.scripts.all()
    dbref = char.id
    string = ""
    for script in scripts:
        if script.key == "flee":
            flee_counter = combat_handler.db.flee_count[dbref]
            if flee_counter > 1:
                if char.ndb.pos < 3:
                    string = "{RFLEE:{R {M%s{n doesn't have the footing" % \
                    (char.db.sdesc) + \
                    " to flee, and they are back in the thick of the battle!"
                    combat_handler.del_flee_char(char)
                else:
                    # subtract positioning
                    pos = char.ndb.pos - 3
                    char.set_pos(pos)
                    string = "{RFLEE:{n {M%s{n has" % (char.db.sdesc) + \
                        "successfully fled from combat!"
                    combat_handler.del_flee_char(char)
                    combat_handler.remove_character(char)
            else:
                string = "{RFLEE:{n {M%s{n is still" % (char.db.sdesc) + \
                        "trying to flee from combat!"
                combat_handler.add_flee_count(char)
        if script.key == "rescue":
            rescuee = combat_handler.db.rescue[dbref]
            attacker = combat_handler.db.pairs[rescuee]
            if winner:
                combat_handler.rescue_tgt(char, rescuee)
                string = "{RRESCUE:{n {M%s{n" % (rescuee.db.sdesc) + \
                    " has been rescued by {M%s{n!" % (char.db.sdesc) + \
                    " {M%s{n must now fight with {M%s{n." % \
                    (attacker.db.sdesc, char.db.sdesc)
            else:
                string = "{RRESCUE:{n {M%s{n has" % (char.db.sdesc) + \
                "failed to rescue {M%s{n from {M%s{n." % \
                (char.db.sdesc, rescuee.db.sdesc, attacker.db.sdesc)
                combat_handler.del_rescue(char)
            # subtract the positioning cost even if they fail
            # if they have the cowardice trait, they spend twice the
            # positioning
            if char.scripts.get("Cowardice"):
                RESCUE_COST *= 2
            elif char.scripts.get("Relentless Cunning"):
                RESCUE_COST = 0
            pos = char.ndb.pos - RESCUE_COST
            char.set_pos(pos) 
        if script.key == "shift target":
            if char.scripts.get("Relentless Cunning"):
                SHIFT_COST = 0
            # subtract positioning
            pos = char.ndb.pos - SHIFT_COST
            char.set_pos(pos)
            new_target = combat_handler.db.shifting[dbref]
            old_target = combat_handler.db.pairs[char]
            combat_handler.switch_target(char, new_target)
            string = "{M%s{n has successfully" % (char.db.sdesc) + \
                " shifted targets from {M%s{n to {M%s{n!" % \
                    (old_target.db.sdesc, new_target.db.sdesc)
        if string:
            combat_handler.msg_all(string)

def personal_combat_msg(char, vict, dmg_dict, move_dict, combo_dict):
    """
    Personalized combat messages to our players who take damage for the round.
    """
    type_to_string = {"edge":"cut", "blunt":"crush", "pierce":"piercing"}
    vict_string = ""
    char_string = ""
    char_move = move_dict[char.id]["move"]
    char_combo = combo_dict[char.id]
    if char_move.move_type != "offensive" and not char_combo.hard_dmg_range:
        return
    percentage = dmg_dict["dmg"] / vict.db.max_health
    if percentage > .40:
        dmg_str = "mortal"
    elif percentage > .30:
        dmg_str = "terrible"
    elif percentage > .20:
        dmg_str = "severe"
    elif percentage > .15:
        dmg_str = "moderate"
    elif percentage > .10:
        dmg_str = "minor"
    elif percentage > 0:
        dmg_str = "small"
    elif dmg_dict["bleed"] > 0:
        dmg_str = "bleeding"
    else:
        # if the damage was less than 0, and there was no bleed, there was no damage done.
        char_string = "Your blow skirts right off {M%s{n's armor," % \
        (vict.db.sdesc) + " doing no damage!" 
        vict_string = "The blow skirts right off your armor" + \
            " on your %s, protecting you from harm!" % (dmg_dict["bodypart"])
        char.msg(char_string)
        vict.msg(vict_string)
        return
    if dmg_dict["weapon"]:
        dmg_type = type_to_string[dmg_dict["weapon"].db.dmg_type]
    else:
        dmg_type = type_to_string["blunt"]
    vict_string += "You have taken a {R%s %s{n on the {C%s{n!" %\
                    (dmg_str, dmg_type, dmg_dict["bodypart"])
    char_string += "You have given {M%s{n a {R%s %s{n on the {C%s{n!" %\
                    (vict.db.sdesc, dmg_str, dmg_type, dmg_dict["bodypart"])
    if dmg_dict["crit"]:
        vict_string += " You've taken a critical blow!" 
        char_string += " You inflict a critical blow!"
    vict_string += "\n"
    char_string += "\n"
    char.msg(char_string)
    vict.msg(vict_string)

def calc_round_dam(char, vict, move_dict, combo_dict, winner=True):
    """
    calculates the damage dealt to an enemy based on
    the weapon and any quality mods, and the vict's
    armor/body parts.
    """
    # get all of our constants established
    damage_dict = {"weapon": None, "dmg":0, "dmg_type":None, 
                    "bleed":0, "bodypart": None, "crit_effect": None, 
                    "crit": False, "self_effect": {}, "vict_effect": {}}
    crit = False
    combat_handler = char.ndb.combat_handler
    # crit threshold reduction basically makes it easier to land a crit,
    # most often influenced by quality, but sometimes can come from mods.
    crit_threshold_reduction = 0
    # initialize our vict's armor class and armor vs. weapon type mod
    armor_class = 0
    armor_vs_mod = 0
    # initialize moves/combos
    char_move = move_dict[char.id]["move"]
    char_combo = combo_dict[char.id]
    vict_move = move_dict[vict.id]["move"]
    vict_combo = combo_dict[vict.id]
    # weapon checking and attributes
    char_weapons = [weapon for weapon in char.db.wielding.values() 
                if weapon and (weapon.db.damage and not weapon.db.broken)]
    if not any(char_weapons):
        char_weapon = None
    else:
        if len(char_weapons) > 1:
            char_weapon = random.choice(char_weapons)
        else:
            char_weapon = char_weapons[0]
    # if they're disarmed, they don't get to have a weapon
    if char.scripts.get("disarmed"):
        char_weapon = None
    # if we have a weapon, grab the information from the weapon itself
    if char_weapon:
        dmg_bonus = char_weapon.db.damage_bonus + run_combat_tick(att, 
            "weap_q_mod", win_type, att_move, att_combo)
        damage_dict["weapon"] = char_weapon
        damage_dict["dmg_type"] = char_weapon.db.dmg_type
        w_quality = char_weapon.db.quality + run_combat_tick(att, 
            "weap_q_mod", win_type, att_move, att_combo)
        broken = char_weapon.db.broken
        hands = char_weapon.db.hands
        weapon_min = char_weapon.db.damage[0] + dmg_bonus
        weapon_max = char_weapon.db.damage[1] + dmg_bonus
        crit_chance = char_weapon.db.crit_chance
    # if not, set some parameters so we can continue on 
    # with damage calculations. if you attack bare-handed, 
    # you'll never get a crit
    else:
        weapon_min = char.db.default_weapon["min"]
        weapon_max = char.db.default_weapon["max"]
        damage_dict["weapon"] = None
        damage_dict["dmg_type"] = char.db.default_weapon["type"]
        w_quality = char.db.default_weapon["quality"]
        dmg_bonus = char.db.default_weapon["dmg_bonus"]
        hands = char.db.default_weapon["hands"]
        crit_chance = char.db.default_weapon["crit"]
    if dmg_bonus > 3:
        dmg_bonus = 3
    # if the combo has a hard damage range, then we use the weapon_min/max and crit threshold reductions
    if char_combo.hard_dmg_range:
        weapon_min = char_combo.hard_dmg_range["min"]
        weapon_max = char_combo.hard_dmg_range["max"]
    # roll the damage and see if it's a crit
    # figure out what body parts we can even hit
    hit_list = []
    for parts in vict.db.body:
        if char_move in parts.hit_moves:
            hit_list.append(parts)
    if hit_list:
        body_part = random.choice(hit_list)
        damage_dict["bodypart"] = body_part
    # randomize the body part we hit
    # if it's a crit, the body part crit effect will take effect
    crit_percentage = random.randint(1, 100) / 100.0
    if (crit_percentage <= (crit_chance + char_combo.crit_chance)) and \
        hit_list:
        damage_dict["crit"] = True
        damage_dict["crit_effect"] = body_part.crit_effect
        damage_dict["dmg"] += body_part.crit_bonus_dmg
        damage_dict["bleed"] += body_part.crit_bonus_bleed
    if winner:
        win_type = "win"
    else:
        win_type = "lose"
    # adding damage bonuses from combos, from both the attacker and the vict
    #stat bonus from attacker stat dict
    damage_dict["dmg"] += run_combat_tick(att, "dam_gain", win_type, att_move,
        att_combo)
    # stat bonus from vict's stat dict
    damage_dict["dmg"] += run_combat_tick(vict, "dam_vuln", "lose", vict_move,
        vict_combo)
    # bleed bonus from vict's stat dict
    damage_dict["bleed"] += run_combat_tick(vict, "bleed_vuln", "lose",
        vict_move, vict_combo)
    # combo's vict bleed bonus
    damage_dict["bleed"] += char_combo.bleed_vict
    # bonus from attacker's combo dmg on vict
    damage_dict["dmg"] += char_combo.health_vict
    # bonuses from the victim's att attribute for combos
    damage_dict["dmg"] += vict_combo.health_att
    damage_dict["dmg"] += vict_combo.bleed_att
    dmg_roll = random.randint(weapon_min, weapon_max)
    damage_dict["dmg"] += dmg_roll
    # add bonus dmg/bleed from the character move
    damage_dict["dmg"] += char_move.bonus_dmg
    damage_dict["bleed"] += char_move.bonus_ble
    if damage_dict["crit"]:
        # crit multiplier is 1.5x
        damage_dict["dmg"] *= 1.50
    # final multiplier from combos
    damage_dict["dmg"] *= char_combo.dam_multiplier
    # multiplier from status effects from the attacker
    if run_combat_tick(att, "dam_multiplier", win_type,
            att_move, att_combo) > 0:
        damage_dict["dmg"] *= run_combat_tick(att, "dam_multiplier", win_type,
            att_move, att_combo)
    # multiplier from status effects from the victim
    if run_combat_tick(vict, "dam_vuln_multiplier", 
            "lose", vict_move, vict_combo) > 0:
        damage_dict["dmg"] *= run_combat_tick(vict, "dam_vuln_multiplier", 
            "lose", vict_move, vict_combo)
    # try seeing if the body_part we're trying to hit has armor
    try:
        char_armor = vict.db.equipped[body_part.name]["armor"]
        armor_type = char_armor.db.armor_type
        armor_class = run_combat_tick(vict, "armor_q_mod", "lose", vict_move,
            vict_combo) + char_armor.db.armor_class + char_armor.db.quality - 1
        if armor_class > (armor.ARMOR_TABLE[armor_type]["base_ac"] + 3):
            armor_class = armor.ARMOR_TABLE[armor_type]["base_ac"] + 3
        vs_class = "vs_%s" % (damage_dict["dmg_type"])
        armor_vs_mod = armor.ARMOR_TABLE[armor_type][vs_class]
    except:
        pass
    if winner:
        win_type = "win"
    else:
        win_type = "lose"
    # we see if any combo effects apply to either 
    # our attacker or vict 
    for (eff, parameters) in char_combo.combat_effect.items():
        if parameters["target"] == "vict" and \
            (win_type in parameters["win_cond"] or \
            parameters["win_cond"] == "all"):
            damage_dict["vict_effect"][eff] = parameters["repeats"]
        elif parameters["target"] == "att" and \
            (win_type in parameters["win_cond"] or \
            parameters["win_cond"] == "all"):
            damage_dict["self_effect"][eff] = parameters["repeats"]
        elif parameters["target"] == "both" and \
            (win_type in parameters["win_cond"] or \
            parameters["win_cond"] == "all"):
            damage_dict["vict_effect"][eff] = parameters["repeats"]
            damage_dict["self_effect"][eff] = parameters["repeats"]
    # Damage =[ [Damage Roll x Location Multiplier ] 
    # - AC ] +/x (Combo Details) Round Up on Damage
    if hit_list:
        damage_dict["dmg"] = round((damage_dict["dmg"] * \
            body_part.damage_multiplier) - (armor_class - armor_vs_mod), 0)
    # after all damage inflicted, we see if 
    # we need to apply any bleed multipliers based
    # on combo
    if damage_dict["dmg"] > 0:
        if char_combo.bleed_multiplier > 0:
            damage_dict["bleed"] += round(damage_dict["dmg"] * \
                        char_combo.bleed_multiplier, 0)
        if run_combat_tick(att,"bleed_multiplier", win_type, att_move,
            att_combo) > 0: 
            damage_dict["bleed"] += round(damage_dict["dmg"] * \
                        run_combat_tick(att,"bleed_multiplier", win_type,
                        att_move, att_combo), 0)
        if run_combat_tick(vict, "bleed_vuln_multiplier", "lose", vict_move,
            vict_combo) > 0:
            damage_dict["bleed"] += round(damage_dict["dmg"] * \
                run_combat_tick(vict, "bleed_vuln_multiplier", "lose",
                vict_move, vict_combo), 0)
    # we set the damage/bleed calculations to 0 if it was a defensive move
    # and the combo doesn't have any damage range in itself. 
    # If the winner was false, then no damage/bleed is applied either.
    if not winner or (char_move.move_type == "defensive" \
        and not char_combo.hard_dmg_range):
        damage_dict["dmg"] = 0
        damage_dict["bleed"] = 0
        damage_dict["crit"] = False
        damage_dict["bodypart"] = None
        damage_dict["crit_effect"] = None

    # if they have indomitable willpower, they get no damage reduction
    has_will = char.scripts.get("Indomitable Willpower")
    if not has_will:
        if (0.50 >= char.get_health_percent() >= 0.25):
            damage_dict["dmg"] = round(damage_dict["dmg"] * 0.8, 0)
        elif (char.get_health_percent() < 0.25):
            damage_dict["dmg"] = round(damage_dict["dmg"] * 0.6, 0)

    logger.log_infomsg("Made it to calculate damage. The damage done was: %s" % (damage_dict["dmg"]))
    # if the move is defensive and their combo doesn't have a hard dmg range, they don't actually attack.
    if damage_dict["dmg"] > 0 or damage_dict["bleed"] > 0:
        vict.add_wound(damage_dict["bodypart"], damage_dict["dmg"], 
                        damage_dict["bleed"], damage_dict["dmg_type"])
    # get a list of all effect multipliers for self, and victim
    self_eff_multi = {}
    vict_eff_multi = {}
    for script in char.scripts.all():
        if script.db.eff_multiplier:
            for (eff, parameter) in script.db.eff_multiplier.items():
                if parameter["target"] == "self" or \
                    parameter["target"] == "all":
                    if eff in self_eff_multi.keys():
                        self_eff_multi["eff"] += parameter["multiplier"]
                    else: 
                        self_eff_multi["eff"] = parameter["multiplier"]
    for script in vict.scripts.all():
        if script.db.eff_multiplier:
            for (eff, parameter) in script.db.eff_multiplier.items():
                if parameter["target"] == "vict" or \
                    parameter["target"] == "all":
                    if eff in vict_eff_multi.keys():
                        vict_eff_multi["eff"] += parameter["multiplier"]
                    else: 
                        vict_eff_multi["eff"] = parameter["multiplier"]

    # add status effects to the combat handler for application for next round
    if damage_dict["crit_effect"]:
        dur = damage_dict["bodypart"].get_repeats() * \
            vict_eff_multi.get(damage_dict["crit_effect"], 1.0)
        dur = round(dur, 0)
        combat_handler.add_status_effect(vict, damage_dict["crit_effect"], dur)
    if damage_dict["vict_effect"]:
        for (eff, duration) in damage_dict["vict_effect"].items():
            dur = duration * vict_eff_multi.get(eff, 1.0)
            dur = round(dur, 0)
            combat_handler.add_status_effect(vict, eff, dur)
    if damage_dict["self_effect"]:
        for (eff, duration) in damage_dict["self_effect"].items():
            dur = duration * self_eff_multi.get(eff, 1.0)
            dur = round(dur, 0)
            combat_handler.add_status_effect(char, eff, dur)
    logger.log_infomsg("Made it to the end of the damage calculations.")
    return damage_dict

def break_weapon(att, vict, count = 3):
    """
    Roll 2d[attacker positioning + 3(w/Brute Strength trait) + 
    weapon-size(1 for one-handed, 2 for two-handed) + quality bonus bonus(0-3)
    vs 
    3d[defender positioning + 3(w/Agile Defender traits for 1 and Shield
    Mastery for shields, always target shield is shield exists) + size (1 for
    one-handed, 2 for two-handed/shield) + quality (0-3)]
    """
    # in case we've tried to run for a tie at least three times recursively, we give up and call it
    # unsuccessful.
    if count < 1:
        return 0

    if att.scripts.get("Brute Strength"):
        brute_bonus = 3
    else:
        brute_bonus = 0
    for wielding in att.db.wielding.values():
        if isinstance(wielding, 
                (weapons.Axe, weapons.Mace, weapons.Greatsword)):
            att_weapon = wielding
        else:
            # this really shouldn't be happening, 
            # considering they need a viable weapon equipped
            # to even be able to do the combo ...
            return "fail"
    # 1 handed is 1, 2 handed is 2. If the value is 3,
    # the max value for the roll is 2.
    att_weapon_size = att_weapon.db.hands
    if att_weapon.db.hands > 2:
        att_weapon_size = 2
    att_dieface = att.db.pos + brute_bonus +\
                att_weapon_size + (att_weapon.db.size - 1)
    att_roll1 = random.randint(1, att_dieface)
    att_roll2 = random.rantint(1, att_dieface)
    attacker_roll = att_roll1 + att_roll2
    # figure out which weapon/shield we're trying to break.
    try:
        wielding = [weapon for weapon in 
                vict.db.wielding.values() if weapon.db.breakable]
        if wielding and len(wielding) > 1:
            vict_wielding = random.choice(wielding)
        elif wielding:
            vict_wielding = wielding[0]
        else:
            return "fail"
    except:
        return 
    # check if the defender has a shield
    for wielding in vict.db.wielding.values():
        if isinstance(wielding, ARMOR.Shield):
            shield = wielding
    # if they have the agile defener trait or 
    # shield mastery, we give them a +3 bonus
    if (shield and vict.scripts.get("Shield Mastery")) or\
        (vict.scripts.get("Expert Footwork")):
        def_bonus = 3
    else:
        def_bonus = 0
    if shield:
        shield = vict_wielding
        vict_wielding_size = 2
    else:
        vict_wielding_size = vict_wielding.db.hands
        if vict_wielding_size > 2:
            vict_wielding_size = 2
    vict_dieface = vict.db.pos + def_bonus +\
                vict_wielding_size + (vict_wielding.db.quality - 1)
    vict_roll1 = random.randint(1, vict_dieface)
    vict_roll2 = random.randint(1, vict_dieface)
    vict_roll3 = random.randint(1, vict_dieface)
    victim_roll = vict_roll1 + vict_roll2 + vict_roll3
    if attacker_roll > victim_roll:
        vict_wielding.break_weapon()
        return vict_wielding
    elif victim_roll > attacker_roll:
        return "fail" 
    # if it's a tie, we recursively run the function again
    else:
        return break_weapon(att, vict, count - 1)

def pairify(pairs):
    """
    Assembles the given pairs into proper match-ups
    """
    parsed_pairs = []
    for (att, vict) in pairs.items():
        parsed_pair = (att, vict)
        parsed_pair = sorted(parsed_pair)
        if parsed_pair not in parsed_pairs:
            parsed_pairs.append(parsed_pair)
    return parsed_pairs

def run_combat_tick(char, stat, win_cond, move, combo):
    stat_val = 0
    for script in char.scripts.all():
        if script.db.is_status_effect or script.db.is_trait:
            stat_val += script.get_combat_stat(stat, win_cond, move, combo)
    return stat_val

def combat_output(p_one, move_one, combo_one, p_one_attacking, dmg_dict1, 
        p_two, move_two, combo_two, p_two_attacking, dmg_dict2, winner,
        break_weapon = None):
    """
    Generates output for each pair given their moves and combos and
    the winner (p_one, p_two, both, or null)
    """
    string = "\n"
    # swap it around so p_one is always the attacker
    # we use some placeholder variables to hold important
    # stuff until we swap it over
    if not p_one_attacking:
        p_one_attacking = True
        p_two_attacking = False
        dummy_p = p_two
        dummy_move = move_two
        dummy_combo = combo_two
        dummy_dict = dmg_dict2
        p_two = p_one
        move_two = move_one
        combo_two = combo_one
        dmg_dict2 = dmg_dict1
        p_one = dummy_p
        move_one = dummy_move
        combo_one = dummy_combo
        dmg_dict1 = dummy_dict

    p_one_weapon = None
    p_two_weapon = None

    if dmg_dict1 and dmg_dict1["weapon"]:
        p_one_weapon = dmg_dict1["weapon"]
    if dmg_dict2 and dmg_dict2["weapon"]:
        p_two_weapon = dmg_dict2["weapon"]

    if p_one_weapon:
        p_one_weapon = p_one_weapon.db.weapon_type
        p_one_wrapper = p_one_weapon.db.move_wrapper
    else:
        p_one_weapon = p_one.db.default_weapon["name"]
        p_one_wrapper = p_one.db.move_wrapper

    if p_two_weapon:
        p_two_weapon = p_two_weapon.db.weapon_type
        p_two_wrapper = p_two_weapon.db.move_wrapper
    else:
        p_two_weapon = p_two.db.default_weapon["name"]
        p_two_wrapper = p_two.db.move_wrapper

    for wrap_move in p_one_wrapper:
        if move_one == wrap_move.move_name:
            wrapper_move_one = wrap_move
            break

    for wrap_move in p_two_wrapper:
        if move_two == wrap_move.move_name:
            wrapper_move_two = wrap_move
            break
            
    if combo_one.name:
        string += "%s, " % (combo_one.suffix_str)
        string += "{M%s{n " % (p_one.db.sdesc)
    else:
        string += "{M%s{n " % (p_one.db.sdesc.capitalize())

    string += "%s" % (wrapper_move_one.active_str)
    if move_one.name not in ("dodge", "duck", "pass"):
        string += " with their %s, " % (p_one_weapon)
    else:
        string += ", "
    string = combat_str_replace(p_one, p_two, p_one_weapon, p_two_weapon,
                                string, None)
    if p_two_attacking:
        string += "while {M%s{n " % (p_two.db.sdesc) 
        if combo_two.name:
            string += "%s, " % (combo_two.active_str)
            string += "%s" % (wrapper_move_two.suffix_str)
        else:
            string += "%s" % (wrapper_move_two.active_str)
        if move_two.name not in ("dodge", "duck", "pass"):
            string += " with their %s. " % (p_two_weapon)
        else:
            string += ". "
        string = combat_str_replace(p_two, p_one, p_two_weapon,
                                        p_one_weapon, string,
                                        None)
    if winner == "both":
        string += "And so, {M%s{n " % (p_one.db.sdesc)
        if combo_one.name:
            string += "%s! " % (combo_one.win_str)
        else:
            string += "%s" % (wrapper_move_one.find_win_move(move_two))
            string += ". "
        string = combat_str_replace(p_one, p_two, p_one_weapon, p_two_weapon,
                                    string, dmg_dict1["bodypart"])
        string += "But, {M%s{n " % (p_two.db.sdesc)
        if combo_two.name:
            string += "%s!" % (combo_two.win_str)
        else:
            string += "%s" % (wrapper_move_two.find_win_move(move_one))
        string = combat_str_replace(p_two, p_one, p_two_weapon, p_one_weapon,
                                     string, dmg_dict2["bodypart"])
    elif winner == "p_one":
        if not p_two_attacking:
            string += "and "
        else:
            string += "So, {M%s{n " % (p_one.db.sdesc)
        if combo_one.name:
            if break_weapon:
                string += "%s" % (combo_one.win_str["success"])
            elif isinstance(combo_one, combo.Break):
                string += "%s" % (combo_one.win_str["fail"])
            else:
                string += "%s" % (combo_one.win_str)
        else:
            string += "%s" % (wrapper_move_one.find_win_move(move_two))
        if dmg_dict1["bodypart"]:
            string = combat_str_replace(p_one, p_two, p_one_weapon,
                                        p_two_weapon, string,
                                        dmg_dict1["bodypart"])
        else:
            string = combat_str_replace(p_one, p_two, p_one_weapon,
                                        p_two_weapon, string, None)
    elif winner == "p_two":
        string += "So, {M%s{n " % (p_two.db.sdesc)
        if combo_two.name:
            if break_weapon:
                string += "%s" % (combo_two.win_str["success"])
            elif isinstance(combo_two, combo.Break):
                string += "%s" % (combo_two.win_str["fail"])
            else:
                string += "%s" % (combo_two.win_str)
        else:
            string += "%s" % (wrapper_move_two.find_win_move(move_one))
        if dmg_dict2["bodypart"]:
            string = combat_str_replace(p_two, p_one, p_two_weapon,
                                        p_one_weapon, string,
                                        dmg_dict2["bodypart"])
        else:
            string = combat_str_replace(p_two, p_one, p_two_weapon,
                                        p_one_weapon, string, None)
    elif winner == "null":
        if not p_two_attacking:
            if move_two.move_type == "offensive" and \
                move_one.move_type == "defensive":
                string += "but misses {M%s{n" % (p_two.db.sdesc)
            else:
                string += "but gains no advantage over {M%s{n" % \
                    (p_two.db.sdesc)
        else:
            string += wrapper_move_one.find_null_move(move_two).capitalize()
    if string[-1] not in ".!":
        string += "."
    string += "\n"
    """
    # status effect stuff
    if dmg_dict1 and dmg_dict1["self_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_one.db.sdesc.capitalize(), 
            STATUS_STORAGE.get_attr(dmg_dict1["self_effect"], "effect_str"))
    if dmg_dict1 and dmg_dict1["crit_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_two.db.sdesc.capitalize(), 
             STATUS_STORAGE.get_attr(dmg_dict1["crit_effect"], "effect_str"))
    if dmg_dict1 and dmg_dict1["vict_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_two.db.sdesc.capitalize(), 
            STATUS_STORAGE.get_attr(dmg_dict1["vict_effect"], "effect_str"))
    string = combat_str_replace(p_one, p_two, p_one_weapon,
                                p_two_weapon, string, None)
    if dmg_dict2 and dmg_dict2["self_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_two.db.sdesc.capitalize(), 
            STATUS_STORAGE.get_attr(dmg_dict2["self_effect"], "effect_str"))
    if dmg_dict2 and dmg_dict2["crit_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_one.db.sdesc.capitalize(), 
            STATUS_STORAGE.get_attr(dmg_dict2["crit_effect"], "effect_str"))
    if dmg_dict2 and dmg_dict2["vict_effect"]:
        string += "\n{M%s{n %s!\n" % \
            (p_one.db.sdesc.capitalize(), 
            STATUS_STORAGE.get_attr(dmg_dict2["vict_effect"], "effect_str"))
    """
    string = combat_str_replace(p_two, p_one, p_two_weapon,
                                p_one_weapon, string, None)
    string += "\n"
    return string

def combat_str_replace(att, vict, att_weapon, vict_weapon, string,
                        vict_body = None):
    """
    Replaces the tokens in our combat output string with the appropriate
    string.

    $o - p_two's sdesc
    $go - p_two's gender
    $s - p_one's sdesc
    $gs - p_one's gender
    $ws - p_one's weapon 
    $wo - p_two's weapon
    $bo - p_two's body part
    """
    string = string.replace("$ws", att_weapon)
    string = string.replace("$wo", vict_weapon)
    string = string.replace("$gs", "{M" + att.genderize_str() + "{n")
    string = string.replace("$go", "{M" + vict.genderize_str() + "{n")
    string = string.replace("$o", "{M" + vict.db.sdesc + "{n")
    string = string.replace("$s", "{M" + att.db.sdesc + "{n")
    string = string.replace("$ps", "{M" + att.genderize_str(2) + "{n")
    string = string.replace("$po", "{M" + vict.genderize_str(2) + "{n")
    if vict_body:
        string = string.replace("$bo", vict_body.singular_name)
    return string

def determine_outcome(p_one, move_one, combo_one, p_one_attacking,
                        p_two, move_two, combo_two, p_two_attacking):
    """
    Based on the combos and moves, it returns who wins. 

    p_one or p_two, or both as a string.
    """
    if move_two in move_one.win_list and move_one in move_two.win_list:
        winner = "both"
        win_type = move_one.move_type
        lose_type = move_two.move_type
    elif move_one in move_two.win_list:
        winner = "p_two"
        win_type = move_two.move_type
        lose_type = move_one.move_type
    elif move_two in move_one.win_list:
        winner = "p_one"
        win_type = move_one.move_type
        lose_type = move_two.move_type
    else:
        winner = "null"
    try:
    # Oh shucks, we gotta figure out if feint reverses any wins. In short,
    # feint reverses a win if it's a failed attack vs. 
    # defense. The feinter instead will win the round. If it's 
    # attack vs. attack, only the non-feinter wins.

    # If it's attack vs. attack and both players feinted, nobody wins.

    # We first check if both players feinted and reported both winning.
    # This results in a null.
        if (combo_one.name == "feint") and\
            (combo_two.name == "feint") and\
            (winner == "both"):
            winner = "null"
        # If player two feinted on a failed attack 
        # vs. defense, then feint kicks in,
        # and player two wins!
        elif (combo_two.name == "feint") and\
            (win_type == "defensive") and\
            (lose_type == "offensive") and\
            (winner == "p_one"):
            winner = "p_two"
        # if both players went offensive and one of the 
        # players performed a feint (and won initially), 
        # it's a null
        elif (combo_one.name == "feint") and\
            (win_type == "offensive") and\
            (lose_type == "offensive") and\
            (winner == "p_one"):
            winner = "null"
        elif (combo_two.name == "feint") and\
            (win_type == "offensive") and\
            (lose_type == "offensive") and\
            (winner == "p_two"):
            winner = "null"   
        # If player one feinted on a failed attack vs. 
        # defense, then feint kicks in, and player one wins!
        elif (combo_one.name == "feint") and\
            (win_type == "defensive") and\
            (lose_type == "offensive") and\
            (winner == "p_two"):
            winner = "p_one"
        # if p_one wins with an offensive feint, the exchange 
        # is actually a null
        elif (combo_one.name == "feint") and\
             (win_type == "offensive") and\
             (lose_type == "defensive") and\
             (winner == "p_one"):
             winner = "null"
        # if p_two wins with an offensive feint, the exchange
        # is actually a null
        elif (combo_two.name == "feint") and\
             (win_type == "offensive") and\
             (lose_type == "defensive") and\
             (winner == "p_two"):
             winner = "null"
        # If player one feinted, and both won, then only p_two actually scores.
        elif (combo_one.name == "feint") and\
            (winner == "both"):
            winner = "p_two"
        # If player two feinted, and both won, then only p_one actually scores.
        elif (combo_two.name == "feint") and\
            (winner == "both"):
            winner = "p_one"
    except:
        pass
        ### END FEINT STUFF
    # If the winner's player two, but they're not attacking, it's still a null.
    if winner == "p_two" and\
        not p_two_attacking:
        winner = "null"
    # If the winner's player one, but they're not attacking, it's still a null.
    if winner == "p_one" and\
        not p_one_attacking:
        winner = "null"
    # special clause for players that both do the 
    # same combo in a round. Whoever has the higher
    # positional points wins the exchange. If they 
    # have the same positioning, nobody wins.
    if (winner == "both") and\
        (combo_one.name == combo_two.name):
        if p_one.ndb.pos > p_two.ndb.pos:
            winner == "p_one"
        elif p_two.ndb.pos > p_one.ndb.pos:
            winner == "p_two"
        else:
            winner == "null"
    return winner