import requests
from logzero import logger
from pyquery import PyQuery as pq

from utils import true_or_quit

endpoint = "https://developers.google.com/android"
urls = {
    "ota": "/ota",
    # "factory": "/images",
}

cookies = {
    "devsite_wall_acks": "nexus-image-tos,nexus-ota-tos",
}

CONFIG = {
    "extension": "zip",
    "algorithm": "sha256",
}


def main():
    roms = {}

    for name, path in urls.items():
        response = requests.get(endpoint + path, cookies=cookies)
        response.raise_for_status()

        html = pq(response.text)
        titles = html("h2")
        tables = titles.next()
        titles_length = len(titles)
        tables_length = len(tables)

        true_or_quit(
            titles_length == tables_length,
            f"Fail to parse, titles length: {titles_length}, tables length: {tables_length}",
        )

        for index in range(tables_length):
            table = tables[index]
            if table.tag != "table":
                continue

            title = titles[index]
            model = title.text.replace('"', "")

            if roms.get("model") is None:
                roms[model] = []

            for rom_tr in table.findall("tr"):
                rom_tds = rom_tr.findall("td")
                rom_tds_length = len(rom_tds)

                true_or_quit(
                    rom_tds_length == 3,
                    f"Invalid td length {rom_tds_length} of {model}",
                )

                version_td, download_td, checksum_td = rom_tds
                version = version_td.text
                link = download_td.find("a").attrib.get("href")
                checksum = checksum_td.text

                true_or_quit(
                    version and link and checksum,
                    f"Invalid value of {model}, version: {version}, link: {link}, checksum: {checksum}",
                )

                roms[model].append(
                    {
                        "version": version,
                        "link": link,
                        "checksum": checksum,
                        "rom_name": name,
                        **CONFIG,
                    }
                )

    return roms


if __name__ == "__main__":
    main()
