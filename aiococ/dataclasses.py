from dateutil import parser
from datetime import datetime


def try_enum(_class, data):
    if data is None:
        return None
    return _class(data=data)


class Clan:
    """Represents the most stripped down version of clan info.
    All other clan classes inherit this.

    Attributes
    ------------
    tag: :class:`str`
        The clan tag
    name: :class:`str`
        The clan name
    badge: :class:`Badge`
        The clan badges
    """
    __slots__ = ('tag', 'name', 'badge', '_data')

    def __init__(self, data):
        self._data = data
        self.tag = data['tag']
        self.name = data['name']
        self.badge = Badge(data=data['badgeUrls'])


class BasicClan(Clan):
    """Represents a Basic Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    :location: :class:`Location` The clan location
    :level: :class:`int` The clan level.
    :points: :class:`int` The clan trophy points.
    :versus_points: :class:`int` The clan versus trophy points.
    :member_count: :class:`int` The member count of the clan
    :rank: :class:`int` The clan rank for it's location this season
    :previous_rank: :class:`int` The clan rank for it's location in the previous season
    """
    __slots__ = ('location', 'level', 'points', 'versus_points',
                 'member_count', 'rank', 'previous_rank')

    def __init__(self, data):
        super(BasicClan, self).__init__(data)
        self._from_data(data)

    def _from_data(self, data):
        self.location = try_enum(Location, data.get('location', None))
        self.level = data.get('clanLevel', None)
        self.points = data.get('clanPoints', None)
        self.versus_points = data.get('clanVersusPoints', None)
        self.member_count = data.get('members', None)
        self.rank = data.get('rank')
        self.previous_rank = data.get('previous_rank')


class SearchClan(BasicClan):
    """Represents a Basic Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    type :class:`str` The clan type: open, closed, invite-only etc.
    required_trophies: :class:`int` The required trophies to join
    war_frequency: :class:`str` The war frequency of the clan
    war_win_streak: :class:`int` The current war win streak of the clan
    war_wins: :class:`int` The total war wins of the clan
    war_ties: :class:`int` The total war ties of the clan
    war_losses: :class:`int` The total war losses of the clan
    public_war_log: :class:`bool` Indicates whether the war log is public
    description: :class:`str` The clan description
    members: :class:`list` :class:`BasicMember` List of clan members
    """
    __slots__ = ('type', 'required_trophies', 'war_frequency', 'war_win_streak',
                 'war_wins', 'war_ties', 'war_losses', 'public_war_log',
                 'description', '_members')

    def __init__(self, *, data):
        self._members = {}

        super(SearchClan, self).__init__(data=data)

        self._from_data(data)

    def _from_data(self, data):
        self.type = data.get('type', None)
        self.required_trophies = data.get('requiredTrophies', None)
        self.war_frequency = data.get('warFrequency', None)
        self.war_win_streak = data.get('warWinStreak', None)
        self.war_wins = data.get('warWins', None)
        self.war_ties = data.get('warTies', None)
        self.war_losses = data.get('warLosses', None)
        self.public_war_log = data.get('isWarLogPublic', None)

        for mdata in data.get('memberList', []):
            self._add_member(BasicPlayer(data=mdata))

    def _add_member(self, data):
        self._members[data.tag] = data

    def get_member(self, tag):
        return self._members.get(tag)

    @property
    def members(self):
        return list(self._members.values())


