import argparse
import logging
import os

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


def get_paquefile(args):
    paquefile = args.paquefile

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


def paque(args):
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    paquefile = get_paquefile(args)
    parser = YAMLParser(paquefile)
    planner = Planner(parser.parse())
    if args.dry_run:
        Executor(planner.plan(args.task[0])).dry_run()
    else:
        Executor(planner.plan(args.task[0])).run()


def main(**args):
    configure_logger()
    parser = argparse.ArgumentParser(description="Paque: Not make, but in Python")
    parser.add_argument(
        "paquefile",
        metavar="paquefile",
        type=str,
        help="File to run",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "task",
        metavar="task",
        type=str,
        help="Task to run from file",
        nargs=1,
        default=None,
    )
    parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true", help="Dry run the plan"
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Set logging to debug level"
    )
    args = parser.parse_args()
    try:
        paque(args)
    except Exception as exc:
        logger.error(exc)


if __name__ == "__main__":
    main()
