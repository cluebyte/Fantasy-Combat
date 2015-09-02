from ev import CmdSet
from CmdCombat import CmdFlee, CmdCombatRescue, CmdCombatStrike, CmdCombatMove
from CmdCombat import CmdStopCombat, CmdLongswordCombo, CmdAxeCombo, CmdMaceCombo
from CmdCombat import CmdGreatswordCombo, CmdStaveCombo, CmdDaggerCombo, CmdSpearCombo
from CmdCombat import CmdShieldCombo
"""
Command sets for all of our combat commands. Each weapon gets its own combo
command set.
"""
class CmdSetCombat(CmdSet):
    key = "CmdSetCombat"
    locks = "cmd:attr(combat_handler)"
    
    def at_cmdset_creation(self):
        self.add(CmdFlee())
        self.add(CmdCombatRescue())
        self.add(CmdCombatStrike())
        self.add(CmdCombatMove())
        self.add(CmdStopCombat())

class CmdSetLongsword(CmdSet):
    key = "CmdSetLongsword"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdLongswordCombo())

class CmdSetAxe(CmdSet):
    key = "CmdSetAxe"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdAxeCombo())

class CmdSetMace(CmdSet):
    key = "MaceCmdSet"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdMaceCombo())

class CmdSetGreatsword(CmdSet):
    key = "CmdSetGreatsword"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdGreatswordCombo())

class CmdSetStave(CmdSet):
    key = "CmdSetStave"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdStaveCombo())

class CmdSetDagger(CmdSet):
    key = "CmdSetDagger"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdDaggerCombo())

class CmdSetSpear(CmdSet):
    key = "CmdSetSpear"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdSpearCombo())

class CmdSetShield(CmdSet):
    key = "CmdSetShield"
    locks = "cmd:attr(combat_handler)"
    def at_cmdset_creation(self):
        self.add(CmdShieldCombo())