from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Rabbit, PedigreeNode


@receiver(post_save, sender=Rabbit)
def create_rabbit_pedigree_node(sender, instance, **kwargs):
    PedigreeNode.objects.get_or_create(
        rabbit=instance,
       defaults={
    "is_manual": False,
    "farm": instance.farm,
},
    )