"""Pokemon Training Gym
=======================

A self-contained module that lets students *test their Assignment 01 team*
before they hand it in.  Drop this file next to your submission ``.py`` file
(the one that contains your ``Pokemon1`` / ``Pokemon2`` / ``Pokemon3`` and
``PokemonTeam`` classes) and run::

    from pokemon_gym import enter_gym
    from my_submission import PokemonTeam   # <- whatever your file is called

    enter_gym(PokemonTeam)

The gym does two things for you:

1.  **Checks your work for errors.**  It looks for the kinds of mistakes that
    would get your Pokemon disqualified or cause the tournament engine to
    crash (missing attributes, a stat budget that does not add up to 150,
    invalid type names, ``pick_attack`` returning a name that isn't one of
    your attacks, and so on).

2.  **Runs a tournament.**  It throws your team into a 32-trainer,
    single-elimination bracket against 31 randomly generated opponents, shows
    you one sample run, and then simulates many tournaments so you can see how
    your team really stacks up.

NOTE FOR STUDENTS: the *real* tournament engine the instructor runs may differ
in small ways.  This gym uses a sensible, fair set of rules so you can practice
and tune your strategy.  Think of it as a sparring partner, not the judge.

This module only uses the Python standard library, so it will run anywhere.
"""

import random


# ===========================================================================
# THE TYPE CHART
# ---------------------------------------------------------------------------
# This is the same balanced type chart shown in the assignment.  It tells us
# how effective an ATTACKING type is against a DEFENDING type:
#   2.0 -> super effective, 0.5 -> not very effective, 0.0 -> no effect.
# ===========================================================================

# the 15 types, in the order they appear in each row below
_TYPES = [
    "normal", "fire", "water", "grass", "electric", "ice", "psychic",
    "fighting", "poison", "ground", "flying", "rock", "bug", "ghost", "dragon",
]

# each row is one ATTACKING type vs. every DEFENDING type (same order as above)
_CHART_ROWS = {
    #            nor  fir  wat  gra  ele  ice  psy  fgt  poi  gnd  fly  roc  bug  gho  dra
    "normal":   [1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,  .5,   1,   0,   1],
    "fire":     [1,  .5,  .5,   2,   1,   2,   1,   1,   1,   1,   1,  .5,   2,   1,  .5],
    "water":    [1,   2,  .5,  .5,   1,   1,   1,   1,   1,   2,   1,   2,   1,   1,  .5],
    "grass":    [1,  .5,   2,  .5,   1,   1,   1,   1,  .5,   2,  .5,   2,  .5,   1,  .5],
    "electric": [1,   1,   2,  .5,  .5,   1,   1,   1,   1,   0,   2,   1,   1,   1,  .5],
    "ice":      [1,  .5,  .5,   2,   1,  .5,   1,   1,   1,   2,   2,   1,   1,   1,   2],
    "psychic":  [1,   1,   1,   1,   1,   1,  .5,   2,   2,   1,   1,   1,   1,   2,   1],
    "fighting": [2,   1,   1,   1,   1,   2,  .5,   1,  .5,   1,  .5,   2,  .5,   1,   1],
    "poison":   [1,   1,   1,   2,   1,   1,   1,   1,  .5,  .5,   1,  .5,   1,   1,   1],
    "ground":   [1,   2,   1,  .5,   2,   1,   1,   1,   2,   1,   0,   2,   1,   1,   1],
    "flying":   [1,   1,   1,   2,  .5,   1,   1,   2,   1,   1,   1,  .5,   2,   1,   1],
    "rock":     [1,   2,   1,   1,   1,   2,   1,  .5,   1,  .5,   2,   1,   2,   1,   1],
    "bug":      [1,  .5,   1,   2,   1,   1,   2,  .5,   1,   1,  .5,   1,   1,  .5,   1],
    "ghost":    [.5,  1,   1,   1,   1,   1,   2,   1,   1,   1,   1,   1,   1,   2,   1],
    "dragon":   [1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2],
}

# turn the rows above into a quick lookup:  TYPE_CHART[attacker][defender] -> float
TYPE_CHART = {
    attacker: {_TYPES[i]: row[i] for i in range(len(_TYPES))}
    for attacker, row in _CHART_ROWS.items()
}


