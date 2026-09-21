# ShiftMate Blogger theme runtime

`shiftmate-menu-runtime-v6.js` is the canonical 10-locale language/menu runtime for the Blogger theme.

Managed locales:

- English (`lang`)
- Español (`lang-es`)
- Deutsch (`lang-de`)
- Français (`lang-fr`)
- Português (Brasil) (`lang-pt-br`)
- 简体中文 (`lang-zh-cn`)
- 繁體中文 (`lang-zh-tw`)
- 한국어 (`lang-ko`)
- 日本語 (`lang-ja`)
- Tiếng Việt (`lang-vi`)

FAQ and Guide use Blogger Pages. Notice and Story use label-combination URLs.

FAQ/Guide links must use the clean Blogger Page paths from `blogger/config.json` (for example `/p/faq-ko.html` and `/p/guide-ko.html`) without `?sm-lang=...`. The runtime keeps the selected locale in `localStorage`, removes the legacy `sm-lang` query parameter from FAQ/Guide URLs with `history.replaceState`, and maintains clean canonical/hreflang links for those Pages.

When applying this runtime to the live Blogger theme, replace the existing contents of the `<script id='shiftmate-menu-runtime'>...</script>` block with the contents of `shiftmate-menu-runtime-v6.js` while keeping the script element itself.

Important: Blogger API v3 used by this repository manages Pages and Posts, not the theme HTML. Theme deployment therefore remains a separate Blogger Theme edit step.
