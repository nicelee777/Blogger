#!/usr/bin/env python3
"""Translate ShiftMate Blogger Page HTML without exposing markup to the model."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

API_URL = "https://api.openai.com/v1/responses"
GLOSSARY_PATH = Path("blogger/glossary.json")
BATCH_SIZE = 180
TOKEN_PREFIX = "__SM_I18N_"
HANGUL_RE = re.compile(r"[가-힣]")
TAG_SPLIT_RE = re.compile(r"(<!--.*?-->|<![^>]*>|<[^>]+>)", flags=re.S)
ATTR_RE = re.compile(
    r"(?P<prefix>(?<![\w:-])(?P<name>aria-label|data-search|data-title|placeholder|title|alt|lang)\s*=\s*)"
    r"(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    flags=re.I | re.S,
)

TRANSLATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["id", "text"],
            },
        }
    },
    "required": ["items"],
}


class SignatureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.signature: list[tuple[str, str, tuple[tuple[str, str], ...]]] = []

    @staticmethod
    def protected_attrs(
        attrs: list[tuple[str, str | None]],
    ) -> tuple[tuple[str, str], ...]:
        localizable = {
            "lang",
            "alt",
            "title",
            "aria-label",
            "placeholder",
            "data-search",
            "data-title",
        }
        return tuple(
            sorted(
                (
                    key,
                    "<LOCALIZED>" if key in localizable else (value or ""),
                )
                for key, value in attrs
            )
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.signature.append(("start", tag, self.protected_attrs(attrs)))

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.signature.append(("empty", tag, self.protected_attrs(attrs)))

    def handle_endtag(self, tag: str) -> None:
        self.signature.append(("end", tag, ()))


def signature(text: str):
    parser = SignatureParser()
    parser.feed(text)
    return parser.signature


def style_blocks(text: str) -> list[str]:
    return re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.I | re.S)


def protect_style_blocks(source: str) -> tuple[str, list[tuple[str, str]]]:
    """Hide CSS before segment extraction and restore it byte-for-byte later."""
    protected: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        token = f"<!--__SHIFTMATE_PROTECTED_STYLE_{len(protected)}__-->"
        protected.append((token, match.group(0)))
        return token

    masked = re.sub(r"<style\b[^>]*>.*?</style>", repl, source, flags=re.I | re.S)
    return masked, protected


def restore_style_blocks(text: str, protected: list[tuple[str, str]]) -> str:
    for token, original in protected:
        if text.count(token) != 1:
            raise ValueError(f"protected style placeholder missing or duplicated: {token}")
        text = text.replace(token, original)
    return text


def load_glossary(locale: str, path: Path = GLOSSARY_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    value = data.get(locale, {})
    if not isinstance(value, dict):
        raise ValueError(f"glossary for {locale} must be an object")
    return {str(k): str(v) for k, v in value.items()}


def extract_output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(str(content["text"]))
    if not chunks:
        raise RuntimeError("OpenAI response did not contain output_text")
    return "\n".join(chunks).strip()


def _token(index: int) -> str:
    return f"{TOKEN_PREFIX}{index:05d}__"


def _needs_translation(value: str) -> bool:
    return bool(HANGUL_RE.search(html.unescape(value)))


def build_translation_template(
    source: str,
    html_lang: str,
) -> tuple[str, list[dict[str, Any]], list[tuple[str, str]]]:
    """Replace only Korean text/attributes with stable placeholders.

    Markup never leaves this process. The model only receives plain text units.
    """
    if TOKEN_PREFIX in source:
        raise ValueError(f"source unexpectedly contains reserved token prefix {TOKEN_PREFIX}")

    masked, protected_styles = protect_style_blocks(source)
    units: list[dict[str, Any]] = []
    parts = TAG_SPLIT_RE.split(masked)
    rebuilt: list[str] = []

    def add_unit(value: str, kind: str) -> str:
        index = len(units)
        units.append(
            {
                "id": index,
                "kind": kind,
                "text": html.unescape(value),
            }
        )
        return _token(index)

    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith("<!--") or part.startswith("<!") or part.startswith("</"):
                rebuilt.append(part)
                continue

            def attr_repl(match: re.Match[str]) -> str:
                name = match.group("name").lower()
                quote = match.group("quote")
                value = match.group("value")
                prefix = match.group("prefix")
                if name == "lang":
                    return f"{prefix}{quote}{html.escape(html_lang, quote=True)}{quote}"
                if not value.strip() or not _needs_translation(value):
                    return match.group(0)
                return f"{prefix}{quote}{add_unit(value, name)}{quote}"

            rebuilt.append(ATTR_RE.sub(attr_repl, part))
            continue

        if not _needs_translation(part):
            rebuilt.append(part)
            continue

        leading = re.match(r"^\s*", part, flags=re.S).group(0)
        trailing = re.search(r"\s*$", part, flags=re.S).group(0)
        start = len(leading)
        end = len(part) - len(trailing) if trailing else len(part)
        core = part[start:end]
        if not core or not _needs_translation(core):
            rebuilt.append(part)
            continue
        rebuilt.append(f"{leading}{add_unit(core, 'text')}{trailing}")

    return "".join(rebuilt), units, protected_styles


def call_openai_batch(
    api_key: str,
    model: str,
    batch: list[dict[str, Any]],
    locale: str,
    language_name: str,
    content_type: str,
) -> dict[int, str]:
    glossary = load_glossary(locale)
    glossary_text = json.dumps(glossary, ensure_ascii=False, indent=2)
    input_payload = json.dumps(batch, ensure_ascii=False)

    instructions = f"""You are the localization engine for ShiftMate, a shift-calendar app.