def _type_multiplier(attacker, defender) -> float:
    """How effective ``attacker``'s attack is against ``defender``.

    A pokemon has two types, so we let the attacker use whichever of its two
    types is most effective against the defender.  Each of the defender's two
    types contributes to the multiplier (just like the real games).

    Args:
        attacker: the pokemon doing the attacking.
        defender: the pokemon being attacked.

    Returns:
        float: the damage multiplier (e.g. 2.0, 1.0, 0.5, 0.0).
    """
    best = None

    # try both of the attacker's types and keep the most effective one
    for atk_type in (attacker.type1, attacker.type2):
        if atk_type not in TYPE_CHART:
            continue  # skip invalid / missing types instead of crashing

        multiplier = 1.0
        for def_type in (defender.type1, defender.type2):
            # an unknown defending type just counts as neutral (x1)
            multiplier *= TYPE_CHART[atk_type].get(def_type, 1.0)

        best = multiplier if best is None else max(best, multiplier)

    # if the attacker had no valid types at all, treat the hit as neutral
    return 1.0 if best is None else best


# ===========================================================================
# THE BATTLE RULES
# ---------------------------------------------------------------------------
# These constants make the gym easy to tweak.  The damage model matches the
# one described to students:
#   raw    = (power + attack_value) * type_multiplier
#   damage = max(0, raw - defender.defense * f)   where f is random in [0.5, 1.0]
# ===========================================================================

STAT_BUDGET = 150          # _max_hp + defense + power + attacks + heal must equal this
BENCH_HEAL_PER_TURN = 5    # hp a benched (non-fainted) pokemon recovers each turn
TIRED_THRESHOLD = 100      # once a pokemon has attacked for this many points it must rest
MAX_TURNS = 300            # safety cap so an unwinnable match can't loop forever
DEFENSE_MIN, DEFENSE_MAX = 0.5, 1.0   # random defense effectiveness range


# ===========================================================================
# RANDOM OPPONENTS
# ---------------------------------------------------------------------------
# To fill the bracket we need 31 opponents.  We generate them on the fly so
# every tournament is different.  These opponent classes implement the *exact*
# same interface the assignment asks you to implement, so your team battles
# them fairly.
# ===========================================================================

# silly trainer-name pieces so each opponent feels like a real rival
_TRAINER_FIRST = [
    "Iggy", "B+", "Roxy", "Bjarke", "Zaha", "Mies", "Corbu", "Tadao",
    "Frank", "Norman", "Renzo", "Santiago", "Eero", "Alvar", "Oscar", "Kenzo",
]
_TRAINER_LAST = [
    "the Brave", "Jr.", "the Bold", "von Detail", "McFacade", "the Cantilever",
    "Prime", "the Parametric", "the Modular", "the Brutalist", "the Glazier",
]

# bits to assemble nonsense pokemon names from
_NAME_PARTS_A = ["Glo", "Spar", "Mun", "Cryo", "Zap", "Terra", "Vex", "Pyro",
                 "Aqua", "Noc", "Volt", "Gly", "Umbra", "Helio", "Fract"]
_NAME_PARTS_B = ["mite", "zard", "puff", "fang", "wing", "claw", "drake",
                 "lith", "byte", "tail", "horn", "spire", "maw", "ling"]


class _RandomPokemon:
    """A randomly generated opponent pokemon.

    It implements the same attributes and ``pick_attack`` method that the
    assignment asks students to build, so it slots straight into the engine.
    """

    def __init__(self, blueprint: dict) -> None:
        # a "blueprint" is just a plain dict of stats, so re-building the
        # pokemon from it always gives a fresh, full-health copy
        self.name = blueprint["name"]
        self.type1 = blueprint["type1"]
        self.type2 = blueprint["type2"]
        self._max_hp = blueprint["max_hp"]
        self.hp = self._max_hp
        self.defense = blueprint["defense"]
        self.power = blueprint["power"]
        self.attacks = dict(blueprint["attacks"])
        self.heal = dict(blueprint["heal"])

    def pick_attack(self, opponent) -> str:
        # if we're hurt and we have a heal available, sometimes heal up
        if self.heal and self.hp <= self._max_hp * 0.35:
            return next(iter(self.heal))

        # otherwise swing with our hardest-hitting attack
        return max(self.attacks, key=self.attacks.get)


