from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from farms.models import Farm
from rabbits.models import Group, Rabbit
from events.models import Event
from datetime import date


class DeleteEventFarmIsolationTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="farmer1",
            password="test-password",
        )
        self.farm1 = Farm.objects.create(
            name="Farm One",
            owner=self.user1,
        )

        self.user2 = User.objects.create_user(
            username="farmer2",
            password="test-password",
        )
        self.farm2 = Farm.objects.create(
            name="Farm Two",
            owner=self.user2,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm2,
            name="Other Farmer Rabbit",
            sex="F",
        )
        self.event = Event.objects.create(
            rabbit=rabbit,
            event_type="vaccination",
            date="2026-10-25",
        )

    def test_farmer_cannot_delete_another_farms_event(self):
        self.client.login(
            username="farmer1",
            password="test-password",
        )

        response = self.client.post(
            reverse("delete_event", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_farmer_can_delete_own_event(self):
        self.client.login(
            username="farmer2",
            password="test-password",
        )

        response = self.client.post(
            reverse("delete_event", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_farmer_cannot_create_event_for_another_farms_group(self):
        group = Group.objects.create(
            name="Other Farm Group",
            farm=self.farm2,
        )

        self.client.login(
            username="farmer1",
            password="test-password",
        )

        response = self.client.post(
            reverse("add_event"),
            {
                "group": group.pk,
                "event_type": "vaccination",
                "date": "2026-10-25",
                "note": "Isolation test",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Event.objects.filter(group=group).exists()
        )

    def test_farmer_cannot_open_another_farms_group_event_form(self):
        group = Group.objects.create(
            name="Other Farm Group",
            farm=self.farm2,
        )

        self.client.login(
            username="farmer1",
            password="test-password",
        )

        response = self.client.get(
            reverse("create_group_event", args=[group.pk])
        )

        self.assertEqual(response.status_code, 404)

class KindlingOffspringBreedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="breeder",
            password="test-password",
        )
        self.farm = Farm.objects.create(
            name="Test Farm",
            owner=self.user,
        )

        self.mother = Rabbit.objects.create(
            farm=self.farm,
            name="Marusia",
            sex="F",
            breed="New Zealand White",
        )
        self.father = Rabbit.objects.create(
            farm=self.farm,
            name="Borya",
            sex="M",
            breed="New Zealand Blue",
        )

    def test_offspring_of_different_breeds_is_cross(self):
        Event.objects.create(
            rabbit=self.mother,
            male=self.father,
            event_type="mating",
            date=date(2026, 10, 1),
        )

        self.client.login(
            username="breeder",
            password="test-password",
        )

        response = self.client.post(
            reverse("add_event"),
            {
                "rabbit": self.mother.pk,
                "event_type": "kindling",
                "date": date(2026, 10, 29),
                "born_alive": 2,
                "born_dead": 0,
            },
        )

        self.assertEqual(response.status_code, 302)

        babies = Rabbit.objects.filter(mother=self.mother)
        self.assertEqual(babies.count(), 2)

        for baby in babies:
            self.assertEqual(baby.breed, "Cross")
            self.assertEqual(baby.father_id, self.father.pk)

            node = baby.pedigree_node
            self.assertEqual(node.mother.rabbit, self.mother)
            self.assertEqual(node.father.rabbit, self.father)

    def test_offspring_of_same_breed_inherits_parent_breed(self):
        self.father.breed = "New Zealand White"
        self.father.save()

        Event.objects.create(
            rabbit=self.mother,
            male=self.father,
            event_type="mating",
            date=date(2026, 10, 1),
        )

        self.client.login(
            username="breeder",
            password="test-password",
        )

        self.client.post(
            reverse("add_event"),
            {
                "rabbit": self.mother.pk,
                "event_type": "kindling",
                "date": date(2026, 10, 29),
                "born_alive": 1,
                "born_dead": 0,
            },
        )

        baby = Rabbit.objects.get(mother=self.mother)
        self.assertEqual(baby.breed, "New Zealand White")

    def test_offspring_with_unknown_parent_breed_is_unknown(self):
        self.father.breed = ""
        self.father.save()

        Event.objects.create(
            rabbit=self.mother,
            male=self.father,
            event_type="mating",
            date=date(2026, 10, 1),
        )

        self.client.login(
            username="breeder",
            password="test-password",
        )

        self.client.post(
            reverse("add_event"),
            {
                "rabbit": self.mother.pk,
                "event_type": "kindling",
                "date": date(2026, 10, 29),
                "born_alive": 1,
                "born_dead": 0,
            },
        )

        baby = Rabbit.objects.get(mother=self.mother)
        self.assertEqual(baby.breed, "Unknown")