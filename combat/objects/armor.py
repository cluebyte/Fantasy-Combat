from game.gamesrc.objects.object import Object

# armor table for each armor type, with their innate weaknesses/strengths against edge, blunt, or pierce.
# also holds information on magic/ele resists
			  # makeshift
ARMOR_TABLE = {"makeshift": {"base_ac":1,"vs_edge":0, "vs_blunt":0, "vs_pierce":-1, "ele_resist": 0.0, "magic_resist":0.0,\
			  "base_wt": 500, "wt_multiplier": 100},\
			  # leather
			   "leather": {"base_ac":1, "vs_edge":0, "vs_blunt":1, "vs_pierce":0, "ele_resist": 30.0, "magic_resist":10.0,\
			   "base_wt":1000, "wt_multiplier": 200},\
			  # maille
			   "maille": {"base_ac":2, "vs_edge":1, "vs_blunt":1, "vs_pierce":0, "ele_resist": 15.0, "magic_resist":25.0,\
			   "base_wt": 1250, "wt_multiplier": 250},\
			  # plate
			   "plate":{"base_ac":3, "vs_edge":1, "vs_blunt":0, "vs_pierce":1, "ele_resist": 10.0, "magic_resist":30.0,\
			   "base_wt":1500, "wt_multiplier": 500}}

# weight multipliers for wearlocs

WEIGHT_TABLE = {"head":2, "torso":6, "arms":2, "legs":4, "feet":1, "hands":1}

class Armor(Object):
	"""
	Armor objects that can be worn in-game over a wear location to provide protection.

	The following are unique attributes associated with armor:

	armor_type (string) - makeshift, leather, maille, or plate. See ARMOR_TABLE for strengths/weaknesses.
	armor_class (int) - how much the armor mitigates damage, each armor type has a base AC for poor quality. 
						quality makes AC +1 for each tier.
	weight (float) - weight in pounds of the armor. each armor type has a different weight multiplier, as well as
					 wearloc.
	quality (int) - integer number. 1-4. 1 - poor, 2- ordinary, 3- good, 4-magic
	wearloc (string) - wearloc of the armor. String needs to match a viable body part location.
	elemental_resist (float) - elemental resist reduction value
	magic_resist (float) - magic resist reduction value
	skill_effects (list) - list of string skill effects that this armor applies on_wear
	status_effects (list) - list of string status effect keys that this armor applies on_wear
	"""
	def at_object_creation(self):
		# these values will be determined by prototypes.
		self.db.quality = 0
		self.db.armor_type = "makeshift"
		self.db.armor_class = ARMOR_TABLE[self.db.armor_type]["base_ac"] + (self.db.quality - 1)
		self.db.wearloc = "head"
		# weight = base_weight * ((quality - 1) * weight_multiplier) * wearloc_weight_multiplier
		self.db.weight = ARMOR_TABLE[self.db.armor_type]["base_wt"] +\
						((self.db.quality - 1) * ARMOR_TABLE[self.db.armor_type]["wt_multiplier"]) *\
						WEIGHT_TABLE[self.db.wearloc]
		self.db.elemental_resist = ARMOR_TABLE[self.db.armor_type]["ele_resist"]
		self.db.magic_resist = ARMOR_TABLE[self.db.armor_type]["magic_resist"]
		self.db.skill_effects = None
		self.db.status_effects = None
		self.db.desc = "This is an armor prototype that shouldn't be loaded."
		self.db.sdesc = "an armor prototype"
		self.db.ldesc = "An armor prototype is here."
		super(Armor, self).at_object_creation()
		
	def at_wear(self, caller):
		# hook on scripts
		for effect in self.db.status_effects:
			caller.scripts.add(effect)
	def at_remove(self):
		# hook on scripts
		for effect in self.db.status_effects:
			caller.scripts.stop(effect)

class Shield(Object):
	"""
	Shield object that can be wielded in the main or off hand to provide protection.
	"""

	def at_object_creation(self):
		self.db.quality = 1
		self.db.desc = "This is a shield prototype tha shouldn't be loaded."
		self.db.sdesc = "a shield prototype"
		self.db.ldesc = "A shield prototype is here."
		self.db.skill_effects = None
		self.db.status_effects = None
		self.db.magic_resist = .05 * self.db.quality
		self.db.elemental_resist = .05 * self.db.quality
		self.db.hands = 1
		self.db.dual_wield = "both"
		self.db.trait = "ShieldMasteryTrait"

	def at_wield(self, caller):
		"""
		for effect in status_effects:
			obj = self.location
			obj.scripts.add(effect)
		"""
		scripts = caller.scripts.all()
		if caller.scripts.get(self.db.trait):
			caller.cmdset.add("CmdSetCombat.CmdSetShield")

	def at_remove(self, caller):
		"""
		# hook on scripts
		for effect in status_effects:
			obj = self.location
			obj.scripts.stop(effect)
		"""
		scripts = caller.scripts.all()
		if caller.scripts.get(self.db.trait):
			caller.cmdset.delete("CmdSetCombat.CmdSetShield")