class _RandomTeam:
    """A randomly generated opponent team (same interface as ``PokemonTeam``)."""

    def __init__(self, blueprint: dict) -> None:
        self.team_name = blueprint["team_name"]
        self.trainer_name = blueprint["trainer_name"]
        self.salutation = blueprint["salutation"]

        # rebuild fresh pokemon from the stored blueprints
        self.roster = {
            poke_bp["name"]: _RandomPokemon(poke_bp)
            for poke_bp in blueprint["pokemon"]
        }
        self.current_pokemon = None

    # --- helper: list the team members that can still fight -----------------
    def _healthy(self):
        return [p for p in self.roster.values() if p.hp > 0]

    # --- pick the pokemon with the best type matchup vs a target ------------
    def _best_against(self, target):
        healthy = self._healthy()
        if not healthy:
            return None
        if target is None:
            return max(healthy, key=lambda p: p._max_hp)
        return max(healthy, key=lambda p: _type_multiplier(p, target))

    def pick_on_go_first(self, opponent_team):
        # we don't know their pokemon yet, so just lead with our beefiest one
        self.current_pokemon = max(self.roster.values(), key=lambda p: p._max_hp)

    def pick_on_go_second(self, opponent_team):
        # we can see their lead - counter it
        self.current_pokemon = self._best_against(opponent_team.current_pokemon)

    def pick_on_faint(self, opponent_team):
        # send out the best remaining counter (never a fainted pokemon)
        self.current_pokemon = self._best_against(opponent_team.current_pokemon)

    def switch_pokemon(self, opponent_team):
        # stay in unless we're badly hurt and someone healthier can counter
        current = self.current_pokemon
        if current is not None and current.hp > current._max_hp * 0.3:
            return
        better = self._best_against(opponent_team.current_pokemon)
        if better is not None:
            self.current_pokemon = better


def _make_team_blueprint(rng: random.Random, index: int) -> dict:
    """Build the data for one random opponent team (3 pokemon)."""
    trainer = f"{rng.choice(_TRAINER_FIRST)} {rng.choice(_TRAINER_LAST)}"

    pokemon = []
    for _ in range(3):
        # --- split exactly STAT_BUDGET points across the stats --------------
        max_hp = rng.randint(40, 70)
        defense = rng.randint(10, 35)
        power = rng.randint(10, 35)
        remaining = STAT_BUDGET - max_hp - defense - power  # always >= 10

        # spend up to a little of the remainder on a heal, keep >=10 for attacks
        heal_amount = rng.randint(0, max(0, min(25, remaining - 10)))
        remaining -= heal_amount

        # split what's left across two attacks
        first_attack = rng.randint(1, remaining - 1) if remaining > 1 else remaining
        second_attack = remaining - first_attack

        attacks = {"jab": first_attack}
        if second_attack > 0:
            attacks["slam"] = second_attack

        heal = {"recover": heal_amount} if heal_amount > 0 else {}

        pokemon.append({
            "name": rng.choice(_NAME_PARTS_A) + rng.choice(_NAME_PARTS_B),
            "type1": rng.choice(_TYPES),
            "type2": rng.choice(_TYPES),
            "max_hp": max_hp,
            "defense": defense,
            "power": power,
            "attacks": attacks,
            "heal": heal,
        })

    return {
        "team_name": f"Squad {index:02d}",
        "trainer_name": trainer,
        "salutation": "Let's battle!",
        "pokemon": pokemon,
    }


# ===========================================================================
# THE BATTLE ENGINE
# ---------------------------------------------------------------------------
# A "match" is one team versus another.  We never trust the team objects to
# behave perfectly: every call into a student's code is wrapped so that a bug
# is recorded and the match keeps going instead of crashing the whole gym.
# ===========================================================================

class _ErrorLog:
    """Collects the unique problems a student's team causes during battle."""

    def __init__(self):
        self._seen = set()
        self.messages = []

    def add(self, message: str) -> None:
        if message not in self._seen:
            self._seen.add(message)
            self.messages.append(message)


def _healthy_members(team):
    """Every pokemon on a team that still has hp left."""
    return [p for p in team.roster.values() if getattr(p, "hp", 0) > 0]


