from pokemon_team import PokemonTeam
import random # used for the coin flip
from pokemon import Pokemon

class PokemonBattle:
    
    # the initialization method (constructor)
    def __init__(self) -> None:
        self.human_team : PokemonTeam = PokemonTeam() # unpopulated team
        self.oppo_team : PokemonTeam = PokemonTeam() # unpopulated team

        self.human_current : Pokemon # the current pokemon battling for you
        self.oppo_current : Pokemon # the current pokemon battling for the computer

        self.current_turn = False # whose turn it is - False = computer, True = human

        self.battle_done = False # set to be True when a roster is empty

        self.turn_count = 0 # we need to set this to make sure an unwinnable battle doesn't go forever

    # PUBLIC METH0DS --------------------------------------------------------
    def choose_oppo_team(self, num_pokemon:int) -> tuple[str, list[str]]:
        """Populates .oppo_team with n pokemon.

        Args:
            num_pokemon (int): Number of pokemon on the team

        Returns:
            tuple[str, list[str]]: Message to pass to GUI, list of img paths to pass to the GUI
        """
        
        # populate the opponent's team with n pokemon
        self.oppo_team.get_random_team(num_pokemon)

        # generate the message
        message = f"Your opponent iggy, called up {self.oppo_team}"

        # get the images
        img_list = []
        for pokemon in self.oppo_team.roster:
            img_path = f"data/img/{pokemon.name}.jpg"
            img_list.append(img_path)
        

        # set the current pokemon and remove from the roster
        self.oppo_current = self.oppo_team.roster.pop(0)

        # return the values
        return message, img_list
    
    def choose_your_team(self, num_pokemon:int) -> tuple[str, list[str]]:
        """Populates .human_team with n pokemon.

        Args:
            num_pokemon (int): Number of pokemon on the team

        Returns:
            tuple[str, list[str]]: Message to pass to GUI, list of img paths to pass to the GUI
        """
        
        # populate the opponent's team with n pokemon
        self.human_team.get_chosen_team(num_pokemon)

        # generate the message
        message = f"You called up {self.human_team}"

        # get the images
        img_list = []
        for pokemon in self.human_team.roster:
            img_path = f"data/img/{pokemon.name}.jpg"
            img_list.append(img_path)

        # set the current battling pokemon and remove from roster
        self.human_current = self.human_team.roster.pop(0)
        
        # return the values
        return message, img_list
    

    def battle_turn(self) -> tuple[str, bool]:
        """Has one current pokemon attack the other. Applies damage and present's message and faint bool to GUI

        Returns:
            tuple[str, bool]: The message description. Bool set to true if pokemon was knocked out.
        """

        # set the pokemon fainted status to False by default
        pokemon_fainted = False

        # figure out whose turn it is
        if self.current_turn: # ie. it's the human's turn
            attacker  = self.human_current
            defender = self.oppo_current
            defend_team = self.oppo_team
        else:
            attacker = self.oppo_current
            defender = self.human_current
            defend_team = self.human_team
        
        # calculate the damage
        attack_name, damage_dealt = attacker.attack_opponent(defender)

        # create the message
        message = f"{attacker.name} attacked with {attack_name}!\n"
        if damage_dealt == 0:
            message += "It had no effect!\n"
        elif damage_dealt <= defender.hp / 3:
            message += "It's not very effective.\n"
        elif damage_dealt <= defender.hp / 1.5:
            message += "It's effective!\n"
        else:
            message += "It's extremely effective!\n"
        
        # assign the damage
        defender.hp -= damage_dealt

        #  Check if defender is  knocked out
        if defender.hp <= 0:
            message += f"{defender.name} fainted!\n" # append fainted message
            pokemon_fainted = True # set this value to True
            
            # concede if no pokemon left
            if len(defend_team.roster) == 0:

                # figure out who's the attacker it is for the message
                if self.current_turn: # you are the attacker
                    message += "Your opponent conceded! You win!"
                else: # opponent is the attacker
                    message += "You conceded! Your opponent says 'good match!'"

                # set the battle_done bool to True
                self.battle_done = True

            # otherwise bring up a new pokemon
            else:
                if self.current_turn: # opponent brings up new pokemon
                    self.oppo_current = self.oppo_team.roster.pop(0)
                    message += f"Your opponent summoned {self.oppo_current.name}!\n"

                else: # you bring up new pokemon
                    self.human_current = self.human_team.roster.pop(0)
                    message += f"You summoned {self.human_current.name}!\n"

        # flip the current turn
        # we can use the not operator to reverse the boolean
        # ie. not True = False, not False = True
        self.current_turn = not self.current_turn

        # move up the turn count by one and break the loop
        # from testing, I realized sometimes pokemon can't defeat each other....
        self.turn_count += 1

        if self.turn_count >= 100:
            message = "This is an unwinnable match! It's a tie!"
            pokemon_fainted = False
            self.battle_done = True

        # finally return the message and faint bool
        return message, pokemon_fainted
                    

            

            

    
