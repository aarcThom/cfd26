import base64       # to embed the pokemon images directly into the HTML (self contained)
import math         # for a nice "ease" on the attack lunge
import os           # to build / check image file paths
import time         # to pause between animation frames

from pokemon_battle import PokemonBattle  # we only need this for the type hint


class BattleGUI:
    """A rich, animated HTML representation of a PokemonBattle.

    Hand it an *already initialized* PokemonBattle (one that has already had its
    teams chosen via ``choose_oppo_team`` and ``choose_your_team``) and it will:

      1. Progress every turn for you (``while not battle.battle_done: ...``),
         recording the state of the battle at each step.
      2. Grab the current pokemon images from ``data/images`` based on
         ``battle.human_current.name`` and ``battle.oppo_current.name``.
      3. Render an animated, flip-book style HTML battle right inside the
         notebook output cell.

    Typical usage inside a notebook::

        from pokemon_battle import PokemonBattle
        from battleGUI import BattleGUI

        battle = PokemonBattle()
        battle.choose_oppo_team(3)
        battle.choose_your_team(3)

        BattleGUI(battle)   # <- showing this as the last line animates the battle
    """

    # the folder that holds every "<name>.jpg" pokemon picture
    IMG_DIR = "data/images"

    def __init__(self, battle: PokemonBattle, img_dir: str = IMG_DIR,
                 turn_seconds: float = 1.4, autoplay: bool = True) -> None:
        """Build the GUI and record the whole battle.

        Args:
            battle (PokemonBattle): An already-initialized battle (teams chosen).
            img_dir (str): Folder containing the "<name>.jpg" images.
            turn_seconds (float): Roughly how long each turn takes to animate.
            autoplay (bool): If True the battle animates automatically when the
                object is displayed in a notebook.
        """

        # make sure the teams have actually been chosen before we start
        if not hasattr(battle, "human_current") or not hasattr(battle, "oppo_current"):
            raise ValueError(
                "The PokemonBattle is not ready. Call choose_oppo_team(...) and "
                "choose_your_team(...) before handing it to BattleGUI."
            )

        self.battle = battle
        self.img_dir = img_dir
        self.turn_seconds = turn_seconds
        self.autoplay = autoplay

        # a cache so we only base64-encode each image a single time
        self._img_cache: dict[str, str] = {}

        # run the whole battle now and record a "key frame" for every step
        self.frames: list[dict] = self._build_frames()

    # ------------------------------------------------------------------ #
    # STEP 1 - run the battle and record what happened at every step
    # ------------------------------------------------------------------ #
    def _snapshot(self, message: str, attacker: str | None) -> dict:
        """Take a snapshot of the current battle state as a plain dict."""
        human = self.battle.human_current
        oppo = self.battle.oppo_current
        return {
            "h_name": human.name,
            "h_hp": max(human.hp, 0),       # never show a negative hp
            "h_max": human._max_hp,
            "o_name": oppo.name,
            "o_hp": max(oppo.hp, 0),
            "o_max": oppo._max_hp,
            "message": message,
            "attacker": attacker,           # "human", "oppo", or None
        }

    def _build_frames(self) -> list[dict]:
        """Progress the battle to the end, recording one frame per state."""
        frames = []

        # the opening "vs" frame, before anyone has attacked
        frames.append(self._snapshot(
            message=(f"A battle begins!\n"
                     f"{self.battle.human_current.name} (you) vs "
                     f"{self.battle.oppo_current.name} (iggy)!"),
            attacker=None,
        ))

        # the exact loop the assignment asked for
        while not self.battle.battle_done:

            # remember who is attacking *before* the turn flips it
            attacker = "human" if self.battle.current_turn else "oppo"

            # remember the pokemon that are out before the turn, so we can tell
            # if a knocked-out pokemon got swapped for a fresh one
            pre_human = self.battle.human_current
            pre_oppo = self.battle.oppo_current

            # progress the turn (this mutates hp, may swap pokemon, etc.)
            message, fainted = self.battle.battle_turn()

            # frame A: the attack itself (shows the damage that was just dealt)
            frames.append(self._snapshot(message=message, attacker=attacker))

            # frame B: if a fainted pokemon was replaced, show the new one
            swapped = (self.battle.human_current is not pre_human) or \
                      (self.battle.oppo_current is not pre_oppo)
            if swapped:
                incoming = (self.battle.oppo_current if attacker == "human"
                            else self.battle.human_current)
                frames.append(self._snapshot(
                    message=f"{incoming.name} is sent into battle!",
                    attacker=None,
                ))

        return frames

    # ------------------------------------------------------------------ #
    # STEP 2 - turn each pokemon name into an embeddable image
    # ------------------------------------------------------------------ #
    def _img_uri(self, name: str) -> str:
        """Return a base64 data-URI for a pokemon, or a placeholder if missing."""
        if name in self._img_cache:
            return self._img_cache[name]

        # try the expected .jpg, then a couple of sensible fallbacks
        uri = ""
        for ext in (".jpg", ".jpeg", ".png"):
            path = os.path.join(self.img_dir, f"{name}{ext}")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("ascii")
                mime = "png" if ext == ".png" else "jpeg"
                uri = f"data:image/{mime};base64,{encoded}"
                break

        self._img_cache[name] = uri
        return uri

    @staticmethod
    def _hp_color(fraction: float) -> str:
        """Classic green / yellow / red health bar colouring."""
        if fraction > 0.5:
            return "#5cdb5c"
        if fraction > 0.2:
            return "#f7c948"
        return "#e85d4e"

    # ------------------------------------------------------------------ #
    # STEP 3 - render a single moment of the battle as HTML
    # ------------------------------------------------------------------ #
    def _pokemon_html(self, name: str, hp: int, max_hp: int, *,
                      is_player: bool, lunge: float, hit: bool) -> str:
        """HTML for one pokemon: its picture plus a name + HP info card."""
        fraction = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))
        pct = fraction * 100.0
        color = self._hp_color(fraction)
        fainted = hp <= 0

        # the player's pokemon sits bottom-left and lunges up-and-right,
        # the opponent sits top-right and lunges down-and-left
        if is_player:
            dx, dy = lunge * 60.0, -lunge * 40.0
        else:
            dx, dy = -lunge * 60.0, lunge * 40.0

        # when fainted, the pokemon greys out, drops and fades away
        if fainted:
            transform = "translateY(35px) rotate(8deg)"
            extra = "opacity:0.25; filter:grayscale(100%);"
        else:
            transform = f"translate({dx:.1f}px, {dy:.1f}px)"
            extra = "filter:brightness(1.6) saturate(1.4);" if hit else ""

        img = self._img_uri(name)
        if img:
            pic = (f'<img src="{img}" alt="{name}" '
                   f'style="width:150px;height:150px;object-fit:contain;'
                   f'image-rendering:auto;transform:{transform};{extra}'
                   f'transition:transform .08s linear;">')
        else:
            # graceful fallback if an image file is missing
            pic = (f'<div style="width:150px;height:150px;display:flex;'
                   f'align-items:center;justify-content:center;background:#222;'
                   f'color:#fff;border-radius:12px;transform:{transform};{extra}">'
                   f'{name}</div>')

        owner = "You" if is_player else "iggy"
        card = (
            f'<div style="background:#fffef0;border:3px solid #303030;'
            f'border-radius:10px;padding:6px 10px;min-width:170px;'
            f'box-shadow:2px 2px 0 #303030;">'
            f'  <div style="font-weight:700;color:#303030;text-transform:capitalize;">'
            f'    {name} <span style="font-weight:400;font-size:11px;color:#888;">({owner})</span>'
            f'  </div>'
            f'  <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">'
            f'    <span style="font-size:11px;font-weight:700;color:#c39b29;">HP</span>'
            f'    <div style="flex:1;height:9px;background:#5b5b4a;border-radius:6px;'
            f'         border:1px solid #303030;overflow:hidden;">'
            f'      <div style="width:{pct:.1f}%;height:100%;background:{color};'
            f'           transition:width .08s linear;"></div>'
            f'    </div>'
            f'  </div>'
            f'  <div style="text-align:right;font-size:11px;color:#555;margin-top:2px;">'
            f'    {hp} / {max_hp}'
            f'  </div>'
            f'</div>'
        )
        return pic, card

    def _scene_html(self, h_name, h_hp, h_max, o_name, o_max, o_hp,
                    message, attacker, lunge) -> str:
        """Assemble a full battle scene (both pokemon + the message box)."""
        # only the attacker lunges; the defender flashes when the lunge peaks
        h_lunge = lunge if attacker == "human" else 0.0
        o_lunge = lunge if attacker == "oppo" else 0.0
        h_hit = attacker == "oppo" and lunge > 0.5
        o_hit = attacker == "human" and lunge > 0.5

        h_pic, h_card = self._pokemon_html(
            h_name, h_hp, h_max, is_player=True, lunge=h_lunge, hit=h_hit)
        o_pic, o_card = self._pokemon_html(
            o_name, o_hp, o_max, is_player=False, lunge=o_lunge, hit=o_hit)

        message_html = message.strip().replace("\n", "<br>")

        return f"""
        <div style="font-family:'Trebuchet MS',Verdana,sans-serif;width:640px;
                    border:4px solid #303030;border-radius:16px;overflow:hidden;
                    box-shadow:4px 4px 0 #303030;">

          <!-- the battlefield -->
          <div style="position:relative;height:340px;background:#ffffff;">

            <!-- opponent: top-right pokemon, info card top-left -->
            <div style="position:absolute;top:18px;left:24px;">{o_card}</div>
            <div style="position:absolute;top:30px;right:60px;text-align:center;">
              {o_pic}
            </div>

            <!-- player: bottom-left pokemon, info card bottom-right -->
            <div style="position:absolute;bottom:24px;right:24px;">{h_card}</div>
            <div style="position:absolute;bottom:18px;left:60px;text-align:center;">
              {h_pic}
            </div>
          </div>

          <!-- the message box -->
          <div style="background:#303030;color:#f5f5f5;padding:14px 18px;
                      min-height:64px;font-size:15px;line-height:1.5;
                      border-top:4px solid #1a1a1a;">
            {message_html}
          </div>
        </div>
        """

    # ------------------------------------------------------------------ #
    # STEP 4 - play the recorded frames back as an animation
    # ------------------------------------------------------------------ #
    def play(self) -> None:
        """Animate the whole battle inside the current notebook output cell."""
        # import here so the module still imports fine outside of a notebook
        from IPython.display import HTML, clear_output, display

        substeps = 10  # how many in-between frames to draw per key frame

        def show(scene_html: str) -> None:
            clear_output(wait=True)       # swap the old frame for the new one
            display(HTML(scene_html))

        # draw the opening frame
        first = self.frames[0]
        show(self._scene_html(
            first["h_name"], first["h_hp"], first["h_max"],
            first["o_name"], first["o_max"], first["o_hp"],
            first["message"], first["attacker"], lunge=0.0))
        time.sleep(self.turn_seconds * 0.7)

        # then tween from each frame to the next
        prev = first
        dt = self.turn_seconds / (substeps + 4)
        for frame in self.frames[1:]:
            for step in range(1, substeps + 1):
                t = step / substeps

                # smoothly interpolate the hp bars; if the pokemon was swapped
                # (different name) just snap straight to the new value
                if frame["h_name"] == prev["h_name"]:
                    h_hp = prev["h_hp"] + (frame["h_hp"] - prev["h_hp"]) * t
                else:
                    h_hp = frame["h_hp"]
                if frame["o_name"] == prev["o_name"]:
                    o_hp = prev["o_hp"] + (frame["o_hp"] - prev["o_hp"]) * t
                else:
                    o_hp = frame["o_hp"]

                # the attacker lunges out and back (a smooth there-and-back arc)
                lunge = math.sin(t * math.pi)

                show(self._scene_html(
                    frame["h_name"], int(round(h_hp)), frame["h_max"],
                    frame["o_name"], frame["o_max"], int(round(o_hp)),
                    frame["message"], frame["attacker"], lunge))
                time.sleep(dt)

            prev = frame
            time.sleep(self.turn_seconds * 0.6)  # hold so the message is readable

    def show_final(self) -> None:
        """Display only the final state of the battle (no animation)."""
        from IPython.display import HTML, display
        f = self.frames[-1]
        display(HTML(self._scene_html(
            f["h_name"], f["h_hp"], f["h_max"],
            f["o_name"], f["o_max"], f["o_hp"],
            f["message"], None, lunge=0.0)))

    # ------------------------------------------------------------------ #
    # notebook hook: showing the object runs the animation automatically
    # ------------------------------------------------------------------ #
    def _ipython_display_(self) -> None:
        if self.autoplay:
            self.play()
        else:
            self.show_final()
