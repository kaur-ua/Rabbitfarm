from django.db import models
from django.contrib.auth.models import User
from farms.models import Farm
from datetime import date
from django.utils.translation import gettext_lazy as _


class Group(models.Model):
    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    cage_number = models.CharField(max_length=50, blank=True)

    photo = models.ImageField(upload_to='rabbit_photos/', blank=True, null=True)

    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="groups"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def rabbits_count(self):
        return self.rabbits.count()


class Rabbit(models.Model):
    farm = models.ForeignKey(
         Farm,
         on_delete=models.CASCADE,
         related_name="rabbits"
            )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rabbits",
        verbose_name=_("Group")
            )
    SEX_CHOICES = [
        ("F", _("Female")),
        ("M", _("Male")),
        ("U", _("Unknown")),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", _("Active")),
        ("SOLD", _("Sold")),
        ("CULLED", _("Culled")),
    ]



    name = models.CharField(max_length=100, verbose_name=_("Name"))
    inventory_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Inventory Number")
    )
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES,
        verbose_name=_("Sex")
    )

    breed = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Breed")
    )

    cage = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Cage")
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name=_("Status")
    )

    mother = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_mother",
        verbose_name=_("Mother")
    )

    mother_manual = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Mother (manual)")
    )

    father = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_father",
        verbose_name=_("Father")
    )
    father_manual = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Father (manual)")
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Birth date")
    )

    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Weight")
    )

    photo = models.ImageField(
        upload_to='rabbit_photos/',
        blank=True,
        null=True,
        verbose_name=_("Photo")
    )

    created_at = models.DateTimeField(auto_now_add=True)


    @property
    def event_status(self):
        last_event = self.events.order_by('-date').first()

        if last_event and last_event.next_action_date:
            days_left = (last_event.next_action_date - date.today()).days

            if days_left <= 3:
                return 'critical'
            elif days_left <= 10:
                return 'warning'
            else:
                return 'normal'

        return 'none'

    def save(self, *args, **kwargs):
        if not self.inventory_number:
            last_rabbit = Rabbit.objects.order_by("-id").first()

            if last_rabbit and last_rabbit.inventory_number:
                self.inventory_number = str(int(last_rabbit.inventory_number) + 1).zfill(4)
            else:
                self.inventory_number = "0001"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