def _ensure_valid_current(team, error_log, is_student) -> bool:
    """Make sure ``team.current_pokemon`` is a healthy roster member.

    If the team's own logic left it on ``None`` or a fainted pokemon, we fall
    back to the first healthy one so the match can continue.  Returns False if
    the team has no healthy pokemon left at all (i.e. it has lost).
    """
    healthy = _healthy_members(team)
    if not healthy:
        return False

    current = getattr(team, "current_pokemon", None)
    if current not in healthy:
        if is_student and current is not None:
            error_log.add(
                "Your team picked a fainted pokemon to send out. Remember the "
                "assignment's hint: never send out a pokemon whose hp is 0."
            )
        team.current_pokemon = healthy[0]
    return True


def _safe_team_call(team, method_name, opponent_team, error_log, is_student) -> None:
    """Call one of a team's selection methods, surviving any error it throws."""
    method = getattr(team, method_name, None)
    if not callable(method):
        if is_student:
            error_log.add(f"Your PokemonTeam is missing the {method_name}() method.")
        return
    try:
        method(opponent_team)
    except Exception as exc:  # noqa: BLE001 - we want to catch anything a student wrote
        if is_student:
            error_log.add(f"Your {method_name}() crashed: {type(exc).__name__}: {exc}")


def _resolve_action(attacker, defender, attacks_done, error_log, is_student, rng):
    """Carry out one pokemon's chosen action (attack / heal / rest).

    Returns the number of attack-points the attacker spent this turn (so the
    'tired' counter can be updated by the caller).
    """
    # ask the pokemon what it wants to do
    try:
        choice = attacker.pick_attack(defender)
    except Exception as exc:  # noqa: BLE001
        if is_student:
            error_log.add(f"Your pick_attack() crashed: {type(exc).__name__}: {exc}")
        return 0  # treat a crash as a wasted turn

    # --- the pokemon chose to heal -----------------------------------------
    if isinstance(choice, str) and choice in getattr(attacker, "heal", {}):
        amount = attacker.heal[choice]
        attacker.hp = min(attacker._max_hp, attacker.hp + amount)
        return 0

    # --- the pokemon chose an attack ---------------------------------------
    if isinstance(choice, str) and choice in getattr(attacker, "attacks", {}):
        # too tired? this turn is spent resting instead of attacking
        if attacks_done >= TIRED_THRESHOLD:
            return -1  # signal: forced rest (caller resets the tired counter)

        attack_value = attacker.attacks[choice]
        multiplier = _type_multiplier(attacker, defender)

        raw = (attacker.power + attack_value) * multiplier
        defense_hit = defender.defense * rng.uniform(DEFENSE_MIN, DEFENSE_MAX)
        damage = max(0, int(raw - defense_hit))

        defender.hp -= damage
        return attack_value

    # --- the pokemon returned something we don't recognise -----------------
    if is_student:
        error_log.add(
            f"pick_attack() returned {choice!r}, which is not one of that "
            f"pokemon's attack or heal names. The engine treats this as a wasted turn."
        )
    return 0


