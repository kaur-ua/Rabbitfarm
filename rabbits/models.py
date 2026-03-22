from django.db import models
from django.contrib.auth.models import User
from farms.models import Farm
from datetime import date




class Rabbit(models.Model):
    farm = models.ForeignKey(
         Farm,
         on_delete=models.CASCADE,
         related_name="rabbits"
    )
    SEX_CHOICES = [
         ("F", "Самка"),
         ("M", "Самець"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Активний"),
        ("SOLD", "Проданий"),
        ("CULLED", "Вибракований"),
    ]

    

    name = models.CharField(max_length=100)
    inventory_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Інвентарний номер"
    ) 
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES
    )

    breed = models.CharField(max_length=100, blank=True)

    cage = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    mother = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_mother"
    )

    father = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_father"
    )

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Вага"
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