Translate each input item's `text` from Korean into {language_name} ({locale}).
The items are text fragments extracted from a {content_type} HTML document. HTML markup is intentionally not provided.

STRICT RULES:
1. Return exactly one output item for every input `id`, with the same integer `id` exactly once.
2. Translate only the `text`. Never add HTML tags, Markdown, URLs, commentary, or placeholder tokens.
3. Fragments can sit next to formatting tags in the original document. Keep the translation grammatically compatible with the fragment itself; do not invent missing neighboring UI labels.
4. Keep ShiftMate and technical names such as Android, iPhone, Google, Chrome, Safari, YouTube, D, E, N, OFF unchanged where appropriate.
5. When a source phrase is an app UI label or navigation term covered by the glossary, use the glossary wording exactly. In ordinary prose, keep the same terminology while allowing natural grammar and capitalization.
6. For `kind=data-search`, produce concise search-friendly target-language keywords/synonyms, preserving technical tokens such as D E N OFF.
7. For accessibility/title/placeholder kinds, translate naturally and concisely.

GLOSSARY (Korean -> {language_name}):
{glossary_text}
"""
    payload = {
        "model": model,
        "instructions": instructions,
        "input": input_payload,
        "reasoning": {"effort": "none"},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "shiftmate_localization_batch",
                "strict": True,
                "schema": TRANSLATION_SCHEMA,
            }
        },
        "store": False,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"OpenAI API error {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc

    if str(data.get("status", "")) == "incomplete":
        raise RuntimeError(f"OpenAI response incomplete: {data.get('incomplete_details')}")

    try:
        result = json.loads(extract_output_text(data))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"translation batch output was not valid JSON: {exc}") from exc

    raw_items = result.get("items") if isinstance(result, dict) else None
    if not isinstance(raw_items, list):
        raise RuntimeError("translation batch output must contain an items array")

    expected_ids = {int(item["id"]) for item in batch}
    translated: dict[int, str] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            raise RuntimeError("translation batch item must be an object")
        item_id = int(item.get("id", -1))
        text = str(item.get("text", ""))
        if item_id in translated:
            raise RuntimeError(f"duplicate translation id: {item_id}")
        if "<" in text or ">" in text or TOKEN_PREFIX in text:
            raise RuntimeError(f"translation id {item_id} contains forbidden markup/token")
        translated[item_id] = text

    if set(translated) != expected_ids:
        missing = sorted(expected_ids - set(translated))
        extra = sorted(set(translated) - expected_ids)
        raise RuntimeError(f"translation batch id mismatch; missing={missing} extra={extra}")
    return translated


def translate_units(
    api_key: str,
    model: str,
    units: list[dict[str, Any]],
    locale: str,
    language_name: str,
    content_type: str,
) -> dict[int, str]:
    translated: dict[int, str] = {}
    for start in range(0, len(units), BATCH_SIZE):
        batch = units[start : start + BATCH_SIZE]
        print(
            f"  translating text batch {start // BATCH_SIZE + 1}/"
            f"{(len(units) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} items)"
        )
        translated.update(
            call_openai_batch(
                api_key,
                model,
                batch,
                locale,
                language_name,
                content_type,
            )
        )
    return translated


def render_translation(
    template: str,
    units: list[dict[str, Any]],
    translated: dict[int, str],
    protected_styles: list[tuple[str, str]],
) -> str:
    result = template
    for unit in units:
        item_id = int(unit["id"])
        token = _token(item_id)
        if result.count(token) != 1:
            raise ValueError(f"translation placeholder missing or duplicated: {token}")
        value = translated[item_id]
        if unit["kind"] == "text":
            safe = html.escape(value, quote=False)
        else:
            safe = html.escape(value, quote=True)
        result = result.replace(token, safe)
    return restore_style_blocks(result, protected_styles).rstrip() + "\n"


def assert_structure(source: str, translated: str) -> None:
    if signature(source) != signature(translated):
        raise ValueError("rendered localized HTML structure differs from source")
    if style_blocks(source) != style_blocks(translated):
        raise ValueError("rendered localized HTML changed CSS/style content")


def translate_preserving_structure(
    api_key: str,
    model: str,
    source: str,
    locale: str,
    language_name: str,
    html_lang: str,
    *,
    content_type: str,
) -> str:
    template, units, protected_styles = build_translation_template(source, html_lang)
    if not units:
        result = restore_style_blocks(template, protected_styles).rstrip() + "\n"
        assert_structure(source, result)
        return result

    translated = translate_units(
        api_key,
        model,
        units,
        locale,
        language_name,
        content_type,
    )
    result = render_translation(template, units, translated, protected_styles)
    assert_structure(source, result)
    return result


def rewrite_guide_locale_links(
    html_text: str,
    config: dict[str, Any],
    locale: str,
) -> str:
    """Point Guide FAQ links to the matching localized FAQ Page deterministically."""
    target = str(config["locales"][locale]["faq_path"])
    pattern = re.compile(
        r"(?P<prefix>href=[\"'])/p/faq-ko\.html(?:\?sm-lang=ko)?(?P<quote>[\"'])",
        flags=re.I,
    )

    def repl(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{target}{match.group('quote')}"

    return pattern.sub(repl, html_text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--content-type", choices=["faq", "guide"], default="faq")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--targets", nargs="*")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 2

    config = json.loads(args.config.read_text(encoding="utf-8"))
    source_locale = config.get("source_locale", "ko")
    locales = config["locales"]
    model = os.environ.get(
        "OPENAI_TRANSLATION_MODEL",
        config.get("translation_model", "gpt-5.6-luna"),
    )

    page_cfg = config.get("page_types", {}).get(args.content_type, {})
    default_dir = Path(page_cfg.get("directory", f"blogger/{args.content_type}"))
    source_path = args.source or (default_dir / f"{source_locale}.html")
    out_dir = args.out_dir or default_dir

    if not source_path.exists():
        print(f"Source page not found; skipping translation: {source_path}")
        return 0

    targets = args.targets or [key for key in locales if key != source_locale]
    source = source_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)

    for locale in targets:
        if locale not in locales:
            raise SystemExit(f"Unknown locale: {locale}")
        info = locales[locale]
        print(
            f"Translating {args.content_type}: {source_locale} -> {locale} "
            f"({info['name']}) with {model}..."
        )
        translated = translate_preserving_structure(
            api_key,
            model,
            source,
            locale,
            info["name"],
            info["html_lang"],
            content_type=args.content_type,
        )
        if args.content_type == "guide":
            translated = rewrite_guide_locale_links(translated, config, locale)
        out = out_dir / f"{locale}.html"
        out.write_text(translated, encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