def _play_match(entrant_a, entrant_b, error_log, rng):
    """Play one full match and return the winning entrant.

    An "entrant" is a dict with a ``factory`` (builds a fresh, full-health
    team), a ``name``, and an ``is_student`` flag.
    """
    team_a = entrant_a["factory"]()
    team_b = entrant_b["factory"]()

    # --- the coin flip: the winner leads and attacks first ------------------
    if rng.random() < 0.5:
        first, second = team_a, team_b
        first_is_student = entrant_a["is_student"]
        second_is_student = entrant_b["is_student"]
    else:
        first, second = team_b, team_a
        first_is_student = entrant_b["is_student"]
        second_is_student = entrant_a["is_student"]

    # --- each trainer chooses their opening pokemon -------------------------
    _safe_team_call(first, "pick_on_go_first", second, error_log, first_is_student)
    _safe_team_call(second, "pick_on_go_second", first, error_log, second_is_student)
    _ensure_valid_current(first, error_log, first_is_student)
    _ensure_valid_current(second, error_log, second_is_student)

    # the attacker goes first, then we alternate
    active, passive = first, second
    active_is_student = first_is_student
    passive_is_student = second_is_student

    tired = {}  # id(pokemon) -> total attack-points spent this match

    for _turn in range(MAX_TURNS):
        # 1) benched pokemon recover a little health
        for poke in active.roster.values():
            if poke is not active.current_pokemon and 0 < poke.hp < poke._max_hp:
                poke.hp = min(poke._max_hp, poke.hp + BENCH_HEAL_PER_TURN)

        # 2) the active trainer may switch (this uses up their attack)
        before = active.current_pokemon
        _safe_team_call(active, "switch_pokemon", passive, error_log, active_is_student)
        _ensure_valid_current(active, error_log, active_is_student)

        if active.current_pokemon is not before:
            # they switched - turn over, no attack this turn
            active, passive = passive, active
            active_is_student, passive_is_student = passive_is_student, active_is_student
            continue

        # 3) carry out the attack / heal
        attacker = active.current_pokemon
        defender = passive.current_pokemon
        spent = _resolve_action(
            attacker, defender, tired.get(id(attacker), 0),
            error_log, active_is_student, rng)

        if spent < 0:
            tired[id(attacker)] = 0          # forced rest clears the tiredness
        elif spent > 0:
            tired[id(attacker)] = tired.get(id(attacker), 0) + spent

        # 4) did the defender faint?
        if defender.hp <= 0:
            if not _healthy_members(passive):
                # the passive team is wiped out - the active team wins
                return entrant_a if active is team_a else entrant_b
            # the passive trainer sends out a replacement, then we sanity-check
            # their choice (this is where a genuinely bad pick gets flagged)
            _safe_team_call(passive, "pick_on_faint", active, error_log, passive_is_student)
            _ensure_valid_current(passive, error_log, passive_is_student)

        # 5) hand the turn to the other trainer
        active, passive = passive, active
        active_is_student, passive_is_student = passive_is_student, active_is_student

    # --- hit the turn cap: decide by who has more health left ---------------
    a_hp = sum(max(0, p.hp) for p in team_a.roster.values())
    b_hp = sum(max(0, p.hp) for p in team_b.roster.values())
    if a_hp != b_hp:
        return entrant_a if a_hp > b_hp else entrant_b
    return rng.choice([entrant_a, entrant_b])  # exact tie -> coin flip


# ===========================================================================
# THE TOURNAMENT
# ---------------------------------------------------------------------------
# 32 trainers, single elimination.  We track how far the student's team gets.
# ===========================================================================

ROUND_NAMES = ["Round of 32", "Round of 16", "Quarterfinal", "Semifinal", "Final"]


def _build_random_entrants(rng: random.Random, count: int):
    """Make ``count`` fresh random opponents for one tournament."""
    entrants = []
    for i in range(count):
        blueprint = _make_team_blueprint(rng, i + 1)
        # default arg captures THIS blueprint so each factory is independent
        factory = lambda bp=blueprint: _RandomTeam(bp)
        entrants.append({
            "name": blueprint["trainer_name"],
            "factory": factory,
            "is_student": False,
        })
    return entrants


def _run_bracket(student_entrant, error_log, rng, log_student_path=False):
    """Run one 32-trainer bracket. Returns (rounds_won, path_log).

    ``rounds_won`` is 0-5: how many rounds the student survived (5 = champion).
    ``path_log`` is a list of human-readable strings describing each of the
    student's matches (only filled in when ``log_student_path`` is True).
    """
    entrants = [student_entrant] + _build_random_entrants(rng, 31)
    rng.shuffle(entrants)

    rounds_won = 0
    path_log = []

    round_index = 0
    while len(entrants) > 1:
        next_round = []
        for i in range(0, len(entrants), 2):
            left, right = entrants[i], entrants[i + 1]
            winner = _play_match(left, right, error_log, rng)
            next_round.append(winner)

            # record the student's own match for the sample bracket
            if log_student_path and (left["is_student"] or right["is_student"]):
                opponent = right if left["is_student"] else left
                student_won = winner["is_student"]
                outcome = "WON " if student_won else "LOST"
                path_log.append(
                    f"  {ROUND_NAMES[round_index]:<13} vs {opponent['name']:<28} {outcome}"
                )

        # did the student advance?
        student_alive = any(e["is_student"] for e in next_round)
        if student_alive:
            rounds_won += 1
        elif log_student_path:
            break  # no need to keep simulating once the student is out

        if not student_alive and not log_student_path:
            # for the silent aggregate runs we still want a true champion count,
            # but the student is gone so we can stop early
            return rounds_won, path_log

        entrants = next_round
        round_index += 1

    return rounds_won, path_log


# ===========================================================================
# VALIDATION  ("did the student do the assignment correctly?")
# ===========================================================================

# the attributes every Pokemon must expose, and the type we expect
_REQUIRED_POKEMON_NUMBERS = ["_max_hp", "hp", "defense", "power"]


