"""
Automates updating the static files. If new files need to be added, then
place them in the TARGETS list.
"""
import asyncio
import json
import tempfile
import logging

import aiohttp
import csv
import os
import zipfile
from collections import defaultdict

import lzma
import zstandard

# Targets first index is the URL and the second is the filename. If filename
# is None, then the url name is used
TARGETS = [
    ("assets/logic/buildings.csv", "buildings.csv"),
    ("assets/logic/characters.csv", "characters.csv"),
    ("assets/logic/heroes.csv", "heroes.csv"),
    ("assets/logic/pets.csv", "pets.csv"),
    ("assets/logic/spells.csv", "spells.csv"),
    ("assets/logic/super_licences.csv", "supers.csv"),
    ("assets/logic/townhall_levels.csv", "townhall_levels.csv"),
    ("assets/logic/character_items.csv", "equipment.csv"),
    ("assets/localization/texts.csv", "texts_EN.csv"),
]
FINGERPRINT = "fffdcbe6cfb14f18138ef6efe9ecbd4ed55b75911"
BASE_URL = f"https://game-assets.clashofclans.com/{FINGERPRINT}"
APK_URL = "https://d.apkpure.net/b/APK/com.supercell.clashofclans?version=latest"


def decompress(data):
    if data[0:4] == b"SCLZ":
        logging.debug("Decompressing using LZHAM ...")
        # Credits: https://github.com/Galaxy1036/pylzham
        import lzham

        dict_size = int.from_bytes(data[4:5], byteorder="big")
        uncompressed_size = int.from_bytes(data[5:9], byteorder="little")

        logging.debug(f"dict size: {dict_size}")
        logging.debug(f"uncompressed size: {uncompressed_size}")

        decompressed = lzham.decompress(
            data[9:], uncompressed_size, {"dict_size_log2": dict_size}
        )
        compression_details = {
            "dict_size"        : dict_size,
            "uncompressed_size": uncompressed_size,
        }
    elif int.from_bytes(data[0:4], byteorder="little") == zstandard.MAGIC_NUMBER:
        logging.debug("Decompressing using ZSTD ...")
        decompressed = zstandard.decompress(data)
        compression_details = {
            "dict_size"        : None,
            "uncompressed_size": None,
        }
    else:
        logging.debug("Decompressing using LZMA ...")
        # fix uncompressed size to 64 bit
        data = data[0:9] + (b"\x00" * 4) + data[9:]

        prop = data[0]
        o_prop = prop
        if prop > (4 * 5 + 4) * 9 + 8:
            raise Exception("LZMA properties error")
        pb = int(prop / (9 * 5))
        prop -= int(pb * 9 * 5)
        lp = int(prop / 9)
        lc = int(prop - lp * 9)
        logging.debug(f"literal context bits: {lc}")
        logging.debug(f"literal position bits: {lp}")
        logging.debug(f"position bits: {pb}")
        dictionary_size = int.from_bytes(data[1:5], byteorder="little")
        logging.debug(f"dictionary size: {dictionary_size}")
        uncompressed_size = int.from_bytes(data[5:13], byteorder="little")
        logging.debug(f"uncompressed size: {uncompressed_size}")
        compression_details = {
            "dict_size"        : dictionary_size,
            "uncompressed_size": uncompressed_size,
            "lc"               : lc,
            "lp"               : lp,
            "pb"               : pb,
            "prop"             : prop,
            "original_prop"    : o_prop,
        }
        decompressed = lzma.LZMADecompressor().decompress(data)
    return decompressed, compression_details





