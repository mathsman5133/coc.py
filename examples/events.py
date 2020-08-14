import coc

client = coc.login("email", "pass", client=coc.EventsClient)


@client.event
async def on_clan_member_join(member, clan):
    print("{} just joined our clan {}!".format(member.name, clan.name))

@client.event
async def on_clan_member_leave(member, clan):
    print("Oh no! {} just left our clan {}!".format(member.name, clan.name))

@client.event
async def on_war_attack(attack, war):
    print(
        "{} just attacked {} for {} stars! It was a {} war.".format(
            attack.attacker.name, attack.defedender.name, attack.stars, war.type
        )
    )

tags = ["#tag", "#tag2", "#tag3"]
client.add_clan_update(tags, retry_interval=30)
client.add_war_update(tags, retry_interval=300)

client.run_forever()
