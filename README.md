# CrushCrushSaveEdit

A small toolkit for editing your **Crush Crush** save file. Crush Crush stores
its save data as a scrambled block of text that isn't human-readable on its
own. This project lets you turn that block into plain text you can edit
(e.g. change your diamond count, love levels, hearts, etc.), then turn your
edited text back into a save file the game can load.

No prior programming knowledge is required, but you will need to use a
terminal (command line) to run a couple of commands.

## Requirements

- **Python 3** installed on your computer. No extra packages need to be
  installed — everything this tool needs comes built into Python.
  - To check if you already have it, open a terminal and run:
    ```
    python3 --version
    ```
    If that prints a version number (e.g. `Python 3.11.4`), you're good to go.
    On Windows you may need to use `python` instead of `python3`.

## Project layout

```
saves/     Put your Crush Crush save file(s) here to work on them.
decoded/   Plain-text versions of your save file end up here, ready to edit.
tools/     The scripts that do the decoding/encoding. You won't need to edit these.
```

Nothing in `saves/` or `decoded/` is required to have any particular name —
use whatever filename your save file already has (Crush Crush itself
defaults to naming it `crushcrush.sav`).

## Step-by-step: editing your save

### 1. Find your Crush Crush save file

Locate the save file Crush Crush created on your computer/device (if you're
not sure where that is, check the game's settings, its installation folder,
or your platform's usual save-game location — the file itself is a small
text file with no file icon preview, often named `crushcrush.sav`).

### 2. Copy it into this project

Copy that save file into the `saves/` folder in this project. You can do
this with your regular file manager (drag and drop), or from a terminal:

```
cp /path/to/your/crushcrush.sav saves/
```

Keep the original filename — it makes the commands below easier to copy and
paste. If your filename contains spaces or parentheses, just remember to
wrap it in quotes in every command, e.g. `"saves/crushcrush (copy).sav"`.

### 3. Decode it to plain text

From the project's root folder, run:

```
python3 tools/crushcrush_save.py decode "saves/crushcrush.sav" "decoded/crushcrush.txt"
```

This creates `decoded/crushcrush.txt` — a plain text file you can open in
any text editor.

### 4. Edit the decoded text file

Open `decoded/crushcrush.txt` in a text editor (e.g. Notepad, TextEdit, VS
Code — anything that edits plain text). You'll see lines like:

```
::
Diamonds:3
::
```

and, further down, sections like:

```
::GirlCassie
Clothing:1073741824i
Hearts:204188
LifeDates:17i
LifeOutfits:1610612736i
Love:9i
```

A few things worth knowing before you edit:

- Each `::` on its own line separates entries. A `::SomethingLikeThis` line
  starts a named section — the plain lines under it (until the next `::`)
  belong to that section (e.g. everything under `::GirlCassie` is about
  Cassie).
- Numbers ending in `i` are whole numbers (integers) — e.g. `Love:9i` means
  a love level of 9. Numbers ending in `f` are decimals (e.g. `Time:0f`).
  Plain numbers with no letter suffix are also whole numbers.
- Only change the **values** (the part after the `:`). Don't rename keys,
  and don't add or remove `::` lines, or the file may fail to load in-game.
- Example: to give yourself 500 diamonds instead of 3, find the line
  `Diamonds:3` and change it to `Diamonds:500`.

Save the text file when you're done editing.

### 5. Re-encode it back into a save file

```
python3 tools/crushcrush_save.py encode "decoded/crushcrush.txt" "saves/crushcrush.edited.sav"
```

This creates a new file, `saves/crushcrush.edited.sav`, in the format Crush
Crush expects.

### 6. (Recommended) Double-check your edit worked

Decode the new file again and make sure it matches what you edited:

```
python3 tools/crushcrush_save.py decode "saves/crushcrush.edited.sav" "decoded/crushcrush.edited.txt"
```

Open `decoded/crushcrush.edited.txt` and confirm your change (e.g.
`Diamonds:500`) is there and everything else still looks intact.

### 7. Back up your original save, then replace it

Before overwriting anything, make a backup copy of your **original** save
file somewhere safe (outside this project), in case anything goes wrong.

Once you're confident the edited file is correct, copy
`saves/crushcrush.edited.sav` back to your Crush Crush save location,
replacing the original file there — and rename it to match the filename the
game expects (e.g. `crushcrush.sav`).

```
cp "saves/crushcrush.edited.sav" /path/to/your/crushcrush.sav
```

Then start Crush Crush and confirm your changes loaded correctly.

## Quick reference

```
# Decode a save file to plain text
python3 tools/crushcrush_save.py decode <path to .sav file> <path to output .txt file>

# Encode plain text back into a save file
python3 tools/crushcrush_save.py encode <path to .txt file> <path to output .sav file>
```

If you leave off the output path, `decode` prints the plain text straight to
your terminal and `encode` prints the encoded save data — useful for a quick
look without creating a file.

## Troubleshooting

- **The game won't load my edited save / crashes on load**: Restore your
  backup of the original save file. Then double-check you only changed
  values (not keys or `::` lines), and re-run the "double-check" step above
  before copying the file back to the game.
- **`command not found: python3`**: Try `python` instead, or install Python
  3 from [python.org](https://www.python.org/downloads/) if it isn't
  installed yet.
- **A path with spaces isn't working**: Make sure the whole path is wrapped
  in double quotes, e.g. `"saves/crushcrush (copy).sav"`.

## Wait, how does this actually work?

Crush Crush save files are base64 text hiding a compressed block of data.
If you're curious about the technical details of the format (useful if
you're modifying these tools, not required for normal editing), see
[AGENTS.md](AGENTS.md).

## AI Disclosure

AI coding tools were used in this project. Their function was to verify the encoding of saves and correctly decode and decompress. They also wrote the tooling scripts and helped to generate the save schema which otherwise would have been a long and boring boilerplate task my ADHD doesn't have the time for.