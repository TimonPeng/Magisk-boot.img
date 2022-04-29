import signal
import sys
from os import getcwd, listdir, makedirs
from os.path import exists, isfile, join
from shutil import rmtree

import click
from logzero import logger
from werkzeug.utils import import_string

from utils import calc_checksum, download_file, dump_images, not_empty

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


# safe exit when dumping images path
dumping_path = None
dumping_pid = None


def safe_exit(signum, frame):
    logger.info("Exiting...")
    if dumping_path:
        rmtree(dumping_path)
    sys.exit()


@click.command()
@click.option(
    "-b",
    "--brands",
    help="Select partitions brands, comma-separated",
    default="",
)
@click.option(
    "-m",
    "--models",
    help="Select partitions models, comma-separated",
    default="",
)
@click.option(
    "-v",
    "--versions",
    help="Select partitions versions, comma-separated",
    default="",
)
@click.option(
    "-f",
    "--force-dump/--no-force-dump",
    default=False,
    help="Force dump ROM",
)
@click.option(
    "-d",
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode",
)
def main(brands, models, versions, force_dump, debug):
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    global dumping_path

    signal.signal(signal.SIGINT, safe_exit)
    signal.signal(signal.SIGTERM, safe_exit)

    supported_brands = get_brands()
    logger.debug(f"Supported brands: {supported_brands}")

    selected_brands = list(filter(not_empty, brands.lower().split(",")))
    logger.debug(f"Selected brands: {selected_brands}")
    selected_models = list(filter(not_empty, models.lower().split(",")))
    logger.debug(f"Selected models: {selected_models}")
    selected_versions = list(filter(not_empty, versions.lower().split(",")))
    logger.debug(f"Selected versions: {selected_versions}")

    for brand in supported_brands:
        if selected_brands and brand.lower() not in selected_brands:
            continue

        logger.info(f"Processing brand: {brand}")
        brand_module = import_string(f"brands.{brand}")

        roms = brand_module.main()
        for (model, model_roms) in roms.items():
            model_bypass = True

            if selected_models:
                model_lower = model.lower()

                for selected_model in selected_models:
                    if selected_model in model_lower:
                        model_bypass = False
                        break
            else:
                model_bypass = False

            if model_bypass:
                continue

            logger.info(f"Processing model: {model}")

            for model_rom in model_roms:
                version = model_rom.get("version")

                version_bypass = True

                if selected_versions:
                    version_lower = version.lower()

                    for selected_version in selected_versions:
                        if selected_version in version_lower:
                            version_bypass = False
                            break
                else:
                    version_bypass = False

                if version_bypass:
                    continue

                logger.info(f"Processing version: {version}")

                link = model_rom.get("link")
                checksum = model_rom.get("checksum")
                rom_name = model_rom.get("rom_name")
                extension = model_rom.get("extension")
                logger.debug(f"{link} {checksum} {rom_name}.{extension}")

                extracted_dir = join(
                    IMAGES_DIR, brand, model, version, rom_name
                )
                download_dir = join(TEMPS_DIR, brand, model, version)
                rom_file_path = join(download_dir, f"{rom_name}.{extension}")

                # if images are exist, skip and clean up
                if not force_dump and isfile(join(extracted_dir, "boot.img")):
                    logger.debug("Images are already extracted")

                    if exists(download_dir):
                        logger.debug("Clean up ROM...")
                        rmtree(download_dir)

                    continue

                # if rom file is exist and support checksum, skip download
                algorithm = model_rom.get("algorithm")
                if (
                    isfile(rom_file_path)
                    and algorithm
                    and calc_checksum(rom_file_path, algorithm) == checksum
                ):
                    logger.debug("ROM is already downloaded")
                else:
                    makedirs(download_dir, exist_ok=True)
                    # TODO split range download
                    # TODO failed retry
                    download_file(link, rom_file_path, version)

                logger.debug("Processing dump images...")
                makedirs(extracted_dir, exist_ok=True)
                dumping_path = extracted_dir
                # TODO check dump result
                dump_task = dump_images(rom_file_path, extracted_dir)
                dumping_path = None

                # clean up
                logger.debug("Clean up...")
                rmtree(download_dir)


if __name__ == "__main__":
    main()
