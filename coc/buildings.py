

class Building:
    def __init__(self, data: dict):
        self._data = data
        self.id: int = data.get("data")
        self.name: str = data.get("name")
        self.timer: int = data.get("timer", 0)
        self.level: int = data.get("lvl")
        self.count: int = data.get("cnt", 1)
        self.upgrading = self.level == 0

class SuperChargableBuilding(Building):
    def __init__(self, data: dict):
        super().__init__(data)
        self.supercharge_level: int = data.get("supercharge") + 1 if data.get("supercharge") else 0

class ResourceBuilding(SuperChargableBuilding):
    def __init__(self, data: dict):
        super().__init__(data)

        self.locked = self.level == 0

    @property
    def max_count(self):
        return ...

    @property
    def max_level(self):
        return ...

class WeaponBuilding(SuperChargableBuilding):
    def __init__(self, data: dict):
        super().__init__(data)
        self.weapon_level: int = data.get("weapon")
        self.gear_up: bool = data.get("gear", False)

    @property
    def max_count(self):
        return ...

    @property
    def max_level(self):
        return ...

class UnitBuilding(Building):
    def __init__(self, data: dict):
        super().__init__(data)

class SuperCharge(Building):
    def __init__(self, data: dict):
        super().__init__(data)
        self._data = data
        self.timer: int = data.get("timer", 0)
        self.level: int = data.get("lvl")