class WarClan(Clan):
    """Represents a Basic Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    members: :class:`list` :class:`WarMember` List of all clan members in war
    attacks: :class:`list` :class:`WarAttack` List of all attacks used this war
    defenses: :class:`list` :class:`WarAttack` List of all defenses by clan members this war
    attack_count: :class:`int` Number of attacks by clan this war
    stars: :class:`int` Number of stars by clan this war
    destruction: :class:`float` Destruction as a percentage
    exp_earned: :class:`int` Total XP earned by clan this war
    attacks_used: :class:`int` Total attacks used by clan this war
    max_stars: :class:`int` Total possible stars achievable
    """
    __slots__ = ('_war', '_members', '_attacks', '_defenses', 'level',
                 'attack_count', 'stars', 'destruction', 'exp_earned',
                 'attacks_used', 'total_attacks', 'max_stars')

    def __init__(self, *, data, war):

        self._war = war

        self._members = {}
        self._attacks = {}
        self._defenses = {}

        super(WarClan, self).__init__(data)

        self.level = data.get('clanLevel', None)
        self.attack_count = data.get('attacks', None)
        self.stars = data.get('stars', None)
        self.destruction = data.get('destructionPercentage', None)
        self.exp_earned = data.get('expEarned', None)

    def _from_data(self, data):
        self.attacks_used = data.get('attacks')
        self.total_attacks = self._war.war_size * 2
        self.stars = data.get('stars')
        self.max_stars = self._war.war_size * 3
        self.destruction = []

        for mdata in data.get('members', []):
            member = WarMember(data=mdata, war=self._war)
            self._add_member(member)

    def _add_member(self, data):
        self._members[data.tag] = data

    def _add_attack(self, data):
        if data.attacker_tag in self._attacks.keys():
            self._attacks[data.attacker_tag].append(data)
        else:
            self._attacks[data.attacker_tag] = [data]

    def _add_defense(self, data):
        if data.defender_tag in self._defenses.keys():
            self._defenses[data.defender_tag].append(data)
        else:
            self._defenses[data.defender_tag] = [data]

    def _find_add_defender(self, data):
        defender_tag = data.defender_tag
        member = self._war.get_member(defender_tag)
        member._add_defense(data)

    def _load_attacks(self):
        for member in self._members:
            for attack in member.attacks:
                self._add_attack(attack)
                self._find_add_defender(attack)

    @property
    def members(self):
        return list(self._members.values())

    @property
    def attacks(self):
        return list(self._attacks.values())

    @property
    def defenses(self):
        return list(self._defenses.values())


class Player:
    """Represents the most stripped down version of a Player
    All other player classes inherit this.


    Attributes
    ------------
    tag: :class:`str`
        The clan tag
    name: :class:`str`
        The clan name
    """
    __slots__ = ('name', 'tag', '_data')

    def __init__(self, data):
        self._data = data
        self.name = data['name']
        self.tag = data['tag']

    def __str__(self):
        return self.name


class BasicPlayer(Player):
    """Represents a Basic Player that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    clan: :class:`Basic Clan` The clan the member belongs to. May be ``None``
    level: :class:`int` The player level.
    trophies: :class:`int` The player's trophy count.
    versus_trophies: :class:`int` The player's versus trophy count.
    role: :class:`str` The members role in the clan - member, elder, etc.
    clan_rank: :class:`int` The members clan rank
    clan_previous_rank :class:`int` The members clan rank last season
    league_rank: :class:`int` The player's current rank in their league for this season
    donations: :class:`int` The members current donation count
    received: :class:`int` The member's current donation received count
    attack_wins: :class:`int` The players current attack wins for this season
    defense_wins: :class:`int` The players current defense wins for this season
    """
    __slots__ = ('clan', 'level', 'league', 'trophies', 'versus_trophies', 'role',
                 'clan_rank', 'clan_previous_rank', 'league_rank', 'donations',
                 'received', 'attack_wins', 'defense_wins')

    def __init__(self, *, data, clan=None):
        self.clan = clan

        super(BasicPlayer, self).__init__(data)
        self._add_data(data)

    def _add_data(self, data):
        self.level = data.get('expLevel', None)
        self.league = try_enum(League, data.get('league', None))
        self.trophies = data.get('trophies', None)
        self.versus_trophies = data.get('versusTrophies', None)
        self.role = data.get('role', None)
        self.clan_rank = data.get('clanRank', None)
        self.clan_previous_rank = data.get('clanRank', None)
        self.league_rank = data.get('rank', None)
        self.donations = data.get('donations', None)
        self.received = data.get('donationsReceived', None)
        self.attack_wins = data.get('attackWins', None)
        self.defense_wins = data.get('defenseWins', None)

        if not self.clan:
            cdata = data.get('clan')
            if cdata:
                self.clan = BasicClan(data=cdata)


class WarMember(Player):
    """Represents a Basic Player that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    town_hall: :class:`int` The members TH level
    map_position: :class:`int` The members map position this war
    attacks: :class:`list` :class: `WarAttack` The member's attacks this war. Could be an empty list
    war: :class:`War` The war this member belongs to
    """
    __slots__ = ('town_hall', 'map_position', 'attacks', 'war')

    def __init__(self, data, war):
        self.attacks = []

        super(WarMember, self).__init__(data)

        self.town_hall = data.get('townHallLevel', None)
        self.map_position = data.get('mapPosition', None)

        for adata in data.get('attacks', []):
            self.attacks.append(WarAttack(data=adata, war=war, member=self))


