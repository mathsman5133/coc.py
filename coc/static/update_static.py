"""
Automates updating the static files.
Now saves both the raw CSV and the generated JSON files.
If new files need to be added, then place them in the TARGETS list.
"""
import aiohttp
import asyncio
import json
import traceback
import urllib
import urllib.request
import logging
import zstandard
import lzma
import csv
import os
import zipfile
from collections import defaultdict

TARGETS = [
    ("logic/buildings.csv", "buildings.csv"),
    ("logic/characters.csv", "characters.csv"),
    ("logic/heroes.csv", "heroes.csv"),
    ("logic/pets.csv", "pets.csv"),
    ("logic/spells.csv", "spells.csv"),
    ("logic/super_licences.csv", "supers.csv"),
    ("logic/townhall_levels.csv", "townhall_levels.csv"),
    ("logic/character_items.csv", "equipment.csv"),
    ("localization/texts.csv", "texts_EN.csv"),
]

APK_URL = "https://d.apkpure.net/b/APK/com.supercell.clashofclans?version=latest"

def get_fingerprint():
    async def download():
        async with aiohttp.request('GET', APK_URL) as fp:
            c = await fp.read()
        return c

    data = asyncio.run(download())

    with open("apk.zip", "wb") as f:
        f.write(data)
    zf = zipfile.ZipFile("apk.zip")
    with zf.open('assets/fingerprint.json') as fp:
        fingerprint = json.loads(fp.read())['sha']

    os.unlink("apk.zip")
    return fingerprint

# Hard-code or fallback
FINGERPRINT = get_fingerprint()
BASE_URL = f"https://game-assets.clashofclans.com/{FINGERPRINT}"

def decompress(data):
    """
    Decompresses the given bytes 'data' if needed (LZHAM, ZSTD, or LZMA).
    Returns (decompressed_bytes, compression_details).
    """
    if data[0:4] == b"SCLZ":
        logging.debug("Decompressing using LZHAM ...")
        import lzham

        dict_size = int.from_bytes(data[4:5], byteorder="big")
        uncompressed_size = int.from_bytes(data[5:9], byteorder="little")

        decompressed = lzham.decompress(data[9:], uncompressed_size, {"dict_size_log2": dict_size})
        return decompressed, {
            "dict_size": dict_size,
            "uncompressed_size": uncompressed_size,
        }

    import zstandard
    if int.from_bytes(data[0:4], byteorder="little") == zstandard.MAGIC_NUMBER:
        logging.debug("Decompressing using ZSTD ...")
        decompressed = zstandard.decompress(data)
        return decompressed, {
            "dict_size": None,
            "uncompressed_size": None,
        }

    # Otherwise, assume LZMA
    logging.debug("Decompressing using LZMA ...")
    data = data[0:9] + (b"\x00" * 4) + data[9:]
    prop = data[0]
    o_prop = prop
    if prop > (4 * 5 + 4) * 9 + 8:
        raise Exception("LZMA properties error")
    import lzma
    decompressed = lzma.LZMADecompressor().decompress(data)
    return decompressed, {"lzma_prop": o_prop}


def process_csv(data, file_path, save_name):
    """
    1. Decompress data -> raw CSV
    2. Write raw CSV
    3. Parse CSV -> final_data[troop][level] = { col_name : value, ... }
       with carry-over for blank Name / VisualLevel.
    4. Post-process:
       - If troop has only one level, do nothing.
       - Else, for each column in the first level (lowest numeric),
         if it does NOT appear in other levels, move it to top-level.
    5. Convert "true"/"false" => bool, numeric => int.
    6. Write out JSON with (troop->level) structure.
    """
    decompressed_data, _ = decompress(data)

    # 1) Write out the raw CSV
    with open(file_path, "wb") as f:
        f.write(decompressed_data)

    import csv
    with open(file_path, encoding='utf-8') as csvf:
        rows = list(csv.reader(csvf))

    if len(rows) < 2:
        with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
            jf.write("{}")
        return

    columns = rows[0]
    final_data = {}
    current_troop = None
    current_level = None

    # 2) Parse & build final_data
    for row_index in range(2, len(rows)):
        row = rows[row_index]
        if not row:
            continue

        # carry-over logic
        if len(row) > 0 and row[0].strip():
            current_troop = row[0].strip()
        if len(row) > 1 and row[1].strip():
            current_level = row[1].strip()

        if not current_troop or not current_level:
            continue

        if current_troop not in final_data:
            final_data[current_troop] = {}
        if current_level not in final_data[current_troop]:
            final_data[current_troop][current_level] = {}

        # fill columns, converting values
        for col_idx, col_name in enumerate(columns):
            if col_idx < len(row):
                val = row[col_idx].strip()
                if val != "":
                    # Convert "true"/"false" => bool
                    if val.lower() == "true":
                        converted = True
                    elif val.lower() == "false":
                        converted = False
                    else:
                        # Attempt numeric => int
                        if val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
                            converted = int(val)
                        else:
                            converted = val

                    final_data[current_troop][current_level][col_name] = converted

    # 3) Post-processing: move columns only in base_level up to top-level
    for troop_name, levels_dict in final_data.items():
        # e.g. levels_dict = { "1": {...}, "2": {...} }
        all_levels = sorted(levels_dict.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
        if len(all_levels) <= 1:
            # only 1 level => do nothing
            continue

        base_level = all_levels[0]
        base_cols = list(levels_dict[base_level].keys())

        for col in base_cols:
            # check if col is present in other levels
            found_elsewhere = False
            for lvl in all_levels[1:]:
                if col in levels_dict[lvl]:
                    found_elsewhere = True
                    break
            # if not found in other levels => move it up
            if not found_elsewhere:
                if col not in levels_dict:
                    # move the single-value column up
                    final_data[troop_name][col] = levels_dict[base_level][col]
                # remove from base_level
                del levels_dict[base_level][col]

    # 4) Write final JSON
    import json
    with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
        jf.write(json.dumps(final_data, indent=2))


def check_header(data):
    if data[0] == 0x5D:
        return "csv"
    if data[:2] == b"\x53\x43":
        return "sc"
    if data[:4] == b"\x53\x69\x67\x3a":
        return "sig:"
    if data[:6] == b'"Name"' or data[:6] == b'"name"':
        return "decoded csv"
    raise Exception("Unknown header")

def main():
    for target_file, target_save in TARGETS:
        target_save = target_file if target_save is None else target_save
        download_url = f"{BASE_URL}/{target_file}"

        print(f"Downloading: {download_url}")
        with urllib.request.urlopen(download_url, timeout=10) as conn:
            data = conn.read()

        # Save raw compressed data
        with open(target_save, "wb") as f:
            f.write(data)

        file_type = check_header(data)
        if file_type == "csv":
            # data is already uncompressed CSV
            process_csv(data=data, file_path=target_save, save_name=target_save.split(".")[0])
        elif file_type == "sig:":
            # skip first 68 bytes, then decompress
            process_csv(data=data[68:], file_path=target_save, save_name=target_save.split(".")[0])
        else:
            # treat as compressed
            process_csv(data=data, file_path=target_save, save_name=target_save.split(".")[0])

if __name__ == "__main__":
    main()