class _Findings:
    """Buckets the problems we find into three severities."""

    def __init__(self):
        self.fatal = []          # the tournament literally cannot run
        self.disqualifiers = []  # would be disqualified in the real tournament
        self.warnings = []       # not illegal, but probably a mistake


def _check_pokemon(name_hint, poke, findings, rng) -> None:
    """Validate a single pokemon against the assignment template."""
    label = getattr(poke, "name", name_hint)

    # --- required attributes exist and are the right kind -------------------
    for attr in _REQUIRED_POKEMON_NUMBERS:
        if not hasattr(poke, attr):
            findings.fatal.append(f"Pokemon '{label}' is missing the .{attr} attribute.")
        elif not isinstance(getattr(poke, attr), (int, float)):
            findings.fatal.append(f"Pokemon '{label}'.{attr} must be a number.")

    for attr in ("name", "type1", "type2"):
        if not hasattr(poke, attr):
            findings.fatal.append(f"Pokemon '{label}' is missing the .{attr} attribute.")
        elif not isinstance(getattr(poke, attr), str):
            findings.fatal.append(f"Pokemon '{label}'.{attr} must be a string.")

    if not isinstance(getattr(poke, "attacks", None), dict) or not poke.attacks:
        findings.fatal.append(f"Pokemon '{label}'.attacks must be a non-empty dictionary.")
        return  # can't validate much more without attacks

    if not isinstance(getattr(poke, "heal", None), dict):
        findings.fatal.append(f"Pokemon '{label}'.heal must be a dictionary.")
        return

    if not callable(getattr(poke, "pick_attack", None)):
        findings.fatal.append(f"Pokemon '{label}' is missing a pick_attack() method.")
        return

    # --- type names must be from the official list --------------------------
    for attr in ("type1", "type2"):
        value = getattr(poke, attr)
        if value not in _TYPES:
            findings.disqualifiers.append(
                f"Pokemon '{label}'.{attr} is '{value}', which is not a valid type. "
                f"Use one of: {', '.join(_TYPES)} (all lowercase)."
            )

    # --- attack / heal values must be numbers -------------------------------
    for move_dict, kind in ((poke.attacks, "attack"), (poke.heal, "heal")):
        for move_name, value in move_dict.items():
            if not isinstance(value, (int, float)):
                findings.fatal.append(
                    f"Pokemon '{label}' {kind} '{move_name}' must have a number value.")

    if len(poke.heal) > 1:
        findings.disqualifiers.append(
            f"Pokemon '{label}' has {len(poke.heal)} heal effects. You may only have one.")

    # --- the all-important 150 stat budget ----------------------------------
    try:
        total = (poke._max_hp + poke.defense + poke.power
                 + sum(poke.attacks.values()) + sum(poke.heal.values()))
        if total != STAT_BUDGET:
            findings.disqualifiers.append(
                f"Pokemon '{label}' stat budget is {total}, but it must equal "
                f"exactly {STAT_BUDGET} (_max_hp + defense + power + all attacks + all heals)."
            )
    except (TypeError, AttributeError):
        pass  # already reported as a missing/bad attribute above

    # --- hp should start at full --------------------------------------------
    if getattr(poke, "hp", None) != getattr(poke, "_max_hp", object()):
        findings.warnings.append(
            f"Pokemon '{label}'.hp does not start equal to ._max_hp. "
            f"Set 'self.hp = self._max_hp' so it starts at full health."
        )

    # --- pick_attack must return one of its own move names ------------------
    sparring_partner = _RandomPokemon(_make_team_blueprint(rng, 99)["pokemon"][0])
    try:
        choice = poke.pick_attack(sparring_partner)
        valid_names = set(poke.attacks) | set(poke.heal)
        if not isinstance(choice, str):
            findings.warnings.append(
                f"Pokemon '{label}'.pick_attack() returned a {type(choice).__name__}, "
                f"but it must return a string (the name of an attack or heal)."
            )
        elif choice not in valid_names:
            findings.warnings.append(
                f"Pokemon '{label}'.pick_attack() returned '{choice}', which is not "
                f"one of its attacks/heals: {sorted(valid_names)}."
            )
    except Exception as exc:  # noqa: BLE001
        findings.warnings.append(
            f"Pokemon '{label}'.pick_attack() raised {type(exc).__name__}: {exc}")


