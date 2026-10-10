"""Known small cases test interpretation, exclusions and type boundaries."""

import json
import unittest
from fractions import Fraction

import numpy as np
import pandas as pd

from statistical_exploration_lab.distributions import categorical_summary, numeric_summary
from statistical_exploration_lab.relationships import categorical_relationship, group_summary, numeric_relationship


class DistributionTests(unittest.TestCase):
    def test_numeric_statistics_and_exclusions(self):
        result = numeric_summary(pd.Series([1, 2, 3, 4, None, np.inf, -np.inf]))
        self.assertEqual(result["total_count"], 7)
        self.assertEqual(result["usable_count"], 4)
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual(result["nonfinite_count"], 2)
        self.assertEqual(result["invalid_count"], 0)
        self.assertEqual((result["min"], result["q25"], result["median"], result["q75"], result["max"]), (1, 1.75, 2.5, 3.25, 4))
        self.assertEqual(result["mean"], 2.5)
        self.assertAlmostEqual(result["std"], np.sqrt(5 / 3))

    def test_empty_and_single_numeric(self):
        empty = numeric_summary(pd.Series([], dtype=float))
        self.assertEqual(empty["status"], "skipped")
        self.assertEqual(empty["reason"], "no_usable_values")
        self.assertIsNone(empty["mean"])
        single = numeric_summary(pd.Series([8]))
        self.assertEqual(single["mean"], 8)
        self.assertIsNone(single["std"])

    def test_numeric_types_are_declared_not_coerced(self):
        for value in ("1", "invalid", True, np.bool_(False), [1], complex(1, 2)):
            with self.subTest(value=value), self.assertRaises(TypeError):
                numeric_summary(pd.Series([1, value], dtype=object))

    def test_integer_precision_loss_is_rejected(self):
        for value in (2 ** 60 + 1, np.int64(2 ** 60 + 1)):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'floating-point precision'):
                numeric_summary(pd.Series([value], dtype=object))
        representable = numeric_summary(pd.Series([2 ** 60], dtype='int64'))
        self.assertEqual(representable['mean'], float(2 ** 60))
        self.assertEqual(representable['status'], 'ok')

    def test_extreme_numeric_values_are_json_safe(self):
        result = numeric_summary(pd.Series([-1.7e308, 1.7e308]))
        self.assertEqual(result["mean"], 0)
        self.assertEqual(result["median"], 0)
        self.assertEqual(result["reason"], "statistics_overflow")
        self.assertIsNone(result["std"])
        json.dumps(result, allow_nan=False)
        constant = numeric_summary(pd.Series([1.7e308, 1.7e308, 1.7e308]))
        self.assertEqual(constant["status"], "ok")
        self.assertAlmostEqual(constant["mean"] / 1.7e308, 1)
        self.assertEqual(constant["std"], 0)
        json.dumps(constant, allow_nan=False)
        largest = np.finfo(float).max
        for values in ([largest] * 3, [-largest, largest], [-largest, -largest, largest]):
            json.dumps(numeric_summary(pd.Series(values)), allow_nan=False)

    def test_category_denominator_and_type_collisions(self):
        result = categorical_summary(pd.Series([True, 1, "1", 1.0, None, "1"], dtype=object))
        counts = {item["value"]: item["count"] for item in result["categories"]}
        self.assertEqual(counts, {"boolean:true": 1, "integer:1": 1, "string:1": 2, "float:1.0": 1})
        self.assertEqual(result["usable_count"], 5)
        self.assertEqual(result["missing_count"], 1)
        proportion = next(item["proportion"] for item in result["categories"] if item["value"] == "string:1")
        self.assertEqual(proportion, 2 / 5)
        self.assertAlmostEqual(sum(item["proportion"] for item in result["categories"]), 1)

    def test_empty_and_invalid_categories(self):
        result = categorical_summary(pd.Series([None, pd.NA, np.nan], dtype=object))
        self.assertEqual(result["categories"], [])
        self.assertEqual(result["status"], "skipped")
        with self.assertRaises(TypeError):
            categorical_summary(pd.Series([np.inf]))
        with self.assertRaises(TypeError):
            categorical_summary(pd.Series([{"a": 1}]))
        with self.assertRaises(TypeError):
            categorical_summary(pd.Series([Fraction(1, 3)], dtype=object))


