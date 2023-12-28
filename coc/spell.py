import ujson

from typing import Type, Dict, List
from pathlib import Path

from .abc import DataContainer, DataContainerHolder
from .enums import Resource
from .miscmodels import TimeDelta

SPELLS_FILE_PATH = Path(__file__).parent.joinpath(Path("static/spells.json"))
ARMY_LINK_ID_FILE_PATH = Path(__file__).parent.joinpath(Path("static/spell_ids.json"))


class Spell(DataContainer):
    """Represents a Spell object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The spell's unique ID.
    name: :class:`str`
        The spell's name.
    range: :class:`int`
        The spell's attack range.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the spell to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this spell.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this spell to the next level.
    training_cost: :class:`int`
        The amount of resources required to train this spell.
    training_resource: :class:`Resource`
        The type of resource used to train this spell.
    training_time: :class:`TimeDelta`
        The amount of time required to train this spell.
    is_elixir_spell: :class:`bool`
        Whether this spell is a regular spell from the Barracks
    is_dark_spell: :class:`bool`
        Whether this spell is a dark-spell, trained in the Dark Barracks.
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this spell.
    level: :class:`int`
        The spell's level
    max_level: :class:`int`
        The max level for this spell.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this spell belongs to.
    """
    name: str
    level: int
    max_level: int
    village: str
    is_active: bool

    id: int
    range: int
    dps: int
    ground_target: bool
    speed: int
    upgrade_cost: int
    upgrade_resource: "Resource"
    upgrade_time: "TimeDelta"
    training_cost: int
    training_resource: "Resource"
    training_time: "TimeDelta"

    is_elixir_spell: bool = False
    is_dark_spell: bool = False
    is_loaded: bool = False

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    @property
    def is_max_for_townhall(self):
        """:class:`bool`:
            Returns a boolean that indicates whether the spell is the max level for the player's townhall level.
        """
        if self.is_max:
            return True

        # 1. Hero/troop levels in-game are 1-indexed, UnitStat is 1-indexed
        # 2. TH-lab levels in-game and here are 1-indexed
        # 3. We then want to check that for the level less than this troop the req'd
        #    TH is less than or equal to current TH,
        #    and for troop level above, it requires a higher TH than we currently have.
        #    Maybe there's a better way to go about doing this.
        return self.lab_to_townhall[self.__class__.lab_level[self.level]] <= self._townhall \
             < self.lab_to_townhall[self.__class__.lab_level[self.level + 1]]

    @classmethod
    def get_max_level_for_townhall(cls, townhall):
        """Get the maximum level for a spell for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum spell level for.

        Returns
        --------
        :class:`int`
            The maximum spell level, or ``None`` if the spell hasn't been unlocked at that level.

        """
        for lab_level, th_level in cls.lab_to_townhall.items():
            if th_level != townhall:
                continue

            levels = [spell_level for spell_level, lab in enumerate(cls.lab_level, start=1) if lab <= lab_level]
            return levels and max(levels) or None

        raise ValueError("The townhall level was not valid.")


class SpellHolder(DataContainerHolder):
    items: List[Type[Spell]] = []
    item_lookup: Dict[str, Type[Spell]]

    FILE_PATH = SPELLS_FILE_PATH
    data_object = Spell

    def _load_json(self, english_aliases, lab_to_townhall):
        with open(SPELLS_FILE_PATH) as fp:
            spell_data = ujson.load(fp)
        with open(ARMY_LINK_ID_FILE_PATH) as fp:
            army_link_ids = ujson.load(fp)

        id = 2000  # fallback ID for non-standard spells
        for supercell_name, spell_meta in spell_data.items():

            if not spell_meta.get("TID"):
                continue

            # ignore deprecated content
            if True in spell_meta.get("Deprecated", [False]):
                continue
            if True in spell_meta.get("DisableProduction", [False]):
                continue
            spell_name = english_aliases[spell_meta["TID"][0]]["EN"][0]
            new_spell: Type[Spell] = type('Spell', Spell.__bases__, dict(Spell.__dict__))
            spell_id = army_link_ids.get(spell_name, id)
            if isinstance(spell_id, int):
                id += 1
            new_spell._load_json_meta(
                spell_meta,
                id=spell_id,
                name=spell_name,
                lab_to_townhall=lab_to_townhall,
            )
            self.items.append(new_spell)
            self.item_lookup[(new_spell.name, new_spell._is_home_village)] = new_spell

        self.loaded = True

    def load(self, data, townhall: int, default: "Spell" = Spell, load_game_data: bool = None) -> Spell:
        if load_game_data is True:
            try:
                spell = self.item_lookup[(data["name"], True)]
            except KeyError:
                spell = default
        else:
            spell = default

        return spell(data=data, townhall=townhall)
