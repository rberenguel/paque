import logging
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from paque.task import Task

logger = logging.getLogger("paque.planner")


class Planner:
    def __init__(self, _tasks: Dict[str, Task]) -> None:
        self._tasks = _tasks
        logger.debug(self._tasks)
        self._steps: List[Task] = []

    def find_dependencies(self, task: str) -> List[str]:
        if task in self._tasks.keys():
            dependencies = self._tasks[task].depends
            logger.debug("DEPENDENCIES: %s", dependencies)
            if isinstance(dependencies, List):
                return [d.name for d in dependencies if d is not None]
            if isinstance(dependencies, Task):
                return [dependencies.name]
            if dependencies is None:
                return []
        raise Exception("Task required, and not found", task)

    @staticmethod
    def dependency_and_arguments(
        raw_dependency: str,
    ) -> Union[Tuple[str, List[str]], Tuple[str, None]]:
        if " " in raw_dependency:
            dependency, *args = raw_dependency.split(" ")
            return dependency, args
        return raw_dependency, None

    def _with_args(self, task_name: str, args: Optional[List[str]]) -> Task:
        logger.debug("Task to replace: %s", task_name)
        try:
            extracted = self._tasks[task_name]
        except KeyError as exc:
            logger.error("Task %s not found in file", task_name)
            sys.exit(-1)
        if args is not None:
            extracted.with_args(args)
        return extracted

    def _remaining(self, dependencies: List[str]) -> List[str]:
        done = {task.name for task in self._steps}
        return sorted(set(dependencies).difference(done))

    def _plan(self, task_name: str, args: Optional[List[str]] = None) -> None:
        initial_state = len(self._steps)
        logger.debug("Already ran: %s", self._steps)
        task = self._with_args(task_name, args)
        initial_dependencies = self.find_dependencies(task_name)
        dependencies = self._remaining(initial_dependencies)
        if len(dependencies) == 0:
            logger.debug("Can run %s(%s) with no dependencies left", task, args)
            step = self._with_args(task_name, args)
            if step not in self._steps:
                logger.debug("Adding step: %s", step)
                self._steps.append(self._with_args(task_name, args))
            return

        logger.debug("Has dependencies, plan them: %s", dependencies)
        for raw_dependency in dependencies:
            dependency, new_args = self.dependency_and_arguments(raw_dependency)
            logger.debug("Dependency %s has args %s", dependency, new_args)
            self._plan(dependency, new_args)

        if len(self._steps) > initial_state and len(self._remaining(dependencies)) != 0:
            logger.debug("Process has progressed, recurse on same task")
            self._plan(task_name, args)
        if len(self._remaining(dependencies)) == 0:
            logger.debug("We have parsed dependencies, fix and repeat on same task")
            self._plan(task_name, args)
        if len(self._steps) == initial_state:
            logger.debug("We have stopped improving")
            raise Exception("Could not find a plan to solve {}({})".format(task, args))
        logger.debug("Final recursion")
        self._plan(task_name, args)

    def plan(self, task: str) -> List[Task]:
        logger.info(">>> Planning execution for task %s", task)
        self._plan(task)
        abbreviated_plan = [task.name for task in self._steps]
        logger.info(">>> Plan requires %s", abbreviated_plan)
        correct_steps = []
        for step in self._steps:
            correct_step = step.replace_dependencies_with(self._steps)
            correct_steps.append(correct_step)
        return correct_steps
