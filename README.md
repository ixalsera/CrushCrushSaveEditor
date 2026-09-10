# CrushCrushSaveEdit

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) [![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A toolkit for decoding, editing, and re-encoding Crush Crush save files across various platforms.

Crush Crush stores its save data as a scrambled block of text that isn't human-readable on its own. This project turns
that block into structured JSON you can edit — diamond count, love levels, hearts, and more — then turns your edited
text back into a save file the game can load.

### Currently Supported Platforms

| Platform | Supported |
|----------|-----------|
| Steam    | Yes       |
| Nutaku   | Partial   |
| iOS      | No        |
| Android  | No        |
| Switch   | Yes       |

## Background

Crush Crush's save format is `base64(3-byte magic + LZF-compressed plaintext)` — an undocumented encoding,
reverse-engineered for this project by diffing successive saves and cross-referencing Unity's own `PlayerPrefs` storage.
See the schema docs under [`docs/`](docs) for what's been mapped out so far.

## Install

Requires [uv](https://docs.astral.sh/uv/) (preferred) or Python 3.13+.

1. [Install uv](https://docs.astral.sh/uv/getting-started/).
2. Download or clone this project onto your computer, then open a terminal **in that folder**.

## Usage

### Quick reference

```shell
# Decode a save file to JSON
uv run tools/crushcrush_save.py decode <path to .sav file> <path to output .json file>

# Encode JSON back into a save file
uv run tools/crushcrush_save.py encode <path to .json file> <path to output .sav file>
```

Leave off the output path and `decode`/`encode` print straight to your terminal instead of writing a file.

### Step-by-step

1. **Copy your save file into `saves/`** in this project.
2. **Decode it:**
   ```shell
   uv run tools/crushcrush_save.py decode "saves/crushcrush.sav" "decoded/crushcrush.json"
   ```
   This creates `decoded/crushcrush.json`, a JSON file you can open in any code editor.

3. **Edit `decoded/crushcrush.json`.** A schema is provided for IntelliSense if your editor supports it.

4. **Re-encode it:**
   ```shell
   uv run tools/crushcrush_save.py encode "decoded/crushcrush.json" "saves/crushcrush.edited.sav"
   ```

   If you're re-encoding for the Nintendo Switch version:
   ```shell
   uv run tools/crushcrush_save.py encode --nintendo "decoded/crushcrush.json" "saves/crushcrush.edited.sav"
   ```

5. **(Recommended) Double-check your edit worked** by decoding the new file again and confirming your change is there
   and everything else looks intact:
   ```shell
   uv run tools/crushcrush_save.py decode "saves/crushcrush.edited.sav" "decoded/crushcrush.edited.json"
   ```

6. **Back up your original save** somewhere outside this project, then copy the edited file over it — renamed to match
   what the game expects (e.g. `crushcrush.sav` for Steam or `CrushSaveData1` for Switch). Start Crush Crush and
   confirm your changes loaded correctly.

## Project Layout

```
saves/     Put your Crush Crush save file(s) here to work on them.
decoded/   Plain-text versions of your save file end up here, ready to edit.
tools/     The scripts that do the decoding/encoding. You won't need to edit these.
```

Nothing in `saves/` or `decoded/` needs a particular name — use whatever filename your save file already has.

## AI Disclosure

AI coding tools were used in this project. Their function was to verify the encoding of saves, correctly decode and
decompress, and diff saves. They also wrote the tooling scripts and helped to generate the save schema. Otherwise, all
this would have been a long and boring boilerplate task my ADHD doesn't have the time for.

## Contributing

This is a personal reverse-engineering project, but PRs and issues are welcome — especially new schema findings. For
anything beyond a small fix, please open an issue first to discuss the approach.

## License

MIT © Sera Honour — see [LICENSE](LICENSE) for details.
