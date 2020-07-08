.. currentmodule:: coc

.. _custom_classes:

Custom Classes
==============

Custom classes are a simple, easy way to override the inbuilt objects to suit your needs.
Internal objects have been adapted and designed with easy subclassing in mind.

Custom class objects should be passed in on every client call, and the objects returned will be an instance of your custom class.
For the EventsClient, please see the custom class section below for more implentation details.

Basic Usage
-----------
A common use could be either creating a new attribute or overriding the client's implentation of a player's role.

.. code-block:: python3

    class MyCustomPlayer(coc.Player):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.role_as_string = str(self.role)

    player = await client.get_player("#tag", cls=MyCustomPlayer)
    print("{0.name}'s role in the clan is {0.role_as_string}".format(player))


Another common use is a utility function that returns a nice list of a clan's members.

.. code-block:: python3

    class MyCustomClan(coc.Clan):
        def format_members(self):
            fmt = ""
            for index, member in enumerate(self.members, start=1):
                fmt += f"{index}. {member.name} ({member.tag}) | Trophies: {member.trophies}\n"
            return fmt

    clan = await client.get_clan("#tag", cls=MyCustomClan)
    print(clan.format_members())

Custom Classes for Nested Objects
---------------------------------

The obvious question when dealing with custom classes is how to override a nested object.
For example, how do I tell the library to use my custom implentation of a :class:`ClanMember`?
Most objects have attributes that define what the class object is, and the suggested way of doing this is overriding them.

For example:

.. code-block:: python3

    class MyCustomClanMember(coc.ClanMember):
        @property
        def donation_ratio(self):
            if received == 0:
                return self.donations  # we can't divide by 0!
            return self.donations / self.received

    class CustomClan(coc.Clan):
        def __init__(self, **kwargs):
            self.member_cls = MyCustomClanMember  # this must be above the __init__ call.
            super().__init__(self, **kwargs)

    clan = await client.get_clan("#tag", cls=CustomClan)
    for member in clan.members:
        print(member.donation_ratio)

Another example is overriding the default :class:`Hero` class:

.. code-block:: python3

    class CustomHero(coc.Hero):
        def format(self):
            return f"{self.name} | {self.level}/{self.max_level}"

    class CustomPlayer(coc.Player):
        def __init__(self, **kwargs):
            self.hero_cls = CustomHero  # this must be above the __init__ call.
            super().__init__(**kwargs)

    player = await client.get_player("#tag", cls=CustomPlayer)
    for hero in player.heroes:
        print(hero.format() + "\n")

Care should be taken to ensure that setting of the nested custom class is **above** the ``super().__init__`` call,
otherwise the default class will be used instead of your custom implementation.
An alternative way which ensures you don't accidentally put it below is by setting it as a property:

.. code-block:: python3

    class CustomPlayer(coc.Player):
        @property
        def achievement_cls(self):
            return CustomAchievementClass


Passing in Arguments to Custom Classes
--------------------------------------
Stateful classes and other arguments passed are often necessary to complete methods in these custom classes.

For example, you may wish to make a database query, and passing in the database / connection / cursor may not always be trivial.

The library allows you to pass any kwargs you wish to be passed into the ``__init__`` of your custom class when calling the client method.

For example:

.. code-block:: python3

    class MyCustomClan(coc.Clan):
        def __init__(self, **kwargs):
            database = kwargs.pop("database")

        def get_something_from_database(self):
            return self.database.get("something")

    clan = await client.get_clan("#tag", cls=MyCustomClan, database=my_database_instance)
    clan.get_something_from_database()

This was a trivial example, but more complicated examples follow the same basic structure.


Memory Optimisations
--------------------
The library has been built to facilitate and support 100% of the Clash of Clans API.

There are times, however, when you will not need every part of the API and this support becomes a burden.

Custom classes, especially when used with the Events Client are a powerful way to reduce the library's memory footprint,
and increase performance. The library has been optimised in both speed and memory, however removing things will ultimately
speed anything up.

However, take care when overriding custom classes for this purpose as you may unintentionally break other parts of the object.
In short, only do this if you know what you're doing!

Nonetheless, a few simple examples follow:

.. code-block:: python3

    class CustomClanMember(coc.ClanMember):
        def __init__(self, data, client, **kwargs):
            self._from_data(data)

        def _from_data(data):
            self.tag = data["tag"]
            self.name = data["name"]
            self.donations = data["donations"]
            self.received = data["received"]

    class CustomClan(coc.Clan):
        def _from_data(data):
            self._members = {m["tag"]: CustomClanMember(data=m, client=client) for m in data["memberList"])}

    @client.event
    @coc.ClanEvents.member_donations(custom_cls=CustomClan)
    @coc.ClanEvents.member_received()
    @coc.ClanEvents.member_name()
    async def foo(...): ...

This example above will dramatically reduce the memory consumption of the Events Client, by only storing the attributes
of the clan member that the events require.

However, this can lead to hard-to-trace bugs and the like.


.. _events_custom_class:
Custom Classes in Events
------------------------
In a similar way to tags and retry intervals, custom classes can be set via the decorator,
or by assigning the attribute.

For example:

.. code-block:: python3

    class MyCustomPlayer(coc.Player):
        ...

    @client.event
    @coc.PlayerEvents.name(custom_cls=MyCustomPlayer)
    async def foo(...): ...

    # alternatively,

    @client.event
    @coc.PlayerEvents.name()
    async def foo(...): ...

    client.player_cls = MyCustomPlayer

As with tags and intervals, if you set a custom class on one event decorator, it will influence every event in that group.

