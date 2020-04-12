import argparse
import logging
import os

from colorlog import ColoredFormatter  # type: ignore

from pake.executor import Executor
from pake.parser import YAMLParser
from pake.planner import Planner

logger = logging.getLogger("pake")


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


def get_pakefile(args):
    pakefile = args.pakefile

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

    if pakefile is None:

        candidates = ["pakefile", "pakefile.yaml"]
        try:
            indexer = list(map(check_file, candidates)).index(True)
        except ValueError:
            indexer = None
        if indexer is None:
            raise Exception(
                "No file provided and neither pakefile, pakefile.yaml are available"
            )
        return candidates[indexer]
    if check_file(pakefile):
        return pakefile


def pake(args):
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    pakefile = get_pakefile(args)
    parser = YAMLParser(pakefile)
    planner = Planner(parser.parse())
    if args.dry_run:
        Executor(planner.plan(args.task[0])).dry_run()
    else:
        Executor(planner.plan(args.task[0])).run()


def main(**args):
    configure_logger()
    parser = argparse.ArgumentParser(description="Pake: Not make, but in Python")
    parser.add_argument(
        "pakefile",
        metavar="pakefile",
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
        pake(args)
    except Exception as exc:
        logger.error(exc)


if __name__ == "__main__":
    main()
