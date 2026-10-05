# Emoji Picker for AngelOS

Meta + . opens a searchable emoji picker on Niri. Search in Russian or English, press Enter to copy the complete emoji sequence, then Ctrl + V to paste into your application. Escape cancels without changing the clipboard. The settings page also has a launch button.

Install **Emoji Picker** from AngelOS Community Store and enable it in Settings → Plugins. Requirements: Python 3.10+, Niri with config includes, fuzzel, wl-clipboard (`wl-copy`), and an emoji font (such as Noto Color Emoji). `notify-send` provides an optional copied notification. Choose System, Dark, Light, Rose, From Wallpaper, or Custom colors (#RRGGBB) in the settings page. Emoji style: System, Google/Noto (requires the system Noto Color Emoji font), bundled Twemoji Mozilla, or a custom installed font family. Text sizes: 12/16/20. Emoji style affects this picker; the receiving app renders pasted emoji itself. Newer symbols absent from Twemoji fall back to system fonts. No network requests at runtime.

Enabling the plugin manages the Niri Meta/Mod + Period binding. The complete include tree is validated before each change. If the shortcut was assigned, its previous action is saved and restored when the plugin is disabled or removed; unrelated edits are preserved. Keep the plugin enabled while using the shortcut. Includes outside the Niri config directory and multiple conflicting bindings are rejected with a status message. This plugin targets Niri, not other compositors.

Emoji data: Unicode Emoji 16.0 fully qualified sequences (3781 entries), with Russian search terms from CLDR 46. Unicode data is redistributed under `data/LICENSE-UNICODE.txt`. Code is MIT licensed.

Tests: `python3 -m unittest discover -s tests -v` (requires Niri for real config validation).

Sources: https://unicode.org/Public/emoji/16.0/emoji-test.txt and https://github.com/unicode-org/cldr/tree/release-46/common/annotations.

On AngelOS with `appearanceThemes` support, these choices also appear beside built-in themes in the general Appearance theme list. The From Wallpaper option follows the active wallpaper using AngelOS's native palette generator, without replacing the current desktop palette. Older AngelOS versions still expose all options through the plugin settings.

Bundled unmodified Twemoji Mozilla v0.7.0, by Mozilla Foundation; visual artwork by Twitter/Twemoji contributors. License and attribution: `fonts/LICENSE-TWEMOJI.md` (Apache-2.0 code and CC-BY-4.0 artwork), https://github.com/mozilla/twemoji-colr.
