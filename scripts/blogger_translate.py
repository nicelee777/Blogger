#!/usr/bin/env python3
"""Translate ShiftMate Blogger Page HTML with the OpenAI Responses API."""
from __future__ import annotations

import argparse
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
# Values may be localized, but the attributes themselves must remain present.
LOCALIZABLE_ATTRS = {
    "lang",
    "alt",
    "title",
    "aria-label",
    "placeholder",
    "data-search",
    "data-title",
}


class SignatureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.signature: list[tuple[str, str, tuple[tuple[str, str], ...]]] = []

    @staticmethod
    def protected_attrs(
        attrs: list[tuple[str, str | None]],
    ) -> tuple[tuple[str, str], ...]:
        # Localizable attributes keep a sentinel value so the model may change the
        # value but may not remove/add the attribute itself.
        return tuple(
            sorted(
                (
                    key,
                    "<LOCALIZED>" if key in LOCALIZABLE_ATTRS else (value or ""),
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
                chunks.append(content["text"])
    if not chunks:
        raise RuntimeError("OpenAI response did not contain output_text")
    return "\n".join(chunks).strip()


def call_openai(
    api_key: str,
    model: str,
    source: str,
    locale: str,
    language_name: str,
    html_lang: str,
    content_type: str = "faq",
    extra_instruction: str = "",
) -> str:
    glossary = load_glossary(locale)
    glossary_text = (
        json.dumps(glossary, ensure_ascii=False, indent=2) if glossary else "{}"
    )

    type_rules = {
        "faq": (
            "This content is an FAQ Page. Do not add, remove, reorder, merge, or split "
            "FAQ items, sections, links, tags, comments, or attributes."
        ),
        "guide": (
            "This content is a long-form User Guide Page. Do not add, remove, reorder, "
            "merge, or split sections, media embeds, links, tags, comments, or attributes."
        ),
        "post": (
            "This content is a Blogger Post. Do not add, remove, reorder, merge, or split "
            "sections, media embeds, links, tags, comments, or attributes."
        ),
    }
    if content_type not in type_rules:
        raise ValueError(f"unsupported translation content type: {content_type}")

    root_rule = (
        f'If the document root has a lang attribute, set it to "{html_lang}". '
        "Do not change other protected attributes."
    )
    retry_rule = f"\n9. {extra_instruction}" if extra_instruction else ""

    instructions = f'''You are the localization engine for ShiftMate, a shift-calendar app. Translate the supplied Blogger HTML from Korean into {language_name} ({locale}). Return ONLY the complete translated HTML, without Markdown fences or commentary.
STRICT RULES:
1. Translate only user-visible prose and permitted localizable attribute values. Preserve HTML tag order and nesting exactly.
2. Never change URLs, email addresses, CSS, id, class, href, datetime, src, data-video-id, data-guide-search, aria-labelledby, iframe/video source URLs, or element order. Other data-* attributes must also stay unchanged EXCEPT data-search and data-title, whose values must be translated.
3. {type_rules[content_type]}
4. Keep product name ShiftMate and technical names such as Android, iPhone, Google Cloud, Chrome, Safari, YouTube, MP3.
5. Use the glossary below EXACTLY when the Korean source term applies. Do not paraphrase glossary UI labels.
6. {root_rule}
7. Preserve every existing formatting tag such as <strong>, <em>, <span>, <br>, <details>, and <summary> in exactly the same position. Never add formatting tags.
8. Translate alt, title, aria-label, placeholder, data-search, and data-title values naturally. For data-search, use useful search synonyms in the target language while preserving the attribute itself.{retry_rule}

GLOSSARY (Korean -> {language_name}):
{glossary_text}'''
    payload = {
        "model": model,
        "instructions": instructions,
        "input": source,
        "reasoning": {"effort": "none"},
        "store": False,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"OpenAI API error {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc

    text = extract_output_text(data)
    if text.startswith("```"):
        text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return text.strip() + "\n"


def assert_structure(source: str, translated: str) -> None:
    if signature(source) != signature(translated):
        raise ValueError(
            "translated HTML structure or protected attributes differ from source"
        )
    if style_blocks(source) != style_blocks(translated):
        raise ValueError("translated HTML changed CSS/style content")


def translate_preserving_structure(
    api_key: str,
    model: str,
    source: str,
    locale: str,
    language_name: str,
    html_lang: str,
    *,
    content_type: str,
    attempts: int = 3,
) -> str:
    """Translate and automatically retry when the model changes HTML structure."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        extra = ""
        if attempt > 1:
            extra = (
                "RETRY AFTER STRUCTURE VALIDATION FAILURE: reproduce the source HTML skeleton "
                "character-for-character in tag sequence and protected attributes. Change only "
                "text nodes and the permitted localizable attribute values (lang, alt, title, "
                "aria-label, placeholder, data-search, data-title). Do not add, remove, move, "
                "or wrap any element or attribute."
            )
        translated = call_openai(
            api_key,
            model,
            source,
            locale,
            language_name,
            html_lang,
            content_type=content_type,
            extra_instruction=extra,
        )
        try:
            assert_structure(source, translated)
            if attempt > 1:
                print(f"  structure-safe translation succeeded on attempt {attempt}")
            return translated
        except ValueError as exc:
            last_error = exc
            print(
                f"  structure validation failed for {locale} "
                f"(attempt {attempt}/{attempts}); retrying...",
                file=sys.stderr,
            )
    raise ValueError(
        f"translation for {locale} failed structure validation after {attempts} attempts: "
        f"{last_error}"
    )


def rewrite_guide_locale_links(
    html: str,
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

    return pattern.sub(repl, html)


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
