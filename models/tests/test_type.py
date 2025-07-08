from enum import Enum
from tortoise import fields
from tortoise.models import Model

class TestTypeEnum(str, Enum):
    """Enumeration for different types of tests."""
    READING_ENG = "reading"
    SPEAKING_ENG = "speaking"
    WRITING_ENG = "writing"
    LISTENING_ENG = "listening"

class TestType(Model):
    """Model representing a type of test with its price and trial price."""
    id = fields.IntField(pk=True)
    type = fields.CharEnumField(
        enum_type=TestTypeEnum,
        max_length=20,
        description="Type of the test"
    )
    price = fields.IntField(description="Price per test")
    trial_price = fields.IntField(description="Trial price")

    class Meta:
        table = "test_type"

    def __str__(self):
        return self.type
