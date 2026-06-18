"""An EXAMPLE Assignment 01 submission, used to show how to run the gym.

This is a complete, *valid* team (every pokemon's stats add up to 150 and uses
real type names). It is here so you can see the gym working end-to-end:

    from pokemon_gym import enter_gym
    from example_team import PokemonTeam

    enter_gym(PokemonTeam)

Use it as a reference for the shape of your own submission - then battle your
own team against it!
"""


class Pokemon1:  # don't rename this class name

    def __init__(self):  # make sure the function signature doesn't change

        # IDENTITY ============================================================
        self.name = "Cinderwing"
        self.type1 = "fire"
        self.type2 = "flying"

        # STATS ===============================================================
        # budget: 55 + 25 + 30 + (20 + 10) + 10 = 150
        self._max_hp = 55
        self.hp = self._max_hp
        self.defense = 25
        self.power = 30
        self.attacks = {"ember": 20, "gust": 10}
        self.heal = {"roost": 10}

    def pick_attack(self, opponent) -> str:
        # heal when we're low and the opponent can't immediately finish us
        if self.hp <= 20 and opponent.hp >= 15:
            return "roost"
        # otherwise lead with our strongest hit
        return "ember"


class Pokemon2:  # don't rename this class name

    def __init__(self):

        # IDENTITY ============================================================
        self.name = "Aquarump"
        self.type1 = "water"
        self.type2 = "ground"

        # STATS ===============================================================
        # budget: 65 + 30 + 25 + (20 + 10) + 0 = 150
        self._max_hp = 65
        self.hp = self._max_hp
        self.defense = 30
        self.power = 25
        self.attacks = {"surf": 20, "mud_shot": 10}
        self.heal = {}

    def pick_attack(self, opponent) -> str:
        # if the opponent is nearly out, swing for the cheaper, reliable hit
        if opponent.hp <= 10:
            return "mud_shot"
        return "surf"


class Pokemon3:  # don't rename this class name

    def __init__(self):

        # IDENTITY ============================================================
        self.name = "Verdantusk"
        self.type1 = "grass"
        self.type2 = "fighting"

        # STATS ===============================================================
        # budget: 60 + 20 + 35 + (15 + 5) + 15 = 150
        self._max_hp = 60
        self.hp = self._max_hp
        self.defense = 20
        self.power = 35
        self.attacks = {"vine_smash": 15, "jab": 5}
        self.heal = {"photosynthesis": 15}

    def pick_attack(self, opponent) -> str:
        if self.hp <= 18 and opponent.hp >= 20:
            return "photosynthesis"
        return "vine_smash"


class PokemonTeam:  # don't rename this class name

    def __init__(self):

        # IDENTITY ============================================================
        self.team_name = "The Drafting Tables"
        self.trainer_name = "Example Student"
        self.salutation = "We measure twice and KO once!"

        # ROSTER ==============================================================
        self.roster = {
            "Cinderwing": Pokemon1(),
            "Aquarump": Pokemon2(),
            "Verdantusk": Pokemon3(),
        }

        # CURRENT POKEMON =====================================================
        self.current_pokemon = None

    # --- a small helper so we never pick a fainted pokemon ------------------
    def _healthy(self):
        return [p for p in self.roster.values() if p.hp > 0]

    def pick_on_go_first(self, opponent_team):
        # lead with our bulkiest pokemon when we don't know their lead
        self.current_pokemon = max(self.roster.values(), key=lambda p: p._max_hp)

    def pick_on_go_second(self, opponent_team):
        # we can see their lead - send out a decent matchup
        self.current_pokemon = self._pick_counter(opponent_team.current_pokemon)

    def pick_on_faint(self, opponent_team):
        # send out our best remaining (healthy) pokemon
        self.current_pokemon = self._pick_counter(opponent_team.current_pokemon)

    def switch_pokemon(self, opponent_team):
        # only switch if our current pokemon is in real trouble
        current = self.current_pokemon
        if current is not None and current.hp > current._max_hp * 0.3:
            return
        better = self._pick_counter(opponent_team.current_pokemon)
        if better is not None:
            self.current_pokemon = better

    # --- pick the healthiest pokemon we still have --------------------------
    def _pick_counter(self, enemy):
        healthy = self._healthy()
        if not healthy:
            return None
        # simple strategy: send out whoever has the most health right now
        return max(healthy, key=lambda p: p.hp)
