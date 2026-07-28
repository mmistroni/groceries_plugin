# enums.py
from enum import IntEnum
from sqlalchemy import TypeDecorator, Integer

class ExpenseTypeEnum(IntEnum):
    HOUSE_INSURANCE = 0
    PHONE_MEDIA = 1
    APPLIANCES_INSURANCE_PENSIONS = 3
    WATER_UTILITIES = 5
    GAS_ENERGY = 6
    CAR_TRANSPORT = 8
    COUNCIL_TAX = 9
    TV_LICENSE = 10
    MORTGAGE_SCHOOLING = 11
    OTHER = 13

    @classmethod
    def from_code(cls, code: int | None) -> "ExpenseTypeEnum | None":
        if code is None:
            return None
        try:
            return cls(code)
        except ValueError:
            return cls.OTHER

    @property
    def display_name(self) -> str:
        return self.name.replace('_', ' ').title()


class ExpenseTypeColumn(TypeDecorator):
    """Safely maps raw DB integers to Python ExpenseTypeEnum."""
    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ExpenseTypeEnum):
            return value.value
        return int(value)

    def process_result_value(self, value, dialect):
        return ExpenseTypeEnum.from_code(value)