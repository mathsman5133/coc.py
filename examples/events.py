from coc.ext import events

client = events.login('email', 'pass')


@client.event()
async def on_clan_member_join(member, clan):
    print('{} just joined our clan {}!'.format(member.name, clan.name))


async def on_clan_member_leave(member, clan):
    print('Oh no! {} just left our clan {}!'.format(member.name, clan.name))


async def when_someone_attacks(attack, war):
    print('{} just attacked {} for {} stars!'.format(attack.attacker.name, attack.defedender.name, attack.stars))

client.add_events(on_clan_member_join, function_dicts={when_someone_attacks: 'on_war_attack'})
client.add_clan_update(['tag', 'another tag'], member_updates=True, retry_interval=30)
client.add_war_update(['clan tag'], retry_interval=60)
client.start_updates('all')

client.run_forever()
