import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import yaml

from paque.task import Section, Task

logger = logging.getLogger("paque.Task")


class Parser(ABC):
    """If you want a different parser, suit yourself. The expected API is a
dictionary of Dict[str, Task], with keys being the names of the tasks"""

    def __init__(self, filename: str):
        self._filename = filename

    @abstractmethod
    def _get_run(self, task_def) -> Optional[str]:
        pass

    @abstractmethod
    def _get_condition(self, task_def) -> Optional[str]:
        pass

    @abstractmethod
    def _get_message(self, task_def) -> Optional[str]:
        pass

    @abstractmethod
    def _get_sleep(self, task_def) -> Optional[str]:
        pass

    @abstractmethod
    def _get_depends(self, task_def) -> Optional[List[Task]]:
        pass

    @abstractmethod
    def parse(self) -> Dict[str, Task]:
        pass


class YAMLParser(Parser):
    """Specific parser for YAML files"""

    def __init__(self, filename: str):
        self.filename = filename

    @staticmethod
    def _find_section(dic, section: str) -> Section:
        """Only allows one section with the same name (that's the 0 at the end).
        Casting specific sections to specific types is done explicitly in _build_tasks

        """
        values = list(filter(lambda x: section in x.keys(), dic))
        if len(values) == 0:
            return None
        return values[0][section]

    def _get_run(self, task_def) -> Optional[str]:
        _run = self._find_section(task_def, "run")
        if _run is None:
            return None
        if isinstance(_run, List):
            if all([isinstance(run_item, str) for run_item in _run]):
                return "\n".join(_run)
        if isinstance(_run, str):
            return _run
        raise Exception("Run section should only contain a string or list of strings")

    def _get_condition(self, task_def) -> Optional[str]:
        _condition = self._find_section(task_def, "condition")
        if _condition is None:
            return None
        if isinstance(_condition, List):
            if all([isinstance(condition_item, str) for condition_item in _condition]):
                return "\n".join(_condition)
        if isinstance(_condition, str):
            return _condition
        raise Exception(
            "Condition section should only contain a string or list of strings"
        )

    def _get_sleep(self, task_def) -> Optional[str]:
        """Sleep if cast to an integer _after_ all variables have been evaluated. So,
this can only fail when running (or dry-running )the plan"""
        _sleep = self._find_section(task_def, "sleep")
        if _sleep is None:
            return None
        if isinstance(_sleep, str):
            return _sleep
        if isinstance(_sleep, int):
            return str(_sleep)
        raise Exception(
            "Sleep section should only contain integers or strings (to be interpolated by arguments)"
        )

    def _get_depends(self, task_def) -> Optional[List[Task]]:
        _depends = self._find_section(task_def, "depends")
        if _depends is None:
            return None
        if isinstance(_depends, List):
            if all([isinstance(dependency, str) for dependency in _depends]):
                return [Task(name=name) for name in _depends]
        raise Exception(
            "Depends section should only contain an array of strings (if only one dependency, break it as an array)"
        )

    def _get_message(self, task_def) -> Optional[str]:
        _message = self._find_section(task_def, "message")
        if _message is None:
            return None
        if isinstance(_message, List):
            if all([isinstance(message_item, str) for message_item in _message]):
                return "\n".join(_message)
        if isinstance(_message, str):
            return _message
        raise Exception(
            "Message section should only contain a string or list of strings"
        )

    def _build_tasks(self, parsed_yaml: Dict[str, Any]) -> Dict[str, Task]:
        task_dict = {}
        for task_name, task_def in parsed_yaml.items():
            run: Optional[str] = self._get_run(task_def)
            sleep: Optional[str] = self._get_sleep(task_def)
            message: Optional[str] = self._get_message(task_def)
            depends: Optional[List[Task]] = self._get_depends(task_def)
            condition: Optional[str] = self._get_condition(task_def)
            task = Task(task_name, run, depends, message, sleep, condition)
            task_dict[task_name] = task
        return task_dict

    def parse(self) -> Dict[str, Task]:
        data = open(self.filename, "r")
        try:
            loaded = yaml.safe_load(data)
        except Exception as e:
            raise Exception("Could not load the YAML file: %s", e)
        return self._build_tasks(loaded)