class RelationshipTests(unittest.TestCase):
    def test_known_pearson_directions(self):
        data = pd.DataFrame({"x": [1, 2, 3, 4], "up": [3, 5, 7, 9], "down": [9, 7, 5, 3]})
        self.assertAlmostEqual(numeric_relationship(data, "x", "up")["coefficients"]["pearson"], 1)
        self.assertAlmostEqual(numeric_relationship(data, "x", "down")["coefficients"]["pearson"], -1)

    def test_integer_relationship_precision_loss_is_not_a_false_constant(self):
        data = pd.DataFrame({'x': [2 ** 60, 2 ** 60 + 1, 2 ** 60 + 2], 'y': [1, 2, 3]})
        with self.assertRaisesRegex(ValueError, 'floating-point precision'):
            numeric_relationship(data, 'x', 'y')

    def test_curved_monotonic_spearman_and_ties(self):
        curved = pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 4, 9, 16]})
        result = numeric_relationship(curved, "x", "y")
        self.assertAlmostEqual(result["coefficients"]["spearman"], 1)
        self.assertLess(result["coefficients"]["pearson"], 1)
        tied = pd.DataFrame({"x": [1, 1, 2, 3], "y": [1, 2, 2, 3]})
        result = numeric_relationship(tied, "x", "y", methods=["spearman"])
        self.assertAlmostEqual(result["coefficients"]["spearman"], 5 / 6)

    def test_pairwise_exclusions_are_not_double_counted(self):
        data = pd.DataFrame({"x": [1, 2, 3, None, np.inf, None], "y": [2, 4, 6, 8, None, np.inf]})
        result = numeric_relationship(data, "x", "y")
        self.assertEqual(result["usable_count"], 3)
        self.assertEqual(result["excluded_count"], 3)
        self.assertEqual(result["exclusions"]["left"]["missing_count"], 2)
        self.assertEqual(result["exclusions"]["left"]["nonfinite_count"], 1)
        self.assertEqual(result["exclusions"]["right"]["missing_count"], 1)
        self.assertEqual(result["exclusions"]["right"]["nonfinite_count"], 1)
        self.assertAlmostEqual(result["coefficients"]["pearson"], 1)

    def test_constant_empty_and_small_pairs(self):
        for data, reason in (
            (pd.DataFrame({"x": [1, 1, 1], "y": [2, 3, 4]}), "constant_field"),
            (pd.DataFrame({"x": [], "y": []}), "insufficient_usable_pairs"),
            (pd.DataFrame({"x": [1, 2], "y": [3, 4]}), "insufficient_usable_pairs"),
        ):
            result = numeric_relationship(data, "x", "y")
            self.assertEqual(result["reason"], reason)
            self.assertTrue(all(value is None for value in result["coefficients"].values()))

    def test_contingency_counts_and_row_percentages(self):
        data = pd.DataFrame({"x": ["a", "a", "a", "b", None, "a"], "y": ["u", "u", "v", "v", "u", None]})
        result = categorical_relationship(data, "x", "y")
        self.assertEqual(result["row_categories"], ["string:a", "string:b"])
        self.assertEqual(result["column_categories"], ["string:u", "string:v"])
        self.assertEqual(result["counts"], [[2, 1], [0, 1]])
        self.assertEqual(result["usable_count"], 4)
        self.assertEqual(result["excluded_count"], 2)
        self.assertAlmostEqual(result["row_percentages"][0][0], 200 / 3)
        self.assertEqual(result["row_percentages"][1], [0, 100])
        self.assertEqual(result["percentage_denominator"], "complete pairs in each row category")

    def test_contingency_type_collisions_and_empty(self):
        data = pd.DataFrame({"x": pd.Series([True, 1, "1"], dtype=object), "y": ["a", "a", "a"]})
        result = categorical_relationship(data, "x", "y")
        self.assertEqual(result["row_categories"], ["boolean:true", "integer:1", "string:1"])
        self.assertEqual(result["counts"], [[1], [1], [1]])
        empty = categorical_relationship(pd.DataFrame({"x": [None], "y": [None]}), "x", "y")
        self.assertEqual(empty["counts"], [])
        self.assertEqual(empty["row_percentages"], [])
        self.assertEqual(empty["reason"], "insufficient_usable_pairs")

    def test_group_counts_include_small_and_excluded_groups(self):
        data = pd.DataFrame({"group": ["a", "a", "a", "b", "c", "c", None], "value": [1, 3, None, 5, None, np.inf, 20]})
        result = group_summary(data, "group", "value")
        groups = {item["value"]: item for item in result["groups"]}
        self.assertEqual(result["missing_group_count"], 1)
        self.assertEqual(sum(item["total_count"] for item in groups.values()) + result["missing_group_count"], result["total_count"])
        self.assertEqual(groups["string:a"]["total_count"], 3)
        self.assertEqual(groups["string:a"]["missing_count"], 1)
        self.assertEqual(groups["string:a"]["statistics"]["mean"], 2)
        self.assertAlmostEqual(groups["string:a"]["statistics"]["std"], np.sqrt(2))
        self.assertEqual(groups["string:b"]["usable_count"], 1)
        self.assertEqual(groups["string:b"]["reason"], "insufficient_usable_values")
        self.assertIsNone(groups["string:b"]["statistics"]["mean"])
        self.assertEqual(groups["string:c"]["missing_count"], 1)
        self.assertEqual(groups["string:c"]["nonfinite_count"], 1)
        self.assertEqual(groups["string:c"]["usable_count"], 0)

    def test_empty_groups_and_all_missing_group_keys(self):
        for data in (
            pd.DataFrame({"group": [], "value": []}),
            pd.DataFrame({"group": [None, None], "value": [1, np.inf]}),
        ):
            result = group_summary(data, "group", "value")
            self.assertEqual(result["groups"], [])
            self.assertEqual(result["missing_group_count"], len(data))
            self.assertEqual(result["status"], "skipped")
            json.dumps(result, allow_nan=False)

    def test_input_unchanged_and_extreme_correlation(self):
        data = pd.DataFrame({"x": [-1e308, 0, 1e308], "y": [1e308, 0, -1e308], "group": ["a", "a", "b"]})
        before = data.copy(deep=True)
        result = numeric_relationship(data, "x", "y")
        self.assertAlmostEqual(result["coefficients"]["pearson"], -1)
        json.dumps(result, allow_nan=False)
        numeric_summary(data["x"])
        categorical_summary(data["group"])
        categorical_relationship(data, "group", "group")
        group_summary(data, "group", "x")
        pd.testing.assert_frame_equal(data, before)

    def test_invalid_fields_settings_and_numeric_types(self):
        data = pd.DataFrame({"x": [1, 2, 3], "y": [2, 3, 4]})
        with self.assertRaises(ValueError):
            numeric_relationship(data, "x", "absent")
        for methods in ([], ["kendall"], ["pearson", "pearson"], "pearson"):
            with self.subTest(methods=methods), self.assertRaises(ValueError):
                numeric_relationship(data, "x", "y", methods=methods)
        for minimum in (0, -1, 1.5, True):
            with self.subTest(minimum=minimum), self.assertRaises(ValueError):
                numeric_relationship(data, "x", "y", minimum=minimum)
        with self.assertRaises(TypeError):
            numeric_relationship(pd.DataFrame({"x": [1, "2", 3], "y": [2, 3, 4]}), "x", "y")
        with self.assertRaises(ValueError):
            numeric_relationship(pd.DataFrame([[1, 2]], columns=["x", "x"]), "x", "x")


if __name__ == "__main__":
    unittest.main()