class SearchPlayer(BasicPlayer):
    """Represents a Basic Player that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    achievements: :class:`list` :class:`Achievement` List of the player's achievements
    troops: :class:`list` :class:`Troop` List of the player's troops
    heroes: :class:`list` :class:`Hero` List of the player's heroes
    spells: :class:`list` :class:`Spell` List of the player's spells
    best_trophies: :class:`int` The players top trophy count
    best_versus_trophies: :class:`int` The players top versus trophy count
    war_stars: :class:`int` The players war star count
    town_hall: :class:`int` The players TH level
    builder_hall: :class:`int` The players BH level
    versus_attacks_wins: :class:`int` The players total BH wins
    """
    __slots__ = ('_achievements', '_troops', '_heroes', '_spells',
                 'best_trophies', 'war_stars', 'town_hall',
                 'builder_hall', 'best_versus_trophies', 'versus_attacks_wins')

    def __init__(self, *, data):
        self._achievements = {}
        self._troops = {}
        self._heroes = {}
        self._spells = {}

        super(SearchPlayer, self).__init__(data=data)

    def _add_data(self, data):
        self.clan = try_enum(Clan, data.get('clan', None))
        self.best_trophies = data.get('bestTrophies', None)
        self.war_stars = data.get('warStars', None)
        self.town_hall = data.get('townHallLevel', None)
        self.builder_hall = data.get('builderHallLevel', None)
        self.best_versus_trophies = data.get('bestVersusTrophies', None)
        self.versus_attacks_wins = data.get('versusBattleWins', None)

        for adata in data.get('achievements', []):
            achievement = Acheivement(data=adata, player=self)
            self._add_achievement(achievement)

        for tdata in data.get('troops', []):
            troop = Troop(data=tdata, player=self)
            self._add_troop(troop)

        for hdata in data.get('heroes', []):
            hero = Hero(data=hdata, player=self)
            self._add_hero(hero)

        for sdata in data.get('spells', []):
            spell = Spell(data=sdata, player=self)
            self._add_spell(spell)

    def _add_achievement(self, data):
        self._achievements[data.name] = data

    def _add_troop(self, data):
        self._troops[data.name] = data

    def _add_hero(self, data):
        self._heroes[data.name] = data

    def _add_spell(self, data):
        self._spells[data.name] = data

    @property
    def achievements(self):
        return list(self._achievements.values())

    @property
    def troops(self):
        return list(self._troops.values())

    @property
    def heroes(self):
        return list(self._heroes.values())

    @property
    def spells(self):
        return list(self._spells.values())


class BaseWar:
    __slots__ = ('team_size', 'clan', 'opponent', '_data')

    def __init__(self, *, data):
        self._data = data
        self._from_data(data)

    def _from_data(self, data):
        self.team_size = data.get('teamSize', None)

        clan = data.get('clan', None)
        if clan:
            self.clan = WarClan(data=clan, war=self)
        else:
            self.clan = None

        opponent = data.get('opponent', None)
        if opponent:
            self.opponent = WarClan(data=opponent, war=self)
        else:
            self.opponent = None


class WarLog(BaseWar):
    __slots__ = ('result', 'end_time')

    def __init__(self, *, data):
        super(WarLog, self).__init__(data=data)

    def _from_data(self, data):
        self.result = data.get('result')
        self.end_time = try_enum(Timestamp, data.get('endTime'))


class CurrentWar(BaseWar):
    __slots__ = ('state', 'preparation_start_time',
                 'start_time', 'end_time')

    def __init__(self, *, data):
        super(CurrentWar, self).__init__(data=data)

    def _from_data(self, data):
        self.state = data.get('state')
        self.preparation_start_time = try_enum(Timestamp, data.get('preparationStartTime'))
        self.start_time = try_enum(Timestamp, data.get('startTime'))
        self.end_time = try_enum(Timestamp, data.get('endTime'))

    @property
    def attacks(self):
        a = [].extend(self.clan.attacks).extend(self.opponent.attacks)
        a.sort(key=lambda o: o.order)
        return a

    @property
    def members(self):
        m = [].extend(self.clan.members).extend(self.opponent.members)
        return m


