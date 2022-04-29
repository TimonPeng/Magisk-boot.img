import hashlib
import os
import shutil
import subprocess
import sys

import requests
from logzero import logger
from tqdm import tqdm


def true_or_quit(condition, message):
    if not condition:
        logger.error(message)
        sys.exit(1)


def calc_divisional_range(file_size, chuck):
    length = file_size // chuck
    flag = 0

    ranges = []
    for i in range(chuck - 1):
        start = i * length
        end = (i + 1) * length
        ranges.append((start, end - 1))
        flag = end

    ranges.append((flag, file_size - 1))

    return ranges


def calc_checksum(file_path, algorithm):
    return hashlib.new(algorithm, open(file_path, "rb").read()).hexdigest()


def download_file(url, file_path, display_name):
    response = requests.get(url, stream=True)
    total = int(response.headers.get("Content-Length", 0))

    with open(file_path, "wb") as file, tqdm(
        desc=display_name,
        total=total,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def unpack_file(file_path, unarchive_dir):
    shutil.unpack_archive(file_path, unarchive_dir)


def dump_images(file_path, output_dir):
    subprocess.run(
        [
            "./payload-dumper-go",
            "-partitions",
            "boot,recovery",
            "-output",
            output_dir,
            file_path,
        ],
        stdout=open(os.devnull, "wb"),
    )
