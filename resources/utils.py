from pathlib import Path
import json
import re
import os
import zipfile
from resources.dictionary import ChineseDictionary
import requests

hsk_vocab = None


def init_dictionary():
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

    # Initialize dictionary at startup - this loads it once when the app starts
    print("Initializing Chinese dictionary...")
    dictionary = ChineseDictionary()
    print("Dictionary ready!")

    return dictionary


def get_hsk_vocabulary():
    if not Path("resources/hsk_vocabulary.json").exists():
        print("Downloading HSK vocabulary...")
        response = requests.get(
            "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/refs/heads/main/complete.json"
        )
        with open("resources/hsk_vocabulary.json", "wb") as f:
            f.write(response.content)
        print("HSK vocabulary downloaded successfully")
    else:
        print("HSK vocabulary already downloaded")

    file = json.load(open("resources/hsk_vocabulary.json"))

    vocab = {}
    for entry in file:
        vocab[entry["simplified"]] = entry["level"]

    return vocab


def _lookup_hsk_level(phrase: str) -> str:
    global hsk_vocab
    if hsk_vocab is None:
        hsk_vocab = get_hsk_vocabulary()

    lvl = hsk_vocab.get(phrase, None)
    if lvl is not None:
        lvl = re.sub(r"[^0-9+]", "", lvl[-1])

    return lvl


def get_hsk_level(phrase: str) -> int:
    lvl = _lookup_hsk_level(phrase)
    if lvl is not None:
        return lvl

    unique_substrings = {
        phrase[i:j] for i in range(len(phrase)) for j in range(i + 1, len(phrase) + 1)
    }

    lvls = [_lookup_hsk_level(substring) for substring in unique_substrings]

    max_val = max(
        lvls,
        key=lambda s: (-1, False)
        if s is None
        else (int(s.rstrip("+")), s.endswith("+")),
    )

    return max_val
