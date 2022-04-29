from os import getcwd, listdir, makedirs
from os.path import isfile, join

import click
from logzero import logger
from werkzeug.utils import import_string

from utils import calc_checksum, download_file, dump_images

# os.path.dirname(os.path.abspath(__file__))
CURRENT_DIR = getcwd()
BRANDS_DIR = join(CURRENT_DIR, "brands")
IMAGES_DIR = join(CURRENT_DIR, "images")
TEMPS_DIR = join(CURRENT_DIR, "temps")


def get_brands():
    manufacturers = []

    for filename in listdir(BRANDS_DIR):
        # is directory
        if not isfile(join(BRANDS_DIR, filename)):
            continue

        if not filename.endswith(".py"):
            logger.warning(
                f"Manufacturer file {filename} is not a python file"
            )
            continue

        splited = filename.split(".")
        manufacturers.append(splited[0])

    return manufacturers


# TODO safe exit when dumping images
extracting_path = None


@click.command()
@click.option(
    "-b",
    "--brands",
    help="Select brands",
)
@click.option(
    "-d",
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode",
)
def main(brands, debug):
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    supported_brands = get_brands()
    logger.debug(f"Supported brands: {supported_brands}")

    selected_brands = brands.lower().split(",") if brands else []
    logger.debug(f"Selected brands: {selected_brands}")

    for brand in supported_brands:
        if selected_brands and brand.lower() not in selected_brands:
            continue

        logger.info(f"Processing brand: {brand}")
        brand_module = import_string(f"brands.{brand}")

        roms = brand_module.main()
        for (model, model_roms) in roms.items():
            logger.info(f"Processing model: {model}")

            for model_rom in model_roms:
                version = model_rom.get("version")
                logger.info(f"Processing version: {version}")

                link = model_rom.get("link")
                checksum = model_rom.get("checksum")
                rom_name = model_rom.get("rom_name")
                extension = model_rom.get("extension")
                logger.debug(f"{link} {checksum} {rom_name}.{extension}")

                # if images are exist, skip dump
                extracted_dir = join(
                    IMAGES_DIR, brand, model, version, rom_name
                )
                if isfile(join(extracted_dir, "boot.img")):
                    logger.debug(f"{version} images are already extracted")
                    continue

                download_dir = join(TEMPS_DIR, brand, model, version)
                rom_file_path = join(download_dir, f"{rom_name}.{extension}")

                # if rom file is exist and support checksum, skip download
                algorithm = model_rom.get("algorithm")
                if (
                    isfile(rom_file_path)
                    and algorithm
                    and calc_checksum(rom_file_path, algorithm) == checksum
                ):
                    logger.debug(f"{version} rom is already downloaded")
                else:
                    makedirs(download_dir, exist_ok=True)
                    # TODO split range download
                    download_file(link, rom_file_path, version)

                makedirs(extracted_dir, exist_ok=True)
                dump_images(rom_file_path, extracted_dir)


if __name__ == "__main__":
    main()
