from pokedex import Pokedex
from pokemon import Pokemon

class PokemonTeam:

    # the initialization method
    def __init__(self):
        
        # for this class we will initilize with an empty team roster
        self.roster : list[Pokemon] = []

        # we will also initialize a pokedex once so we can grab pokemon from it as needed
        self.pokedex = Pokedex()

    # the pretty representation of the team
    def __repr__(self) -> str:
        
        # If the team hasn't been built yet:
        if len(self.roster) == 0:
            return "an empty Pokemon team!"

        repl_string = "a pokemon team consisting of: "
        for i, pokemon in enumerate(self.roster):
            if i < len(self.roster) - 2:
                repl_string += f"{pokemon.name}, " # trailing commas from first name up to second last
            elif i == len(self.roster) - 1:
                repl_string += f"{pokemon.name}." # the last item has a period afterwards
            else:
                repl_string += f"{pokemon.name}, and " # the second last name has and
        return repl_string
    
    # PUBLIC METHODS ==================================================================================

    # gather a randomized team - for the computer
    def get_random_team(self, num_pokemon:int) -> None:
        """Populates .roster with a bunch of pokemon

        Args:
            num_pokemon (int): The number of pokemon on the team.
        """

        roster_list = [] # initialize an empty list

        # loop for n times
        for i in range(num_pokemon):
            roster_list.append(self.pokedex.choose_random())

        self.roster = roster_list


    # gather a user chosen team - chosen by user input

    def get_chosen_team(self, num_pokemon:int) -> None:
        """Populates .roster with a bunch of user chosen pokemon

        Args:
            num_pokemon (int): The number of pokemon on the team
        """

        roster_list = [] # initialize an empty list

        for i in range(num_pokemon):
            user_choice = input(f"Choose pokemon #{i}")
            roster_list.append(self.pokedex.choose_pokemon(user_choice))
        
        self.roster = roster_list