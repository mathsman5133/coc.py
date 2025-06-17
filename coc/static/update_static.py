"""
Automates updating the static files. If new files need to be added, then
place them in the TARGETS list.
"""
import json
import urllib
import urllib.request

# Targets first index is the URL and the second is the filename. If filename
# is None, then the url name is used
TARGETS = [
    ("buildings.json", None),
    ("characters.json", None),
    ("heroes.json", None),
    ("object_ids.json", None),
    ("pets.json", None),
    ("spells.json", None),
    ("supers.json", None),
    ("townhall_levels.json", None),
    ("lang/texts_EN.json", "texts_EN.json"),
]

BASE_URL = "https://coc.guide/static/json/"


def main():
    for target_file in TARGETS:
        req = urllib.request.Request(f"{BASE_URL}{target_file[0]}")
        try:
            print(f"[+] Downloading {req.full_url}")
            with urllib.request.urlopen(req) as response:
                bytes = response.read()
                encoding = response.info().get_content_charset('utf8')
        except urllib.error.URLError:
            print(f"[!] Failed to fetch {req.full_url}")
            continue

        json_obj = json.loads(bytes.decode(encoding))

        filename = target_file[0] if target_file[1] is None else target_file[1]
        with open(filename, "wt", encoding="UTF-8") as outfile:
            json.dump(json_obj, outfile)


if __name__ == "__main__":
    main()