def process_csv(data, file_path, save_name):
    # decompress the data if needed
    if not (data[:6] == '"Name"' or data[:6] == b'"Name"' or data[:6] == b'"name"' or data[:6] == b'"name"'):
        decompressed = decompress(data)

        with open(f"{file_path}", "wb") as f:
            f.write(decompressed[0])

    # create a dictionary
    data = defaultdict(lambda: defaultdict(list))

    # Open a csv reader called DictReader
    with open(f"{file_path}", encoding='utf-8') as csvf:
        csv_reader = csv.reader(csvf, delimiter=',')
        line_count = 0
        column_names = {}
        key = None
        for row in csv_reader:
            if line_count == 0:
                for count, item in enumerate(row):
                    column_names[count] = item
                line_count += 1
            elif line_count == 1:
                line_count += 1
                continue
            else:
                for count, item in enumerate(row):
                    if count == 0 and item != "":
                        key = item
                    else:
                        if item == "TRUE":
                            item = True
                        elif item == "FALSE":
                            item = False
                        elif item.isnumeric():
                            item = int(item)
                        elif item == "":
                            if not data[key][column_names[count]]:
                                continue
                            item = data[key][column_names[count]][-1]
                        data[key][column_names[count]].append(item)
        try:
            del data["String"]
        except:
            pass
    # Open a json writer, and use the json.dumps()
    # function to dump data
    with open(f"{save_name}.json", 'w', encoding='utf-8') as jsonf:
        if save_name in ["characters", "heroes"]:
            data_copy = data.copy()
            for key, item in data_copy.items():
                not_equal = len(data_copy[key]["VisualLevel"]) != data_copy[key]["VisualLevel"][-1]
                has_levels = data_copy[key]["VisualLevel"]
                change = data_copy[key]["VisualLevel"][-1] - len(data_copy[key]["VisualLevel"])
                if not_equal and has_levels:
                    for k, i in item.items():
                        if i:
                            data[key][k] = [data_copy[key][k][0] for x in range(change)] + i

        jsonf.write(json.dumps(data, indent=4))

    # clean up the .csv file, it is not used in coc.py
    os.unlink(file_path)


def check_header(data):
    if data[0] == 0x5D:
        return "csv"
    if data[:2] == b"\x53\x43":
        return "sc"
    if data[:4] == b"\x53\x69\x67\x3a":
        return "sig:"
    if data[:6] == '"Name"' or data[:6] == b'"Name"' or data[:6] == b'"name"' or data[:6] == b'"name"':
        return "decoded csv"
    raise Exception("  Unknown header")


def get_fingerprint():
    import aiohttp
    import asyncio

    async def download():
        async with aiohttp.request('GET', APK_URL) as fp:
            c = await fp.read()
        return c

    data = asyncio.run(download())

    temp_dir = tempfile.TemporaryDirectory()
    os.makedirs(temp_dir.name)
    file=os.path.join(temp_dir.name,"apk.zip")
    print(f" tempAPKFile: {file}")
    with open(f"{file}", "wb") as f:
        f.write(data)
    zf = zipfile.ZipFile(f"{file}")
    with zf.open('assets/fingerprint.json') as fp:
        fingerprint = json.loads(fp.read())['sha']

    # clean up apk
    try:
        os.unlink(f"{file}")
    except PermissionError as e:
        print (f" {e}")

    return fingerprint


def save_apk():
    async def download():
        async with aiohttp.request('GET', APK_URL) as fp:
            c = await fp.read()
        return c

    data = asyncio.run(download())

    temp_dir = tempfile.TemporaryDirectory().name
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file = os.path.join(temp_dir,"apk.zip")
    print(f" apk_file: {file}")
    with open(f"{file}", "wb") as f:
        f.write(data)
    zf = zipfile.ZipFile(f"{file}")
    print(f"zip file {zf}")
    return file


def find_file_in_zip(zip_path, target_file):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List all files in the zip
        all_files = zip_ref.namelist()

        # Check if the target file exists in the zip
        if target_file in all_files:
            # Extract and read the content of the target file
            with zip_ref.open(target_file) as file:
                content = file.read()
                return content
        else:
            return f"File {target_file} not found in the zip."


def main():

    apk_zip=save_apk()
    for target_file, target_save in TARGETS:
        """
        target_save = target_file if target_save is None else target_save
        download_url = f"{BASE_URL}/{target_file}"

        print(download_url)
        with urllib.request.urlopen(download_url, timeout=10) as conn:
            data = conn.read()

       

        with open(target_save, "wb") as f:
            f.write(data)
        """
        data = find_file_in_zip(apk_zip,target_file)

        file_type = check_header(data)
        if file_type == "csv":
            process_csv(data=data, file_path=target_save, save_name=target_save.split(".")[0])
        elif file_type == "sig:":
            process_csv(data=data[68:], file_path=target_save, save_name=target_save.split(".")[0])


if __name__ == "__main__":
    main()