def _validate(team_class, rng) -> _Findings:
    """Run every check we can think of against a student's submission."""
    findings = _Findings()

    # --- can we even build the team? ----------------------------------------
    try:
        team = team_class()
    except Exception as exc:  # noqa: BLE001
        findings.fatal.append(
            f"Could not create your PokemonTeam: {type(exc).__name__}: {exc}")
        return findings

    # a very common mistake: __init__ misspelled as __int__, which leaves the
    # team with none of its attributes set
    if not hasattr(team, "roster"):
        findings.fatal.append(
            "Your PokemonTeam has no .roster attribute. Double-check that your "
            "constructor is spelled '__init__' (two underscores on each side) - "
            "a common typo is '__int__', which means your setup code never runs."
        )
        return findings

    # --- team identity attributes -------------------------------------------
    for attr in ("team_name", "trainer_name", "salutation"):
        if not hasattr(team, attr):
            findings.warnings.append(f"Your PokemonTeam is missing .{attr}.")
        elif not isinstance(getattr(team, attr), str):
            findings.warnings.append(f"Your PokemonTeam.{attr} should be a string.")

    if not hasattr(team, "current_pokemon"):
        findings.warnings.append(
            "Your PokemonTeam is missing .current_pokemon (set it to None in __init__).")

    # --- the roster ---------------------------------------------------------
    if not isinstance(team.roster, dict):
        findings.fatal.append("Your PokemonTeam.roster must be a dictionary.")
        return findings
    if len(team.roster) == 0:
        findings.fatal.append("Your PokemonTeam.roster is empty - add your three pokemon.")
        return findings
    if len(team.roster) != 3:
        findings.warnings.append(
            f"Your roster has {len(team.roster)} pokemon. The assignment asks for exactly 3.")

    # --- the selection methods exist ----------------------------------------
    for method_name in ("pick_on_go_first", "pick_on_go_second",
                        "pick_on_faint", "switch_pokemon"):
        if not callable(getattr(team, method_name, None)):
            findings.fatal.append(f"Your PokemonTeam is missing the {method_name}() method.")

    # --- validate each pokemon ----------------------------------------------
    for key, poke in team.roster.items():
        _check_pokemon(key, poke, findings, rng)

    # --- do the selection methods actually pick a real pokemon? -------------
    if not findings.fatal:
        dummy_opponent = _RandomTeam(_make_team_blueprint(rng, 1))
        dummy_opponent.current_pokemon = next(iter(dummy_opponent.roster.values()))
        for method_name in ("pick_on_go_first", "pick_on_go_second", "pick_on_faint"):
            try:
                team.current_pokemon = None
                getattr(team, method_name)(dummy_opponent)
                if team.current_pokemon not in team.roster.values():
                    findings.warnings.append(
                        f"After {method_name}(), .current_pokemon is not one of your "
                        f"roster pokemon. Make sure you set it to a value from self.roster."
                    )
            except Exception as exc:  # noqa: BLE001
                findings.warnings.append(
                    f"Your {method_name}() raised {type(exc).__name__}: {exc}")

    return findings


# ===========================================================================
# REPORTING  (the pretty printed output)
# ===========================================================================

def _print_header(title: str) -> None:
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


def _print_findings(findings: _Findings) -> bool:
    """Print the validation results. Returns True if it's safe to run battles."""
    _print_header("STEP 1 - CHECKING YOUR TEAM")

    if not findings.fatal and not findings.disqualifiers and not findings.warnings:
        print("\n  Nice! No problems found. Your team is ready to battle.\n")
        return True

    if findings.fatal:
        print("\n  [X] FATAL PROBLEMS - the tournament can't run until these are fixed:")
        for msg in findings.fatal:
            print(f"      - {msg}")

    if findings.disqualifiers:
        print("\n  [!] DISQUALIFIERS - your pokemon would be removed from the real")
        print("      tournament for these (the gym will still simulate so you can practice):")
        for msg in findings.disqualifiers:
            print(f"      - {msg}")

    if findings.warnings:
        print("\n  [*] WARNINGS - probably mistakes, worth a look:")
        for msg in findings.warnings:
            print(f"      - {msg}")

    print()
    return not findings.fatal


