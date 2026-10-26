from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from farms.models import Farm
from rabbits.models import Group, Rabbit
from events.models import Event


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
