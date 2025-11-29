.. currentmodule:: coc
.. _migrating_to_v4_0:

Migrating to coc.py v4.0
========================

Most of the outward facing library is the same, with a few changes detailed below. Significant changes are caused
by a large static data update, support for army recipes, and a bump to 3.10 minimum python version.

Static Data
-----------

Static data is now always loaded into the client for use with :func:`coc.Client.parse_army_link`,
:func:`coc.Client.parse_account_data`, & other static data relying functions. Injection into :class:`coc.Troop`,
:class:`coc.Hero`, and other item classes still only happens when set to do so.

The function :func:`coc.Client.create_army_link` was removed.

The changes to :class:`coc.Troop` and similar classes are minor, but some attributes may be different:

- different typing (like from :class:`str` to :class:`coc.enums.VillageType`)
- new attributes (like :attr:`coc.Spell.duration`)
- removed attributes (like :attr:`coc.Troop.training_time`)

Consult the docs to see what has changed. The documentation has been vastly improved to include both new & missing info.

New Classes/Functions
---------------------

- :class:`coc.ArmyRecipe` for use with parsed army links (:func:`coc.Client.parse_army_link`)
- :class:`coc.AccountData` for use with parsed account data (:func:`coc.Client.parse_account_data`)
- :class:`coc.StaticData` for use with parsed static data (can be accessed via :attr:`coc.Client.static_data`)
- :class:`coc.Translation` for translations of item names & descriptions (:func:`coc.Client.get_translation`)
- :class:`coc.ExtendedCWLGroup` for group CWL medal & promotion data (:func:`coc.Client.get_extended_cwl_group_data`)

- :class:`coc.Building`, :class:`coc.Trap`, :class:`coc.Guardian`, :class:`coc.Helper`, :class:`coc.Scenery`,
  :class:`coc.Skin`, :class:`coc.Decoration`, :class:`coc.Obstacle` and :class:`coc.ClanCapitalHousePart` added for use
  with parsed static data
- :class:`coc.Pet` added instead of using :class:`coc.Hero` for pets

Constant/Enums
--------------

Coc.py game data was updated and now includes all the recently added troops & heros. Any lists that used to be
in ``coc.enums`` now reside in ``coc.constants``. Internally these constants are now dynamically generated from static
data to ensure consistent & easy updates. Additionally, the following were added:

- :class:`coc.SEASONAL_SPELL_ORDER`
- :class:`coc.SEASONAL_TROOP_ORDER`
- :class:`coc.Resource` updated with new Resource types
- :class:`coc.SceneryType` added
- :class:`coc.EquipmentRarity` added
- :class:`coc.SkinTier` added
- :class:`coc.Gender` added
- :class:`coc.BuildingType` added
- :class:`coc.ProductionBuildingType` added

