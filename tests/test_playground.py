"""Integration checks for the editable table-inspection example."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import tempfile
import unittest

import pandas as pd


class PlaygroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        example = Path(__file__).resolve().parents[1] / "examples" / "inspect_table.py"
        with redirect_stdout(StringIO()):
            cls.cells = runpy.run_path(str(example), run_name="__main__")

    def test_file_runs_and_keeps_decisions_visible(self):
        self.assertEqual(self.cells["profile"].observation_key, ("record_id",))
        by_name = self.cells["typed"].by_name()
        self.assertEqual(by_name["amount"].sentinels, ())
        self.assertIn("UNK", by_name["note"].sentinel_candidates)
        self.assertEqual(by_name["note"].sentinels, ())
        self.assertEqual(self.cells["data"].loc[2, "amount"], -1.0)

    def test_csv_choice_preserves_identifier_and_category_text(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "observations.csv"
            source.write_text("record_id,label,amount\n001,NA,10\n002,UNK,20\n", encoding="utf-8")
            table = self.cells["load_table"](source)
            self.assertEqual(table["record_id"].tolist(), ["001", "002"])
            self.assertEqual(table["label"].tolist(), ["NA", "UNK"])
            self.assertEqual(table["amount"].tolist(), ["10", "20"])

    def test_selected_recipe_preserves_input_and_confirmed_roles(self):
        table = pd.DataFrame({"id": ["a", "b", "c"], "measure": [-1.0, 2.0, 2.0]})
        before = table.copy(deep=True)
        structure, typed = self.cells["inspect_selected_table"](
            table, observation_key="id", roles={"measure": "continuous"},
            missing_values={"measure": []},
        )
        self.assertNotEqual(structure.gate.status, "stop")
        self.assertEqual(typed.by_name()["measure"].semantic_type, "continuous")
        pd.testing.assert_frame_equal(table, before)

    def test_selected_recipe_retains_stop_without_typing(self):
        table = pd.DataFrame({"id": ["a", "a"], "measure": [1.0, 2.0]})
        structure, typed = self.cells["inspect_selected_table"](table, observation_key="id")
        self.assertEqual(structure.gate.status, "stop")
        self.assertIsNone(typed)


if __name__ == "__main__":
    unittest.main()
