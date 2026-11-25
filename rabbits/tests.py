from django.test import TestCase
from django.utils.translation import override
from django.contrib.auth.models import User
from farms.models import Farm
from events.models import Event
from rabbits.models import Rabbit, RabbitBreed, PedigreeNode
from rabbits.forms import RabbitForm
from rabbits.services import (
    check_pair_relatedness,
    evaluate_pairing,
    find_duplicate_parents,
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
    def set_parents(self, rabbit, mother=None, father=None):
        node = rabbit.pedigree_node
        node.mother = mother.pedigree_node if mother else None
        node.father = father.pedigree_node if father else None
        node.save()

    def test_rabbits_with_same_mother_are_related(self):
        mother = self.create_rabbit("Mother", "F")
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(female, mother=mother)
        self.set_parents(male, mother=mother)

        self.assertEqual(
            check_pair_relatedness(female, male),
            "related",
        )

    def test_rabbits_with_same_father_are_related(self):
        father = self.create_rabbit("Father", "M")
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(female, father=father)
        self.set_parents(male, father=father)

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

        female_parent = self.create_rabbit("Female Parent", "F")
        male_parent = self.create_rabbit("Male Parent", "M")

        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(female_parent, mother=grandparent)
        self.set_parents(male_parent, mother=grandparent)

        self.set_parents(female, mother=female_parent)
        self.set_parents(male, mother=male_parent)

        self.assertEqual(
            check_pair_relatedness(female, male),
            "related",
        )

    def test_unknown_grandparents_do_not_prove_unrelatedness(self):
        female_mother = self.create_rabbit("Female Mother", "F")
        female_father = self.create_rabbit("Female Father", "M")
        male_mother = self.create_rabbit("Male Mother", "F")
        male_father = self.create_rabbit("Male Father", "M")

        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(
            female,
            mother=female_mother,
            father=female_father,
        )
        self.set_parents(
            male,
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

        self.set_parents(female, mother=common_mother)
        self.set_parents(male, mother=common_mother)

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

        female_grandparent = self.create_rabbit("Female Grandparent", "F")
        male_grandparent = self.create_rabbit("Male Grandparent", "M")

        female_grandfather = self.create_rabbit("Female Grandfather", "M")
        male_grandfather = self.create_rabbit("Male Grandfather", "M")

        female_parent = self.create_rabbit("Female Parent", "F")
        male_parent = self.create_rabbit("Male Parent", "M")

        female_father = self.create_rabbit("Female Father", "M")
        male_father = self.create_rabbit("Male Father", "M")

        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(female_grandparent, mother=great_grandparent)
        self.set_parents(male_grandparent, mother=great_grandparent)

        self.set_parents(
            female_parent,
            mother=female_grandparent,
            father=female_grandfather,
        )
        self.set_parents(
            male_parent,
            mother=male_grandparent,
            father=male_grandfather,
        )

        self.set_parents(
            female,
            mother=female_parent,
            father=female_father,
        )
        self.set_parents(
            male,
            mother=male_parent,
            father=male_father,
        )

        result = evaluate_pairing(female, male)

        self.assertFalse(result["recommended"])
        self.assertEqual(result["relatedness"], "related")

    def test_recommended_pairs_exclude_related_rabbits(self):
        common_mother = self.create_rabbit("Common Mother", "F")
        female = self.create_rabbit("Female", "F")
        male = self.create_rabbit("Male", "M")

        self.set_parents(female, mother=common_mother)
        self.set_parents(male, mother=common_mother)

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
            any("Possible crossbreeding" in warning for warning in result["warnings"])
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
            any("Possible crossbreeding" in warning for warning in result["warnings"])
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
            any("Possible crossbreeding" in warning for warning in result["warnings"])
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
                        "Possible crossbreeding" in warning
                        for warning in result["warnings"]
                    )
                )
    def test_rabbit_creation_creates_pedigree_node(self):
        rabbit = self.create_rabbit("Signal Test", "F")

        self.assertTrue(
            PedigreeNode.objects.filter(
                rabbit=rabbit,
                farm=self.farm,
            ).exists()
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

class FarmInventoryNumberTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="inventory_test",
            password="test-password",
        )
        self.farm1 = Farm.objects.create(
            name="Farm One",
            owner=self.user,
        )
        self.farm2 = Farm.objects.create(
            name="Farm Two",
            owner=self.user,
        )

    def test_inventory_numbers_are_independent_per_farm(self):
        rabbit1 = Rabbit.objects.create(
            farm=self.farm1,
            name="Rabbit One",
            sex="F",
        )
        rabbit2 = Rabbit.objects.create(
            farm=self.farm2,
            name="Rabbit Two",
            sex="F",
        )

        self.assertEqual(rabbit1.inventory_number, "0001")
        self.assertEqual(rabbit2.inventory_number, "0001")

        rabbit3 = Rabbit.objects.create(
            farm=self.farm1,
            name="Rabbit Three",
            sex="F",
)

        self.assertEqual(rabbit3.inventory_number, "0002")

class RabbitFormParentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="parent_test",
            password="test-password",
        )
        self.farm = Farm.objects.create(
            name="Parent Test Farm",
            owner=self.user,
        )
    
    def test_finds_matching_registered_rabbit_by_origin_source(self):
        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Registered Mother",
            sex="F",
            breed="Vienna Blue",
            origin_source="External Farm",
        )

        matches = find_duplicate_parents(
            self.farm,
            "Registered Mother",
            "F",
            "Vienna Blue",
            "External Farm",
        )

        self.assertEqual(
            list(matches),
            [rabbit.pedigree_node],
        )

    def test_finds_matching_manual_parent(self):
        parent = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="External Farm",
            is_manual=True,
        )

        matches = find_duplicate_parents(
            self.farm,
            "External Mother",
            "F",
            "Vienna Blue",
            "External Farm",
        )

        self.assertEqual(list(matches), [parent])

    def test_different_origin_is_not_a_duplicate(self):
        PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="Farm One",
            is_manual=True,
        )

        matches = find_duplicate_parents(
            self.farm,
            "External Mother",
            "F",
            "Vienna Blue",
            "Farm Two",
        )

        self.assertFalse(matches.exists())
    def test_unknown_breed_matches_empty_breed(self):
        PedigreeNode.objects.create(
            farm=self.farm,
            is_manual=True,
            manual_name="Unknown Breed Mother",
            manual_sex="F",
            manual_breed="",
            origin_farm="Farm One",
        )

        matches = find_duplicate_parents(
            self.farm,
            "Unknown Breed Mother",
            "F",
            "Невідома",
            "Farm One",
        )

        self.assertTrue(matches.exists())

    def test_parent_from_another_farm_is_not_a_duplicate(self):
        other_farm = Farm.objects.create(
            name="Other Farm",
            owner=self.user,
        )

        PedigreeNode.objects.create(
            farm=other_farm,
            is_manual=True,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="Farm One",
        )

        matches = find_duplicate_parents(
            self.farm,
            "External Mother",
            "F",
            "Vienna Blue",
            "Farm One",
        )

        self.assertFalse(matches.exists())

    def test_parent_with_different_sex_is_not_a_duplicate(self):
        PedigreeNode.objects.create(
            farm=self.farm,
            is_manual=True,
            manual_name="Test Parent",
            manual_sex="M",
            manual_breed="Vienna Blue",
            origin_farm="Farm One",
        )

        matches = find_duplicate_parents(
            self.farm,
            "Test Parent",
            "F",
            "Vienna Blue",
            "Farm One",
        )

        self.assertFalse(matches.exists())

    def test_duplicate_manual_parent_requires_explicit_selection(self):
        PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="External Farm",
            is_manual=True,
        )

        form = RabbitForm(
            data={
                "name": "Test Offspring",
                "sex": "F",
                "status": "ACTIVE",
                "breed": "Vienna Blue",
                "origin_source": "External Farm",
                "mother_manual": "External Mother",
                },
            farm=self.farm,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("mother_node", form.errors)

    def test_registered_parents_are_saved_to_both_models(self):
        mother = Rabbit.objects.create(
            farm=self.farm,
            name="Mother",
            sex="F",
        )
        father = Rabbit.objects.create(
            farm=self.farm,
            name="Father",
            sex="M",
        )
        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring",
            sex="F",
        )

        form = RabbitForm(
           data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "mother_node": mother.pedigree_node.pk,
                "father_node": father.pedigree_node.pk,
                "status": rabbit.status,
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        node = saved_rabbit.pedigree_node

        self.assertEqual(saved_rabbit.mother, mother)
        self.assertEqual(saved_rabbit.father, father)
        self.assertEqual(node.mother, mother.pedigree_node)
        self.assertEqual(node.father, father.pedigree_node)

    def test_pedigree_only_parents_are_saved_without_rabbit_links(self):
        mother_node = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            is_manual=True,
        )
        father_node = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Father",
            manual_sex="M",
            is_manual=True,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring External",
            sex="F",
        )

        form = RabbitForm(
            data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "status": rabbit.status,
                "mother_node": mother_node.pk,
                "father_node": father_node.pk,
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        node = saved_rabbit.pedigree_node

        self.assertIsNone(saved_rabbit.mother)
        self.assertIsNone(saved_rabbit.father)
        self.assertEqual(node.mother, mother_node)
        self.assertEqual(node.father, father_node)

    def test_manual_parent_names_create_pedigree_nodes(self):
        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring Manual",
            sex="F",
        )

        form = RabbitForm(
            data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "status": rabbit.status,
                "breed": "Vienna Blue",
                "origin_source": "External Farm",
                "mother_manual": "External Mother",
                "father_manual": "External Father",
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        node = saved_rabbit.pedigree_node

        self.assertIsNone(saved_rabbit.mother)
        self.assertIsNone(saved_rabbit.father)

        self.assertEqual(node.mother.manual_name, "External Mother")
        self.assertEqual(node.mother.manual_sex, "F")
        self.assertEqual(node.father.manual_name, "External Father")
        self.assertEqual(node.father.manual_sex, "M")

        self.assertEqual(node.mother.manual_breed, "Vienna Blue")
        self.assertEqual(node.mother.origin_farm, "External Farm")
        self.assertEqual(node.father.manual_breed, "Vienna Blue")
        self.assertEqual(node.father.origin_farm, "External Farm")

    
    def test_existing_manual_parent_is_reused_without_losing_pedigree_links(self):
        grandmother = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="Grandmother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="External Farm",
            is_manual=True,
        )

        existing_mother = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="External Farm",
            is_manual=True,
            mother=grandmother,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring Reuse",
            sex="F",
        )

        form = RabbitForm(
            data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "status": rabbit.status,
                "breed": "Vienna Blue",
                "origin_source": "External Farm",
                "mother_manual": "External Mother",
                "mother_node": existing_mother.pk,
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        offspring_node = saved_rabbit.pedigree_node
        existing_mother.refresh_from_db()

        self.assertEqual(offspring_node.mother_id, existing_mother.pk)
        self.assertEqual(existing_mother.mother_id, grandmother.pk)

        self.assertEqual(
            PedigreeNode.objects.filter(
                farm=self.farm,
                manual_name="External Mother",
                manual_sex="F",
                manual_breed="Vienna Blue",
                origin_farm="External Farm",
                is_manual=True,
            ).count(),
            1,
        )

    
    def test_same_parent_name_with_different_breed_creates_separate_node(self):
        existing_mother = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="External Farm",
            is_manual=True,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring Different Breed",
            sex="F",
        )

        form = RabbitForm(
            data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "status": rabbit.status,
                "breed": "Pannon White",
                "origin_source": "External Farm",
                "mother_manual": "External Mother",
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        offspring_node = saved_rabbit.pedigree_node

        self.assertNotEqual(offspring_node.mother_id, existing_mother.pk)
        self.assertEqual(offspring_node.mother.manual_name, "External Mother")
        self.assertEqual(offspring_node.mother.manual_breed, "Pannon White")
        self.assertEqual(offspring_node.mother.origin_farm, "External Farm")

        self.assertEqual(
            PedigreeNode.objects.filter(
                farm=self.farm,
                manual_name="External Mother",
                manual_sex="F",
                is_manual=True,
            ).count(),
            2,
        )


    def test_same_parent_name_and_breed_with_different_origin_creates_separate_node(self):
        existing_mother = PedigreeNode.objects.create(
            farm=self.farm,
            manual_name="External Mother",
            manual_sex="F",
            manual_breed="Vienna Blue",
            origin_farm="Farm One",
            is_manual=True,
        )

        rabbit = Rabbit.objects.create(
            farm=self.farm,
            name="Offspring Different Origin",
            sex="F",
        )

        form = RabbitForm(
            data={
                "name": rabbit.name,
                "sex": rabbit.sex,
                "status": rabbit.status,
                "breed": "Vienna Blue",
                "origin_source": "Farm Two",
                "mother_manual": "External Mother",
            },
            instance=rabbit,
            farm=self.farm,
        )

        self.assertTrue(form.is_valid(), form.errors)

        saved_rabbit = form.save()
        form.save_pedigree()

        saved_rabbit.refresh_from_db()
        offspring_node = saved_rabbit.pedigree_node

        self.assertNotEqual(offspring_node.mother_id, existing_mother.pk)
        self.assertEqual(offspring_node.mother.manual_name, "External Mother")
        self.assertEqual(offspring_node.mother.manual_breed, "Vienna Blue")
        self.assertEqual(offspring_node.mother.origin_farm, "Farm Two")

        self.assertEqual(
            PedigreeNode.objects.filter(
                farm=self.farm,
                manual_name="External Mother",
                manual_sex="F",
                is_manual=True,
            ).count(),
            2,
        )  
