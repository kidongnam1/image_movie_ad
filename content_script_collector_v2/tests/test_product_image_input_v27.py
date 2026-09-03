import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
import product_image_input_v27 as img

class ProductImageInputV27Tests(unittest.TestCase):
    def test_local_file_copy_and_rights_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); src=td/"sample.png"; src.write_bytes(b"fake-png-data")
            old=img.IMAGE_DIR
            try:
                img.IMAGE_DIR=td/"input_images"
                dst=img.import_image_file(src,"테스트 상품","상업 이용 라이선스 보유")
                self.assertTrue(dst.exists())
                meta=json.loads(img.provenance_path(dst).read_text(encoding="utf-8"))
                self.assertTrue(meta["approved_for_ad_use"])
                self.assertEqual(meta["rights_basis"],"상업 이용 라이선스 보유")
                self.assertEqual(len(meta["sha256"]),64)
                img.update_rights_metadata(dst,"판매자/권리자 사용허락")
                meta=json.loads(img.provenance_path(dst).read_text(encoding="utf-8"))
                self.assertEqual(meta["rights_basis"],"판매자/권리자 사용허락")
            finally:
                img.IMAGE_DIR=old
    def test_private_and_invalid_urls_are_blocked(self):
        with self.assertRaises(ValueError):img._validate_remote_url("file:///tmp/a.png")
        with self.assertRaises(ValueError):img._validate_remote_url("http://127.0.0.1/a.png")
        with self.assertRaises(ValueError):img._validate_remote_url("http://localhost/a.png")

if __name__=="__main__":unittest.main()
