# CrushCrushSaveEdit

A small toolkit for editing your **Crush Crush** save file. Crush Crush stores
its save data as a scrambled block of text that isn't human-readable on its
own. This project lets you turn that block into plain text you can edit
(e.g. change your diamond count, love levels, hearts, etc.), then turn your
edited text back into a save file the game can load.

## Requirements

[uv](https://docs.astral.sh/uv/) (preferable) or Python 3

## Usage

### Decoding a save
```shell
# copy your save into this project, then:
uv run tools/crushcrush_save.py decode "saves/crushcrush.sav" "decoded/crushcrush.txt"
```

### Encoding an edited save
```shell
# ...edit decoded/crushcrush.txt in a text editor...
uv run tools/crushcrush_save.py encode "decoded/crushcrush.txt" "saves/crushcrush.edited.sav"
# then copy saves/crushcrush.edited.sav back over your real save file
```

## Project layout

```
saves/     Put your Crush Crush save file(s) here to work on them.
decoded/   Plain-text versions of your save file end up here, ready to edit.
tools/     The scripts that do the decoding/encoding. You won't need to edit these.
```

Nothing in `saves/` or `decoded/` is required to have any particular name —
use whatever filename your save file already has (Crush Crush itself
defaults to naming it `crushcrush.sav`).

## Full walkthrough

### 1. Install uv

[uv](https://docs.astral.sh/uv/) is a small, free tool that runs Python
scripts without you needing to separately install Python yourself — it
downloads and manages one behind the scenes the first time it's needed.

Open a terminal (on Windows: search for "PowerShell" in the Start menu; on
macOS: search for "Terminal" in Spotlight; on Linux: whatever terminal your
distro provides) and run the command for your operating system:

**macOS / Linux:**
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

If you already use a package manager, that works too: `brew install uv`
(macOS/Homebrew), `winget install astral-sh.uv` (Windows), `pipx install uv`,
etc.

Close and reopen your terminal afterwards, then check it worked:

```
uv --version
```

If that prints something like `uv 0.11.8`, you're set. (You do not need to
separately install Python — uv handles that.)

### 2. Get this project onto your computer

If you haven't already, download/clone this project folder somewhere on
your computer, and open a terminal **in that folder**. In most terminals you
can do this by typing `cd ` (with a trailing space) and then dragging the
project folder from your file manager into the terminal window, which fills
in its path — then press Enter.

### 3. Find your Crush Crush save file

Locate the save file Crush Crush created on your computer/device. By
default, this is in a `SavesDir` folder inside the game's installation
folder, but may also be in your Steam Cloud (i.e. Steam's
`userdata/<SteamID64>/459820/remote` directory). The save file should be
called `crushcrush.sav`.

### 4. Copy it into this project

Copy that save file into the `saves/` folder in this project. The simplest
way is with your regular file manager: open both the folder containing your
save and this project's `saves/` folder side by side, and drag the file
across (holding Ctrl while dragging on Windows, or Option on macOS, keeps
the original in place and copies rather than moves it).

Alternatively, from a terminal:

```
cp /path/to/your/crushcrush.sav saves/
```

Keep the original filename — it makes the commands below easier to copy and
paste. If your filename contains spaces or parentheses, just remember to
wrap it in quotes in every command, e.g. `"saves/crushcrush (copy).sav"`.

### 5. Decode it to plain text

From a terminal, in the project's root folder, run:

```
uv run tools/crushcrush_save.py decode "saves/crushcrush.sav" "decoded/crushcrush.txt"
```

The first time you run this, uv may take a few seconds to set itself up —
that's normal. This creates `decoded/crushcrush.txt` — a plain text file you
can open in any text editor.

### 6. Edit the decoded text file

Open `decoded/crushcrush.txt` in a text editor (e.g. Notepad, TextEdit, VS
Code). You'll see lines like:

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

### 7. Re-encode it back into a save file

```
uv run tools/crushcrush_save.py encode "decoded/crushcrush.txt" "saves/crushcrush.edited.sav"
```

This creates a new file, `saves/crushcrush.edited.sav`, in the format Crush
Crush expects.

### 8. (Recommended) Double-check your edit worked

Decode the new file again and make sure it matches what you edited:

```
uv run tools/crushcrush_save.py decode "saves/crushcrush.edited.sav" "decoded/crushcrush.edited.txt"
```

Open `decoded/crushcrush.edited.txt` and confirm your change (e.g.
`Diamonds:500`) is there and everything else still looks intact.

### 9. Back up your original save, then replace it

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
uv run tools/crushcrush_save.py decode <path to .sav file> <path to output .txt file>

# Encode plain text back into a save file
uv run tools/crushcrush_save.py encode <path to .txt file> <path to output .sav file>
```

If you leave off the output path, `decode` prints the plain text straight to
your terminal and `encode` prints the encoded save data — useful for a quick
look without creating a file.

## Troubleshooting

- **The game won't load my edited save / crashes on load**: Restore your
  backup of the original save file. Then double-check you only changed
  values (not keys or `::` lines), and re-run the "double-check" step above
  before copying the file back to the game.
- **`command not found: uv`** (or `'uv' is not recognized...` on Windows):
  uv either isn't installed, or your terminal needs to be closed and
  reopened after installing it so it picks up the change. Re-run the
  install command from step 1 and open a fresh terminal window.
- **A path with spaces isn't working**: Make sure the whole path is wrapped
  in double quotes, e.g. `"saves/crushcrush (copy).sav"`.

## Wait, how does this actually work?

Crush Crush save files are base64 text hiding a compressed block of data.
If you're curious about the technical details of the format (useful if
you're modifying these tools, not required for normal editing), see
[AGENTS.md](AGENTS.md).

## AI Disclosure

AI coding tools were used in this project. Their function was to verify the encoding of saves and correctly decode and
decompress. They also wrote the tooling scripts and helped to generate the save schema which otherwise would have been a
long and boring boilerplate task my ADHD doesn't have the time for.
