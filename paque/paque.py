import logging
import os

import click
from colorlog import ColoredFormatter  # type: ignore

from paque.executor import Executor
from paque.parser import YAMLParser
from paque.planner import Planner

logger = logging.getLogger("paque")


def configure_logger():
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "yellow",
            "INFO": "cyan",
            "WARNING": "purple",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_paquefile(paquefile):
    def check_file(candidate: str):
        try:
            candidate_path = os.path.join(os.getcwd(), candidate)
            with open(candidate_path) as _:
                logger.debug("File found: %s", candidate_path)
                return True
        except IOError:
            logger.debug("File not found: %s (IO failed)", candidate_path)
            return False
        logger.debug("File not found: %s (no exception?)", candidate_path)
        return False

    print(paquefile)
    if paquefile is None:

        candidates = ["paquefile", "paquefile.yaml"]
        try:
            indexer = list(map(check_file, candidates)).index(True)
        except ValueError:
            indexer = None
        if indexer is None:
            raise Exception(
                "No file provided and neither paquefile, paquefile.yaml are available"
            )
        return candidates[indexer]
    if check_file(paquefile):
        return paquefile


@click.command()
@click.argument("task", required=True)
@click.argument("path", default="paquefile.yaml", required=False)
@click.option(
    "--dry-run", default=False, is_flag=True, help="Dry run, logging the plan",
)
@click.option("--debug", help="Set log level to debug", is_flag=True)
def paque(task, path, dry_run, debug):
    """Paque simplifies running simple workflows you want to run. It offers a few
features of `make`, but removing most of its power. It runs on a `paquefile` or
`paquefile.yaml` (or just pass the name of the file)

    """
    configure_logger()
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    paquefile = get_paquefile(path)
    parser = YAMLParser(paquefile)
    planner = Planner(parser.parse())
    if dry_run:
        try:
            Executor(planner.plan(task)).dry_run()
        except Exception as exc:
            logger.exception(exc)
    else:
        try:
            Executor(planner.plan(task)).run()
        except Exception as exc:
            logger.exception(exc)


if __name__ == "__main__":
    paque()
