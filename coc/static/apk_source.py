import requests
from bs4 import BeautifulSoup
import re
import time

APK_MIRROR_BASE = "https://www.apkmirror.com"
COC_PAGE = f"{APK_MIRROR_BASE}/apk/supercell/clash-of-clans/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_direct_apk_url(version_suffix="2"):
    """
    Skips to the latest APK download page and returns a working intermediate download URL.
    This link prompts the browser or urllib to download the actual APK.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    print("[*] Fetching main Clash of Clans page...")
    resp = session.get(COC_PAGE)
    soup = BeautifulSoup(resp.text, "html.parser")

    release_link = soup.select_one("div.appRow a.downloadLink")
    if not release_link:
        raise Exception("ERROR: No release link found on APKMirror home page")

    release_page_url = APK_MIRROR_BASE + release_link.get("href")
    print(f"[+] Latest release page: {release_page_url}")

    # Extract version string from the URL
    version_match = re.search(r"clash-of-clans-([\d-]+)-release", release_page_url)
    if not version_match:
        raise Exception("ERROR: Could not extract version number from release URL")

    version_str = version_match.group(1)
    version_segments = version_str.split("-")
    version_num = "-".join(version_segments[:3])

    # Construct the direct variant page
    download_page = f"{release_page_url}clash-of-clans-{version_num}-{version_suffix}-android-apk-download/"
    print(f"[+] Variant download page: {download_page}")

    variant_page = session.get(download_page)
    variant_soup = BeautifulSoup(variant_page.text, "html.parser")

    dl_button = variant_soup.select_one("a.downloadButton")
    if not dl_button:
        raise Exception("ERROR:Download button not found on variant page")

    intermediate_url = APK_MIRROR_BASE + dl_button.get("href")
    print(f"[+] Final download link (intermediate, triggers download): {intermediate_url}")
    return intermediate_url

if __name__ == "__main__":
    print(get_direct_apk_url())