class Acheivement:
    """Represents a Clash of Clans Hero.

    Attributes
    -----------
    player: :class:`SearchPlayer` The player this achievement is assosiated with
    name: :class:`str` The name of the hero
    stars: :class:`int` The current stars achieved for the achievement
    value: :class:`int` The number of X things attained for this achievement
    target: :class:`int` The number of X things required to complete this achievement
    info: :class:`str` Information regarding the achievement
    completion_info: :class:`str` Information regarding completion of the achievement
    village: :class:`str` Either `home` or `builderBase`
    is_completed: :class:`bool` Indicates whether the achievement is completed (3 stars achieved)
    is_home_base: :class:`bool` Helper property to tell you if the achievement belongs to the home base
    is_builder_base: :class:`bool` Helper property to tell you if the achievement belongs to the builder base
    """

    __slots__ = ('player', 'name', 'stars', 'value', 'target',
                 'info', 'completion_info', 'village')

    def __init__(self, *, data, player):
        self.player = player
        self._from_data(data)

    def _from_data(self, data):
        self.name = data['name']
        self.stars = data.get('stars')
        self.value = data['value']
        self.target = data['target']
        self.info = data['info']
        self.completion_info = data.get('completionInfo')
        self.village = data['village']

    @property
    def is_builder_base(self):
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        return self.village == 'home'

    @property
    def is_completed(self):
        return self.stars == 3


class Troop:
    """Represents a Clash of Clans Troop.

    Attributes
    -----------
    player: :class:`SearchPlayer` The player this troop is assosiated with
    name: :class:`str` The name of the troop
    level: :class:`int` The level of the troop
    max_level: :class:`int` The overall max level of the troop, excluding townhall limitations
    village: :class:`str` Either `home` or `builderBase`
    is_max: :class:`bool` Indicates whether the troop is maxed overall, excluding townhall limitations
    is_home_base: :class:`bool` Helper property to tell you if the troop belongs to the home base
    is_builder_base: :class:`bool` Helper property to tell you if the troop belongs to the builder base
    """
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village')

    def __init__(self, *, data, player):
        self.player = player
        self._from_data(data)

    def _from_data(self, data):
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        return self.village == 'home'


class Hero:
    """Represents a Clash of Clans Hero.

    Attributes
    -----------
    player: :class:`SearchPlayer` The player this hero is assosiated with
    name: :class:`str` The name of the hero
    level: :class:`int` The level of the hero
    max_level: :class:`int` The overall max level of the hero, excluding townhall limitations
    village: :class:`str` Either `home` or `builderBase`
    is_max: :class:`bool` Indicates whether the hero is maxed overall, excluding townhall limitations
    is_home_base: :class:`bool` Helper property to tell you if the hero belongs to the home base
    is_builder_base: :class:`bool` Helper property to tell you if the hero belongs to the builder base
    """
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village')

    def __init__(self, *, data, player: Player):
        self.player = player
        self._from_data(data)

    def _from_data(self, data):
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        return self.level == self.max_level

    @property
    def is_builder_base(self):
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        return self.village == 'home'


class Spell:
    """Represents a Clash of Clans Spell.

    Attributes
    -----------
    player: :class:`SearchPlayer` The player this spell is assosiated with
    name: :class:`str` The name of the spell
    level: :class:`int` The level of the spell
    max_level: :class:`int` The overall max level of the spell, excluding townhall limitations
    village: :class:`str` Either `home` or `builderBase`
    is_max: :class:`bool` Indicates whether the spell is maxed overall, excluding townhall limitations
    is_home_base: :class:`bool` Helper property to tell you if the spell belongs to the home base
    is_builder_base: :class:`bool` Helper property to tell you if the spell belongs to the builder base
    """
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village')

    def __init__(self, *, data, player):
        self.player = player
        self._from_data(data)

    def _from_data(self, data):
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        return self.village == 'home'


class WarAttack:
    """
    Represents a Clash of Clans War Attack

    Attributes
    -----------
    war: :class:`War` The war this attack belongs to
    stars: :class:`int` The stars achieved
    destruction: :class:`float` The destruction achieved as a percentage (of 100)
    order: :class:`int` The attack order in this war
    attacker_tag: :class:`int` The attacker tag
    defender_tag: :class:`int` The defender tag
    attacker: :class:`WarMember` The attacker
    defender: :class:`WarMember` The defender

    """
    __slots__ = ('war', 'member', 'stars',
                 'destruction', 'order',
                 'attacker_tag', 'defender_tag')

    def __init__(self, *, data, war, member):
        self.war = war
        self.member = member
        self._add_data(data=data)

    def _add_data(self, data):
        self.stars = data['stars']
        self.destruction = data['destructionPercentage']
        self.order = data['order']
        self.attacker_tag = data['attackerTag']
        self.defender_tag = data['defenderTag']

    @property
    def attacker(self):
        return self.war.get_member(self.attacker_tag)

    @property
    def defender(self):
        return self.war.get_member(self.defender_tag)


