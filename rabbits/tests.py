from django.test import TestCase
from django.contrib.auth.models import User
from farms.models import Farm
from events.models import Event
from rabbits.models import Rabbit, RabbitBreed
from rabbits.services import (
    check_pair_relatedness,
    evaluate_pairing,
    get_mating_readiness,
    get_pairing_candidates,
    get_recommended_pairs,
    INSUFFICIENT_DATA,
    NOT_READY,
    READY,
)
from datetime import date

class PairRelatednessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testbreeder",
            password="test-password",
        )
        self.farm = Farm.objects.create(
            name="Test Farm",
            owner=self.user,
        )

    def create_rabbit(self, name=None, sex="F", **kwargs):
        if name is None:
            name = f"Test Rabbit {Rabbit.objects.count() + 1}"

        return Rabbit.objects.create(
            farm=self.farm,
            name=name,
            sex=sex,
            **kwargs,
        )

    def test_rabbits_with_same_mother_are_related(self):
        mother = self.create_rabbit("Mother", "F")
        female = self.create_rabbit("Female", "F", mother=mother)
        male = self.create_rabbit("Male", "M", mother=mother)

        self.assertEqual(
            check_pair_relatedness(female, male),
            "related",
        )

    def test_rabbits_with_same_father_are_related(self):
        father = self.create_rabbit("Father", "M")
        female = self.create_rabbit("Female", "F", father=father)
        male = self.create_rabbit("Male", "M", father=father)

        self.assertEqual(
            check_pair_relatedness(female, male),
            "related",
        )

    def test_incomplete_pedigree_returns_unknown(self):
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.assertEqual(
            check_pair_relatedness(female, male),
            "unknown",
        )

    def test_rabbits_with_common_grandparent_are_related(self):
        grandparent = self.create_rabbit("Grandparent", "F")

        female_parent = self.create_rabbit(
            "Female Parent", "F", mother=grandparent
        )
        male_parent = self.create_rabbit(
            "Male Parent", "M", mother=grandparent
        )

        female = self.create_rabbit(
            "Female", "F", mother=female_parent
        )
        male = self.create_rabbit(
            "Male", "M", mother=male_parent
        )

        self.assertEqual(
            check_pair_relatedness(female, male),
            "related",
        )

    def test_unknown_grandparents_do_not_prove_unrelatedness(self):
        female_mother = self.create_rabbit("Female Mother", "F")
        female_father = self.create_rabbit("Female Father", "M")
        male_mother = self.create_rabbit("Male Mother", "F")
        male_father = self.create_rabbit("Male Father", "M")

        female = self.create_rabbit(
            "Female", "F",
            mother=female_mother,
            father=female_father,
        )
        male = self.create_rabbit(
            "Male", "M",
            mother=male_mother,
            father=male_father,
        )

        self.assertEqual(
            check_pair_relatedness(female, male),
            "unknown",
        )

    def test_related_pair_is_not_recommended(self):
        female = self.create_rabbit(sex="F")
        male = self.create_rabbit(sex="M")

        common_mother = self.create_rabbit(sex="F")
        female.mother = common_mother
        female.save()

        male.mother = common_mother
        male.save()

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "related")

    def test_incomplete_pedigree_does_not_add_warning(self):
        female = self.create_rabbit(sex="F", breed="New Zealand White")
        male = self.create_rabbit(sex="M", breed="New Zealand White")

        result = evaluate_pairing(female, male)

        self.assertTrue(result["recommended"])
        self.assertEqual(result["relatedness"], "unknown")
        self.assertEqual(result["warnings"], [])

    def test_pair_without_known_common_ancestors_is_recommended(self):
        female = self.create_rabbit(sex="F")
        male = self.create_rabbit(sex="M")

        female_mother = self.create_rabbit(sex="F")
        female_father = self.create_rabbit(sex="M")
        male_mother = self.create_rabbit(sex="F")
        male_father = self.create_rabbit(sex="M")

        female.mother = female_mother
        female.father = female_father
        female.save()

        male.mother = male_mother
        male.father = male_father
        male.save()

        result = evaluate_pairing(female, male)

        self.assertTrue(result["recommended"])
        self.assertEqual(
            result["relatedness"],
            "unknown",
        )

    def test_same_rabbit_is_not_recommended(self):
        rabbit = self.create_rabbit("Rabbit", "F")

        result = evaluate_pairing(rabbit, rabbit)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "same_rabbit")

    def test_different_farms_are_not_recommended(self):
        other_farm = Farm.objects.create(
            name="Other Farm",
            owner=self.user,
        )
        female = self.create_rabbit("Female", "F")
        male = Rabbit.objects.create(
            farm=other_farm,
            name="Male",
            sex="M",
        )

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "different_farm")

    def test_inactive_rabbit_is_not_recommended(self):
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M", status="SOLD")

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "inactive")

    def test_pairing_candidates_include_all_active_rabbits(self):
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")
        self.create_rabbit("Sold Rabbit", "F", status="SOLD")

        # Активний кріль із попереднім паруванням теж має залишитися кандидатом.
        from events.models import Event

        Event.objects.create(
            rabbit=male,
            event_type="mating",
            date=date.today(),
        )

        females, males = get_pairing_candidates(self.farm)

        self.assertIn(female, females)
        self.assertIn(male, males)
        self.assertNotIn(
            Rabbit.objects.get(name="Sold Rabbit"),
            females,
        )

    def test_unknown_ancestors_beyond_three_generations(self):
        great_grandparent = self.create_rabbit("Great Grandparent", "F")

        female_grandparent = self.create_rabbit(
            "Female Grandparent", "F",
            mother=great_grandparent,
        )
        male_grandparent = self.create_rabbit(
            "Male Grandparent", "M",
            mother=great_grandparent,
        )

        female_parent = self.create_rabbit(
            "Female Parent", "F",
            mother=female_grandparent,
            father=self.create_rabbit("Female Grandfather", "M"),
        )
        male_parent = self.create_rabbit(
            "Male Parent", "M",
            mother=male_grandparent,
            father=self.create_rabbit("Male Grandfather", "M"),
        )

        female = self.create_rabbit(
            "Female", "F",
            mother=female_parent,
            father=self.create_rabbit("Female Father", "M"),
        )
        male = self.create_rabbit(
            "Male", "M",
            mother=male_parent,
            father=self.create_rabbit("Male Father", "M"),
        )

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "related")

    def test_recommended_pairs_exclude_related_rabbits(self):
        common_mother = self.create_rabbit("Common Mother", "F")
        female = self.create_rabbit(
            "Female", "F", mother=common_mother
        )
        male = self.create_rabbit(
            "Male", "M", mother=common_mother
        )

        pairs = get_recommended_pairs(self.farm)

        self.assertFalse(
            any(
                pair["female"] == female and pair["male"] == male
                for pair in pairs
            )
        )

    def test_recommended_pairs_include_warning_for_incomplete_pedigree(self):
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        pairs = get_recommended_pairs(self.farm)

        pair = next(
            (
                item for item in pairs
                if item["female"] == female and item["male"] == male
            ),
            None,
        )

        self.assertIsNotNone(pair)
        self.assertEqual(pair["relatedness"], "unknown")
        self.assertFalse(
            any("родовід" in warning.lower() for warning in pair["warnings"])
        )

    def test_recommended_pairs_include_unrelated_rabbits(self):
        female_mother = self.create_rabbit("Female Mother", "F")
        female_father = self.create_rabbit("Female Father", "M")
        male_mother = self.create_rabbit("Male Mother", "F")
        male_father = self.create_rabbit("Male Father", "M")

        female = self.create_rabbit(
            "Female", "F",
            mother=female_mother,
            father=female_father,
        )
        male = self.create_rabbit(
            "Male", "M",
            mother=male_mother,
            father=male_father,
        )

        pairs = get_recommended_pairs(self.farm)

        pair = next(
            (
                item for item in pairs
                if item["female"] == female and item["male"] == male
            ),
            None,
        )

        self.assertIsNotNone(pair)
        self.assertEqual(pair["relatedness"], "unknown")

    def test_same_known_breed_is_recommended_without_cross_warning(self):
        female = self.create_rabbit(
            sex="F",
            breed="New Zealand White",
        )
        male = self.create_rabbit(
            sex="M",
            breed="New Zealand White",
        )

        result = evaluate_pairing(female, male)

        self.assertTrue(result["recommended"])
        self.assertFalse(
            any("кросовим" in warning for warning in result["warnings"])
        )

    def test_different_known_breeds_are_not_recommended(self):
        female = self.create_rabbit(
            sex="F",
            breed="New Zealand White",
        )
        male = self.create_rabbit(
            sex="M",
            breed="New Zealand Blue",
        )

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertTrue(
            any("кросовим" in warning for warning in result["warnings"])
        )

    def test_missing_breed_allows_pair_with_cross_warning(self):
        female = self.create_rabbit(
            sex="F",
            breed="New Zealand White",
        )
        male = self.create_rabbit(sex="M")

        result = evaluate_pairing(female, male)

        self.assertTrue(result["recommended"])
        self.assertTrue(
            any("кросовим" in warning for warning in result["warnings"])
        )

    def test_unknown_breed_allows_pair_with_cross_warning(self):
        for unknown_breed in ("unknown", "невідома"):
            with self.subTest(breed=unknown_breed):
                female = self.create_rabbit(
                    sex="F",
                    breed=unknown_breed,
                )
                male = self.create_rabbit(
                    sex="M",
                    breed="New Zealand White",
                )

                result = evaluate_pairing(female, male)

                self.assertTrue(result["recommended"])
                self.assertTrue(
                    any(
                        "кросовим" in warning
                        for warning in result["warnings"]
                    )
                )

class MatingReadinessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="readiness_test",
            password="test-password",
        )
        self.farm = Farm.objects.create(
            name="Readiness Farm",
            owner=self.user,
        )

    def test_missing_birth_date_returns_insufficient_data(self):
        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Rabbit Without Birth Date",
            sex="F",
            birth_date=None,
        )

        self.assertEqual(
            get_mating_readiness(rabbit, today=date(2026, 10, 19)),
            INSUFFICIENT_DATA,
        )

    def test_rabbit_ready_when_age_and_weight_thresholds_met(self):
        RabbitBreed.objects.create(
            name="Test Medium Breed",
            conditional_class="medium",
            first_mating_age_months=4.5,
            first_mating_weight_kg=3.40,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Ready Rabbit",
            sex="F",
            breed="Test Medium Breed",
            birth_date=date(2026, 1, 1),
            weight=3.50,
        )

        self.assertEqual(
            get_mating_readiness(rabbit, today=date(2026, 10, 19)),
            READY,
        )

    def test_rabbit_not_ready_when_weight_is_below_threshold(self):
        RabbitBreed.objects.create(
            name="Test Medium Breed",
            conditional_class="medium",
            first_mating_age_months=4.5,
            first_mating_weight_kg=3.40,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Underweight Rabbit",
            sex="F",
            breed="Test Medium Breed",
            birth_date=date(2026, 1, 1),
            weight=3.00,
        )

        self.assertEqual(
            get_mating_readiness(rabbit, today=date(2026, 10, 19)),
            NOT_READY,
        )

    def test_missing_weight_returns_insufficient_data(self):
        RabbitBreed.objects.create(
            name="Test Medium Breed",
            conditional_class="medium",
            first_mating_age_months=4.5,
            first_mating_weight_kg=3.40,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Rabbit Without Weight",
            sex="F",
            breed="Test Medium Breed",
            birth_date=date(2026, 1, 1),
            weight=None,
        )

        self.assertEqual(
            get_mating_readiness(rabbit, today=date(2026, 10, 19)),
            INSUFFICIENT_DATA,
        )

    def test_existing_mating_event_skips_first_mating_readiness(self):
        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Rabbit Already Mated",
            sex="F",
            birth_date=date(2026, 1, 1),
            breed="Unknown Breed",
            weight=None,
        )

        Event.objects.create(
            rabbit=rabbit,
            event_type="mating",
            date=date(2026, 10, 19),
        )

        self.assertIsNone(
            get_mating_readiness(rabbit, today=date(2026, 10, 19))
        )

class RecommendedPairReadinessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pair_readiness_test",
            password="test-password",
        )
        self.farm = Farm.objects.create(
            name="Pair Readiness Farm",
            owner=self.user,
        )

    def test_pair_with_insufficient_readiness_data_has_warning(self):
        female = Rabbit.objects.create(
            farm=self.farm,
            name="Female Without Birth Date",
            sex="F",
            status="ACTIVE",
            birth_date=None,
        )
        male = Rabbit.objects.create(
            farm=self.farm,
            name="Male Without Birth Date",
            sex="M",
            status="ACTIVE",
            birth_date=None,
        )

        pairs = get_recommended_pairs(self.farm)

        pair = next(
            (
                item for item in pairs
                if item["female"] == female and item["male"] == male
            ),
            None,
        )

        self.assertIsNotNone(pair)
        self.assertTrue(pair["warnings"])
        self.assertTrue(
            any("даних" in warning.lower() for warning in pair["warnings"])
        )

    def test_pair_with_rabbit_too_young_is_not_recommended(self):
        RabbitBreed.objects.create(
            name="Test Medium Breed",
            conditional_class="medium",
            first_mating_age_months=4.5,
            first_mating_weight_kg=3.40,
        )

        female = Rabbit.objects.create(
            farm=self.farm,
            name="Too Young Female",
            sex="F",
            status="ACTIVE",
            breed="Test Medium Breed",
            birth_date=date(2026, 10, 1),
            weight=3.50,
        )

        male = Rabbit.objects.create(
            farm=self.farm,
            name="Male Without Birth Date",
            sex="M",
            status="ACTIVE",
            birth_date=None,
        )

        pairs = get_recommended_pairs(self.farm)

        self.assertFalse(
            any(
                pair["female"] == female and pair["male"] == male
                for pair in pairs
            )
        )

    def test_previous_mating_does_not_block_pair_recommendation(self):
        female = Rabbit.objects.create(
            farm=self.farm,
            name="Previously Mated Female",
            sex="F",
            status="ACTIVE",
            birth_date=None,
        )

        male = Rabbit.objects.create(
            farm=self.farm,
            name="New Male",
            sex="M",
            status="ACTIVE",
            birth_date=None,
        )

        Event.objects.create(
            rabbit=female,
            event_type="mating",
            date=date.today(),
        )

        pairs = get_recommended_pairs(self.farm)

        self.assertTrue(
            any(
                pair["female"] == female and pair["male"] == male
                for pair in pairs
            )
        )