def _verdict(win_rate: float) -> str:
    """A friendly one-line summary based on tournament win rate."""
    if win_rate >= 0.20:
        return "Championship contender! Your team is seriously strong."
    if win_rate >= 0.08:
        return "Solid team - you're a real threat in the bracket."
    if win_rate >= 0.03:
        return "Mid-pack. You'll win some rounds; tune your stats and strategy."
    return "Your team struggles. Revisit your stats, types, and pick_attack logic."


# ===========================================================================
# THE MAIN ENTRY POINT
# ===========================================================================

def enter_gym(team, num_tournaments: int = 200, show_sample: bool = True,
              seed: int = None) -> None:
    """Test your Assignment 01 team: check it for errors, then run a tournament.

    Args:
        team: your ``PokemonTeam`` class (preferred) or an instance of it.
        num_tournaments (int): how many tournaments to simulate for the stats.
        show_sample (bool): print one play-by-play sample bracket first.
        seed (int): optional fixed seed, so you can reproduce the same results.
    """
    rng = random.Random(seed)

    # accept either the class or an instance of it
    team_class = team if isinstance(team, type) else type(team)

    print()
    print("*" * 64)
    print("*           WELCOME TO THE POKEMON TRAINING GYM                 *")
    print("*" * 64)

    # ----- STEP 1: validation ----------------------------------------------
    findings = _validate(team_class, rng)
    can_battle = _print_findings(findings)
    if not can_battle:
        print("  Fix the fatal problems above and run the gym again. Good luck!\n")
        return

    # this entrant rebuilds a fresh copy of the student's team for every match
    student_entrant = {
        "name": "YOUR TEAM",
        "factory": lambda: team_class(),
        "is_student": True,
    }

    error_log = _ErrorLog()

    # ----- STEP 2a: one sample bracket -------------------------------------
    if show_sample:
        _print_header("STEP 2 - A SAMPLE TOURNAMENT (one bracket, 32 trainers)")
        rounds_won, path = _run_bracket(student_entrant, error_log, rng,
                                        log_student_path=True)
        print()
        for line in path:
            print(line)
        print()
        if rounds_won == len(ROUND_NAMES):
            print("  *** YOU WON THE WHOLE TOURNAMENT! CHAMPION! ***")
        else:
            print(f"  You were knocked out in the {ROUND_NAMES[rounds_won]}.")
        print()

    # ----- STEP 2b: many tournaments for real statistics -------------------
    _print_header(f"STEP 3 - HOW YOU STACK UP ({num_tournaments} tournaments)")

    # tally how far the team gets across many randomized brackets
    distribution = [0] * (len(ROUND_NAMES) + 1)  # index = rounds_won (5 = champion)
    total_matches = 0
    total_match_wins = 0

    for _ in range(num_tournaments):
        rounds_won, _ = _run_bracket(student_entrant, error_log, rng)
        distribution[rounds_won] += 1
        total_match_wins += rounds_won
        total_matches += rounds_won + (0 if rounds_won == len(ROUND_NAMES) else 1)

    championships = distribution[len(ROUND_NAMES)]
    win_rate = championships / num_tournaments
    reached_final = sum(distribution[4:]) / num_tournaments
    reached_semi = sum(distribution[3:]) / num_tournaments
    match_win_rate = (total_match_wins / total_matches) if total_matches else 0.0

    print()
    print(f"  Tournament win rate : {win_rate:6.1%}  ({championships} of {num_tournaments})")
    print(f"  Reached the final   : {reached_final:6.1%}")
    print(f"  Reached the semis   : {reached_semi:6.1%}")
    print(f"  Match win rate      : {match_win_rate:6.1%}")
    print()
    print("  How far you got, across all tournaments:")
    stage_labels = ["Out in Round of 32", "Out in Round of 16",
                    "Out in Quarterfinal", "Out in Semifinal",
                    "Lost the Final", "CHAMPION"]
    most = max(distribution) or 1
    for count, label in zip(distribution, stage_labels):
        bar = "#" * int(round(40 * count / most))
        print(f"    {label:<22} {count:>5}  {bar}")
    print()
    print(f"  VERDICT: {_verdict(win_rate)}")

    # ----- any errors the team caused during battle ------------------------
    if error_log.messages:
        print()
        print("  [!] Heads up - your team caused these issues during battles.")
        print("      Fix them before you submit:")
        for msg in error_log.messages:
            print(f"      - {msg}")

    print()
    print("*" * 64)
    print()


# a friendly alias, in case students reach for a different name
test_team = enter_gym
