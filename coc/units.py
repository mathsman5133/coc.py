
class Unit:
    def __init__(self, data: dict):
        self._id = data.get("id")
        self._timestamp = data.get("timestamp")
        self.name: str = data.get("name")
        self.level: int = data.get("level")

class Equipment(Unit):
    def __init__(self, data: dict):
        super().__init__(data=data)

        self.required_blacksmith_level: int = data.get("requiredBlacksmithLevel")
        self.shiny_ore: int = data.get("shinyOre")
        self.glowy_ore: int = data.get("glowyOre")
        self.starry_ore: int = data.get("starryOre")
        self.rarity: str = data.get("rarity")

        self.allowed_hero: str = data.get("allowedHero")

        self.damage_per_second: int = data.get("dps")
        self.attack_speed: int = data.get("attackSpeedPercentage")
        self.hitpoints: int = data.get("hitPoints")
        self.heal_per_second: int = data.get("healPerSecond")
        self.heal_on_activation: int = data.get("healOnActivation")

        self.abilities: list[Ability] = ...



class Ability():
    def __init__(self, data: dict):
        ...

class TroopSpawnerAbility(Ability):
    def __init__(self, data: dict):
        super().__init__(data)

class ProjectileAbility(Ability):
    def __init__(self, data: dict):
        super().__init__(data)
        self.damage: int = data.get("damage")

class SpellAbility(Ability):
    def __init__(self, data: dict):
        super().__init__(data)
        self.activation_time: int = data.get("time")
        self.speed_boost: int = data.get("speedBoost")
        self.radius: int = data.get("radius")