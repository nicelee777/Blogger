"""Regression tests for known-obsolete FAQ/Guide statements."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from blogger_content_freshness import scan_document, visible_text

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads(
    (ROOT / "blogger/content-freshness-rules.json").read_text(encoding="utf-8")
)["rules"]


class FreshnessTests(unittest.TestCase):
    def test_ignores_css_and_comments_in_visible_text(self) -> None:
        html = "<style>.x{content:'오래된 설명'}</style><!--예정--><p>사용법</p>"
        self.assertEqual(visible_text(html), "사용법")

    def test_rejects_retired_update_panel(self) -> None:
        html = '<aside class="sm-faq-update"><p>업데이트 예정 기능 안내</p></aside>'
        self.assertTrue(scan_document(html, "faq", "ko", RULES))

    def test_rejects_old_multidevice_answer(self) -> None:
        html = "<p>여러 기기에서 데이터를 동기화하며 사용할 수 있도록 다중기기 지원을 준비하고 있습니다.</p>"
        self.assertTrue(any("multidevice" in e for e in scan_document(html, "faq", "ko", RULES)))

    def test_rejects_old_english_answer(self) -> None:
        html = '<details id="faq-multiple-devices"><p>We are preparing multiple-device support.</p></details>'
        self.assertTrue(scan_document(html, "faq", "en", RULES))

    def test_accepts_current_multidevice_answer(self) -> None:
        html = "<p>같은 계정으로 로그인하면 여러 기기에서 지원되는 근무 데이터를 동기화합니다.</p>"
        self.assertEqual(scan_document(html, "faq", "ko", RULES), [])

    def test_accepts_valid_guide_description(self) -> None:
        html = "<p>동료 화면에 들어가거나 월을 변경하면 최신 공유 근무를 다시 확인합니다.</p>"
        self.assertEqual(scan_document(html, "guide", "ko", RULES), [])


if __name__ == "__main__":
    unittest.main()
