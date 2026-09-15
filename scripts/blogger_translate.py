#!/usr/bin/env python3
"""Translate ShiftMate Blogger HTML with the OpenAI Responses API."""
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
LOCALIZABLE_ATTRS = {"lang", "alt", "title", "aria-label"}


class SignatureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.signature: list[tuple[str, str, tuple[tuple[str, str], ...]]] = []

    @staticmethod
    def protected_attrs(attrs: list[tuple[str, str | None]]) -> tuple[tuple[str, str], ...]:
        return tuple(
            sorted(
                (key, value or "")
                for key, value in attrs
                if key not in LOCALIZABLE_ATTRS
            )
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.signature.append(("start", tag, self.protected_attrs(attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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
) -> str:
    glossary = load_glossary(locale)
    glossary_text = (
        json.dumps(glossary, ensure_ascii=False, indent=2)
        if glossary
        else "{}"
    )
    instructions = f'''You are the localization engine for ShiftMate, a shift-calendar app. Translate the supplied Blogger HTML from Korean into {language_name} ({locale}). Return ONLY the complete translated HTML, without Markdown fences or commentary.
STRICT RULES:
1. Translate only user-visible prose and localizable accessibility text. Preserve HTML tag order and nesting.
2. Never change URLs, email addresses, CSS, id, class, href, datetime, src, data-* attributes, aria-labelledby, or element order.
3. Do not add or remove FAQ items, sections, links, tags, comments, or attributes.
4. Keep product name ShiftMate and technical names such as Android, iPhone, Google Cloud, Chrome, Safari, MP3.
5. Use the glossary below EXACTLY when the Korean source term applies. Do not paraphrase glossary UI labels.
6. On the root element with class shiftmate-faq, set lang="{html_lang}". Do not change other protected attributes.
7. Preserve the meaning and emphasis (<strong>) of the source exactly.

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("blogger/config.json"))
    ap.add_argument("--source", type=Path, default=Path("blogger/faq/ko.html"))
    ap.add_argument("--out-dir", type=Path, default=Path("blogger/faq"))
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
    targets = args.targets or [key for key in locales if key != source_locale]
    source = args.source.read_text(encoding="utf-8")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for locale in targets:
        if locale not in locales:
            raise SystemExit(f"Unknown locale: {locale}")
        info = locales[locale]
        print(
            f"Translating {source_locale} -> {locale} "
            f"({info['name']}) with {model}..."
        )
        translated = call_openai(
            api_key,
            model,
            source,
            locale,
            info["name"],
            info["html_lang"],
        )
        assert_structure(source, translated)
        out = args.out_dir / f"{locale}.html"
        out.write_text(translated, encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