class Location:
    """Represents a Clash of Clans Location

    Attributes
    -----------
    id: :class:`str` The location ID
    name: :class:`str` The location name
    is_country: :class:`bool` Indicates whether the location is a country
    country_code: :class:`str` The shorthand country code, if the location is a country
    """
    __slots__ = ('id', 'name', 'is_country', 'country_code')

    def __init__(self, *, data):
        self._from_data(data=data)

    def __str__(self):
        return self.name

    def _from_data(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.is_country = data.get('isCountry')
        self.country_code = data.get('countryCode')


class League:
    """Represents a Clash of Clans League

    Attributes
    -----------
    id: :class:`str` The league ID
    name: :class:`str` The league name
    badge: :class:`Badge` The league badge
    """
    __slots__ = ('id', 'name', 'badge')

    def __init__(self, *, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.badge = try_enum(Badge, data=data.get('iconUrls', None))

    def __str__(self):
        return self.name


class LeagueRankedPlayer(BasicPlayer):
    """Represents a league ranked player; a basic player with a rank

    Attributes
    -----------
    rank: :class:`int` The players rank in their league for this season
    """
    def __init__(self, *, data):
        self.rank = data.get('rank', None)
        super(LeagueRankedPlayer, self).__init__(data=data)


class Season:
    """Represents a Clash of Clans Season

    rank: """
    __slots__ = ('rank', 'trophies', 'id')

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data):
        self.rank = data['rank']
        self.trophies = data['trophies']
        self.id = data['id']


class LegendStatistics:
    __slots__ = ('player', 'legend_trophies', 'current_season',
                 'previous_season', 'best_season')

    def __init__(self, *, data, player):
        self.player = player
        self._from_data(data)

    def _from_data(self, data):
        self.legend_trophies = data['legendTrophies']
        self.current_season = try_enum(Season, data=data.get('currentSeason', None))
        self.previous_season = try_enum(Season, data=data.get('previousSeason', None))
        self.best_season = try_enum(Season, data=data.get('bestSeason', None))


class Badge:
    __slots__ = ('small', 'medium', 'large', 'url')

    def __init__(self, *, data):
        self.small = data.get('small')
        self.medium = data.get('medium')
        self.large = data.get('large')

        self.url = self.medium

    async def save(self, fp, size=None):
        sizes = {'small': self.small,
                 'medium': self.medium,
                 'large': self.large}

        if size and size in sizes.keys():
            url = sizes[size]
        else:
            url = self.medium

        # data = await utils.save_url(url)
        #
        # with open(fp, 'wb') as f:
        #     return f.write(data)


class Timestamp:
    __slots__ = 'time'

    def __init__(self, *, data):
        self.time = data

    @property
    def utc_timestamp(self):
        return parser.parse(self.time)

    @property
    def now(self):
        return datetime.utcnow()

    @property
    def seconds_until(self):
        delta = self.utc_timestamp - self.now
        return delta.total_seconds()


class LeaguePlayer:
    def __init__(self, *, data):
        self.tag = data.get('tag')
        self.name = data.get('name')
        self.town_hall = data.get('townHall')


class LeagueClan(BasicClan):
    def __init__(self, *, data):
        self._members = {}

        super(LeagueClan, self).__init__(data)


        for mdata in data.get('members', []):
            self._add_member(LeaguePlayer(data=mdata))

    def _add_member(self, data):
        self._members[data.tag] = data

    @property
    def members(self):
        return list(self._members.values())


class LeagueGroup:
    def __init__(self, *, data):
        self._clans = {}
        self._rounds = []
        self._from_data(data)

    def _from_data(self, data):
        self.tag = data.get('tag', None)
        self.state = data.get('state', None)
        self.season = data.get('season', None)

        for cdata in data.get('clans', []):
            self._add_clan(cdata)

        for rdata in data.get('rounds', []):
            self._add_round(rdata)

    def _add_clan(self, data):
        self._clans[data.tag] = data

    def _add_round(self, data):
        self._rounds.append(data['warTags'])

    @property
    def clans(self):
        return list(self._clans.values())

    @property
    def rounds(self):
        return self._rounds


class LeagueWar(CurrentWar):
    def __init__(self, *, data):
        super(LeagueWar, self).__init__(data=data)
        self.tag = data.get('tag', None)
