from pokemon import Pokemon # we need to import our pokemon class into this file

import json # remember we need to import the json library to import our data
import difflib # we can use difflib to grab the closest match to a user input
import random # we can use random to pick a random pokemon for the opponent

class Pokedex:

    # the initialization method (aka the constructor)
    def __init__(self) -> None:
        """Initialize the pokedex. Imports in all data from pokemon file.
        """

        # instead of passing in arguments to populate our attributes, we can
        # populate our attributes programmatically in the constructor\
        # we we will define some private helper functions to keep our code clean

        json_dictionary = self._load_poke_dict("data/pokemon.json") # get the pokemon dictionary from json
        self.pokedex = self._get_pokemon_objects(json_dictionary) # get the actual pokemon objects
    

    # PUBLIC METHODS --------------------------------------------------------------------

    def choose_pokemon(self, choice:str) -> Pokemon:
        """ Uses difflib to return the closest matching pokemon

        Args:
            choice (str): The pokemon to pick

        Returns:
            Pokemon: The pokemon object with that name (or close).
        """
        choice_formatted = choice.lower() # make sure the input is all lowercase

        all_names = self.pokedex.keys() # grab all keys (pokemon names) in the dictionary

        # use difflib to grab the closest match, just in case there was a typo
        closest_match = difflib.get_close_matches(choice_formatted, all_names, n = 1)
        chosen_pokemon = self.pokedex[closest_match[0]] # we grab the only object in the list

        return chosen_pokemon
    
    def choose_random(self) -> Pokemon:
        """pick a random pokemon from the pokedex

        Returns:
            Pokemon: The pokemon object.
        """

        random_name = random.choice(list(self.pokedex.keys())) # we can cast sequence as list to avoid error
        random_mon = self.pokedex[random_name] # grab the actual Pokemon object

        return random_mon



    # PRIVATE HELPER METHODS ------------------------------------------------------------

    def _load_poke_dict(self, path:str) -> dict:
        """Load the pokemon dictionary from the JSON file.

        Args:
            path (str): The path to the pokemon JSON file

        Returns:
            dict: The pokemon dictionary
        """

        with open(path, mode='r', encoding="utf-8") as context_manager:
            pokemon_dict = json.load(context_manager)
        return pokemon_dict
    


    def _get_pokemon_objects(self, poke_dict:dict) -> dict[str, Pokemon]:
        """Return a dictionary of pokemon objects. Keys are pokemon names. value is obj.

        Args:
            poke_dict (dict): The pokemon dictionary imported from JSON.

        Returns:
            dict[str, Pokemon]: Dictionary - Key = Name, Value = Pokemon Object
        """
        # create a new, empty dictionary that we will return
        obj_dict = {}

        # iterate through the Pokemon entries in the dictionary
        for poke_key in poke_dict:
            name = poke_key # the key is the name
            
            # the associated value is yet another dict, so let's split it out
            poke_stats = poke_dict[poke_key]

            # now we can start grabbing the stats
            poke_num = poke_stats["pokedex_number"]
            type1 = poke_stats["type1"]
            type2 = poke_stats["type2"]
            attack = poke_stats["attack"]
            defense = poke_stats["defense"]
            hp = poke_stats["hp"]
            abilities = poke_stats["abilities"] # this is a list of strings

            # we will now write yet another helper function since this is a little more involved - see _get_ratios() below
            ratio_dict = self._get_ratios(poke_stats)

            # we can now populate the pokemon object!
            pokemon_object = Pokemon(
                name = name,
                dex_num = poke_num,
                t1 = type1,
                t2 = type2,
                attack = attack,
                defense = defense,
                hp = hp,
                abilities = abilities,
                against_ratio = ratio_dict
            )

            # now let's append it to the object dictionary
            obj_dict[name] = pokemon_object
        
        # return the final dictionary
        return obj_dict





    def _get_ratios(self, dict_in:dict) -> dict[str, float]:
        """Get the properly formatted pokemon ratio dictionary
            We need to strip the 'against_' from the inputs

        Args:
            dict_in (dict): the pokemon stats dictionary from the JSON

        Returns:
            dict[str, float]: a cleaned ratio dictionary
        """
        
        # create the empty output dictionary
        ratio_dict_out = {}

        for key in dict_in:
            # testing if the key starts with 'against_'
            if key.startswith("against_"):
                formatted_key = key.removeprefix("against_") # remove the 'against_'
                ratio_dict_out[formatted_key] = dict_in[key] # append the float value to the formatted key
        
        return ratio_dict_out