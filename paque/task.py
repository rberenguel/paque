import logging
from typing import Dict, List, Optional, Union

Section = Optional[Union[List[str], str, int]]

logger = logging.getLogger("paque.Task")


class Task:
    """Task instance. Having it as a separate entity (instead of faking it with
dictionaries inside of the Planner) means it's easier to test, debug and swap
implementations. Obviously"""

    def __init__(
        self,
        name: str = "",
        run: Optional[str] = None,
        depends: Optional[List["Task"]] = None,
        message: Optional[str] = None,
        sleep: Optional[str] = None,
        condition: Optional[str] = None,
    ):
        self.name = name
        self.run = run
        self.depends = depends
        self.message = message
        self.sleep = sleep
        self.condition = condition

    def __repr__(self) -> str:
        """Why did you use emoji? Why not?"""
        depends_if_then_runs = f"[{self.depends}] ({self.condition}?)-> {self.run}"
        says_sleeps = f"(🗣 {self.message},😴 {self.sleep})"
        return f"Task({self.name}: {depends_if_then_runs} {says_sleeps}"

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return repr(self) < repr(other)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.name == other.name and str(self) == str(other)

    def replace_dependencies_with(self, steps: List["Task"]) -> "Task":
        """Replace dependencies with fully processed dependencies. This is to ensure
the final plan has all tasks as the final state requires. This is actually an
advantage when faking it with dictionaries inside the Planner: you can do this
by just replacements as you go. Not with a separate Task implementation with
properties.

        """
        proper_dependencies = []
        if self.depends is None:
            return self
        for dependency in self.depends:
            done_step = [step for step in steps if step.name == dependency.name][0]
            proper_dependencies.append(done_step)
        self.depends = proper_dependencies
        return self

    @staticmethod
    def _args_dict(args: List[str]) -> Dict[str, str]:
        """Helper to convert arguments to dictionries for formatting/replacement"""
        args_dict = {}
        for arg in args:
            key, value = arg.split(":")
            args_dict[key] = value
        return args_dict

    def with_args(self, args: Optional[List[str]]) -> "Task":
        """Replaces the properties of this task with the replacements after argument
substitution"""

        def interpolate(item):
            try:
                return item.format(**args_dict)
            except KeyError as e:
                raise Exception(f"Argument not found: {e}")

        logger.debug("Task: %s", self)
        logger.debug("args: %s", args)

        if args is None:
            return self

        args_string = " ".join(args)

        args_dict: Dict[str, str] = self._args_dict(args)
        self.name = interpolate(self.name)
        if args_string not in self.name:
            self.name = self.name + " {}".format(args_string)
        if self.run is not None:
            self.run = interpolate(self.run)
        if self.message is not None:
            self.message = interpolate(self.message)
        if self.sleep is not None:
            self.sleep = interpolate(self.sleep)
        if self.condition is not None:
            self.condition = interpolate(self.condition)
        if self.depends is not None:  # Depends can be an empty list instead of None!
            self.depends = [
                dependency.with_args(args)
                for dependency in self.depends
                if dependency is not None
            ]

        logger.debug("interpolated Task: %s", self)
        return self

    def get_sleep(self) -> Optional[int]:
        """Sleep is special: it eventually needs to be an integer. We cast it at the
very end of the processes"""
        if self.sleep is None:
            return None
        try:
            return int(self.sleep)
        except ValueError as v:
            raise Exception("Sleep should be an integer by this point %s", v)
