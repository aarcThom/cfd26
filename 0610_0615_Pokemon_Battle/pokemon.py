import random

class Pokemon:
    
    # the initialization method - called when a new object is constructed
    # when you have a lot of parameters, it is usually more readable to break
    # them up into single lines like so
    def __init__(self, 
                 name:str, 
                 dex_num:int, 
                 t1:str, 
                 t2:str,
                 attack:int,
                 defense:int, 
                 hp:int,
                 abilities:list[str],
                 against_ratio: dict[str, float]
                 ) -> None:
        
        """Initialize a new Pokemon

        Args:
            name (str): The pokemon name
            dex_num (int): The pokedex number
            t1 (str): Type 1
            t2 (str): Type 2
            attack (int): The strength of the attack
            defense (int): The defense strength
            hp (int): How many hitpoints the Pokemon has.
            abilities (list[str]): The names of the attacks.
            against_ratio (dict): The relative strength against other pokemon types
        """

        # now we assign the passed into values to the instances attributes
        self.name = name
        self.dex_num = dex_num
        self.type1 = t1
        self.type2 = t2
        self.attack = attack
        self.defense = defense
        self.hp = hp
        self._max_hp = hp # remember we need to keep track of the pokemon's max hp
        self.abilities = abilities
        self.against_ratio = against_ratio

    # DUNDER METHODS ----------------------------------------------------------------------
    # using this to give us a pretty representation when testing
    def __repr__(self) -> str:
        return f"{self.name}"

    # METHODS -----------------------------------------------------------------------------
    # We can now define the actions that the pokemon take

    def attack_opponent(self, opponent:Pokemon) -> tuple[str, int]:
        """Attack an opponent. Applies type multiplier to determine damage dealt.

        Args:
            opponent (Pokemon): The Pokemon to attack

        Returns:
        
            tuple[str, int]: The attack name and the amount of damage dealt.
        """
        # we get a multiplier for the attack -------------------------------------

        attack_multiplier = 1 # the baseline multiplier

        # we iterate through the opponent types
        for oppo_type in [opponent.type1, opponent.type2]:
            
            # we need to check if the type is in the dictionary.
            # some pokemon have None as their second type - ie. only have 1 type
            if oppo_type in self.against_ratio:
                attack_multiplier *= self.against_ratio[oppo_type] # multiply by the type
        
        # now we multiply the multiplier by the attack amount
        final_attack = attack_multiplier * self.attack

        # we choose a random multiplier amount to determine how effective the opponent defense is
        defense_multiplier = random.uniform(0.5, 1.0)
        final_defense = defense_multiplier * opponent.defense

        # now we figure out how much damage was assigned and round it to an int
        damage_dealt = int(final_attack - final_defense)
        if damage_dealt < 0:
            damage_dealt = 0 # need to make sure we don't have negative attacks
        
        # randomly choose the attack name
        attack_name = random.choice(self.abilities)

        # return the attackname and damage dealt
        return attack_name, damage_dealt
        