from pathlib import Path
import os
import zipfile
from resources.dictionary import ChineseDictionary
import requests

if not Path("resources/cedict_ts.u8").exists():
    if not os.path.exists("resources"):
        os.makedirs("resources")
    print("Downloading CC-CEDICT dictionary...")
    response = requests.get(
        "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
    )
    with open("resources/cedict_1_0_ts_utf-8_mdbg.zip", "wb") as f:
        f.write(response.content)
    print("Unzipping dictionary...")
    with zipfile.ZipFile("resources/cedict_1_0_ts_utf-8_mdbg.zip", "r") as zip_ref:
        zip_ref.extractall("resources")
    print("Dictionary downloaded and unzipped successfully")
    print("deleting zip file...")
    os.remove("resources/cedict_1_0_ts_utf-8_mdbg.zip")
    print("zip file deleted successfully")


def init_dictionary():
    # Initialize dictionary at startup - this loads it once when the app starts
    print("Initializing Chinese dictionary...")
    dictionary = ChineseDictionary()
    print("Dictionary ready!")

    return dictionary
