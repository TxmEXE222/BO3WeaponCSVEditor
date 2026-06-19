## BO3 Weapon .CSV Editor

Tool for editing `level_common_weapon.csv` in Black Ops III.

Made by TxmEXE222. 
Big thanks to WeaponCSV by MakeCentsGaming for the inspiration.

## Features

- Editor tab with weapon fields, dropdowns for bools / weaponVO / class
- Spreadsheet tab - sort columns, filter rows
- Preview tab - shows what the saved file looks like, highlights changed lines
- Drag and drop a csv onto the window
- Undo/redo (Ctrl+Z / Ctrl+Y)
- Section breaks, comment out rows with `//`, copy rows, warns on duplicate weapon names

Built for Windows. Should run on other OS if you have tkinter but I haven't tested that.

## Setup

Need Python 3.10+.
Pillow 10.0+.
tkinterdnd2 0.3.0+

```
pip install -r requirements.txt
python BO3CSVEditor.py
```

## Building an exe

```
pip install pyinstaller
pyinstaller --noconfirm --clean BO3WeaponCSVEditor.spec
```
(A plain pyinstaller BO3CSVEditor.py build sometimes misses icons/images, breaks drag-and-drop, and uses different defaults.)

Your exe ends up at `dist\BO3WeaponCSVEditor\BO3WeaponCSVEditor.exe`. Keep that whole folder, don't just copy the exe out.
