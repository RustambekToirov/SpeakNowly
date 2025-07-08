from tortoise import fields
from .base import BaseModel
from datetime import datetime


class TariffCategory(BaseModel):
    name = fields.CharField(max_length=255, null=False, description="Name")
    name_uz = fields.CharField(max_length=255, null=True, description="Name (Uzbek)")
    name_ru = fields.CharField(max_length=255, null=True, description="Name (Russian)")
    name_en = fields.CharField(max_length=255, null=True, description="Name (English)")
    sale = fields.DecimalField(max_digits=7, decimal_places=2, default=0, description="Sale %")
    is_active = fields.BooleanField(default=True, description="Active")

    class Meta:
        table = "tariff_categories"
        verbose_name = "Tariff Category"
        verbose_name_plural = "Tariff Categories"

    def __str__(self):
        return self.name
    
    async def __str__(self):
        return f"{self.name} ({self.sale}%)"


class Tariff(BaseModel):
    category = fields.ForeignKeyField("models.TariffCategory", related_name="tariffs", null=True, description="Category")
    name = fields.CharField(max_length=255, null=False, description="Name")
    name_uz = fields.CharField(max_length=255, null=True, description="Name (Uzbek)")
    name_ru = fields.CharField(max_length=255, null=True, description="Name (Russian)")
    name_en = fields.CharField(max_length=255, null=True, description="Name (English)")
    description = fields.TextField(null=False, description="Description")
    description_uz = fields.TextField(null=True, description="Description Uz")
    description_ru = fields.TextField(null=True, description="Description Ru")
    description_en = fields.TextField(null=True, description="Description En")
    tokens = fields.IntField(description="Tokens")
    duration = fields.IntField(default=30, description="Duration")
    old_price = fields.IntField(null=True, description="Old Price")
    price = fields.IntField(description="Price")
    is_active = fields.BooleanField(default=True, description="Active")
    is_default = fields.BooleanField(default=False, description="Default")

    @classmethod
    async def get_default_tariff(cls):
        """
        Get the default tariff.
        :return: Tariff object or None if not found.
        """
        return await cls.filter(is_default=True).first()

    class Meta:
        table = "tariffs"
        verbose_name = "Tariff"
        verbose_name_plural = "Tariffs"

    def __str__(self):
        return f"{self.name} - {self.price}"
    
    async def __str__(self):
        return f"{self.name} - {self.price}"


class Feature(BaseModel):
    name = fields.CharField(max_length=255, unique=True, null=False, description="Name")
    name_uz = fields.CharField(max_length=255, null=True, description="Name (Uzbek)")
    name_ru = fields.CharField(max_length=255, null=True, description="Name (Russian)")
    name_en = fields.CharField(max_length=255, null=True, description="Name (English)")
    description = fields.TextField(null=False, description="Description")
    description_uz = fields.TextField(null=True, description="Description Uz")
    description_ru = fields.TextField(null=True, description="Description Ru")
    description_en = fields.TextField(null=True, description="Description En")

    class Meta:
        table = "features"
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ["-id"]

    def __str__(self):
        return self.name
    
    async def __str__(self):
        return f"{self.name}"


class TariffFeature(BaseModel):
    tariff = fields.ForeignKeyField("models.Tariff", related_name="tariff_features", description="Tariff")
    feature = fields.ForeignKeyField("models.Feature", related_name="tariff_features", description="Feature")
    is_included = fields.BooleanField(default=True, description="Is Included")

    class Meta:
        table = "tariff_features"
        verbose_name = "Tariff Feature"
        verbose_name_plural = "Tariff Features"

    def __str__(self):
        return f"{self.tariff.name} - {self.feature.name}"

    async def __str__(self):
        await self.fetch_related("tariff", "feature")
        return f"{self.tariff.name} - {self.feature.name}"


class Sale(BaseModel):
    tariff = fields.ForeignKeyField("models.Tariff", related_name="sales", description="Tariff")
    percent = fields.IntField(default=0, description="Percent")
    start_date = fields.DateField(description="Start Date")
    start_time = fields.TimeField(description="Start Time")
    end_date = fields.DateField(description="End Date")
    end_time = fields.TimeField(description="End Time")
    is_active = fields.BooleanField(default=True, description="Active")

    class Meta:
        table = "sales"
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        return f"Sale {self.percent}% for {self.tariff.name}"
    
    async def __str__(self):
        return f"Sale {self.percent}% for {self.tariff.name}"
