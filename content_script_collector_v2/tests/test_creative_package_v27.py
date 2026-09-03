import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
import creative_package_v27 as cp27

class CreativePackageV27Tests(unittest.TestCase):
    def test_augment_v27_writes_registry_and_assets(self):
        generated={"version":"2.7","creative_registry":{"registered_candidates":3,"database":"x.sqlite"},"input_assets":{"product_image":"input_images/a.png","product_url":"https://example.com/product"}}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/"project.json").write_text(json.dumps({"project_id":"x"}),encoding="utf-8");(p/"manifest.json").write_text(json.dumps({"generated_files":[]}),encoding="utf-8")
            cp27.augment_v27(p,generated)
            self.assertTrue((p/"creative_registry.json").exists())
            self.assertTrue((p/"input_assets.json").exists())
            project=json.loads((p/"project.json").read_text(encoding="utf-8"));self.assertEqual(project["script_generator_version"],"2.7");self.assertEqual(project["input_assets"]["product_url"],"https://example.com/product")
            manifest=json.loads((p/"manifest.json").read_text(encoding="utf-8"));self.assertEqual(manifest["milestone"],"CREATIVE_PACKAGE_V27_PLATFORM_READY");self.assertIn("creative_registry.json",manifest["generated_files"])

if __name__=="__main__":unittest.main()
