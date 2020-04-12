from paque import __version__
from paque.planner import Planner
from paque.task import Task
from paque.parser import YAMLParser
import logging

logging.basicConfig(level=logging.DEBUG)


def test_version():
    assert __version__ == "0.1.0"


def test_processes_argument_list():
    two = "C argument1_to_C argument2_to_C"
    assert Planner.dependency_and_arguments(two) == (
        "C",
        ["argument1_to_C", "argument2_to_C"],
    )


def test_planner_simple_plan_():
    simple_plan = {
        "E": [{"sleep": 1}],
        "A": [{"depends": ["C", "D", "E"]}],
        "C": [{"depends": ["E"]}],
        "D": [{"sleep": 1}],
    }
    plan = Planner(YAMLParser("none")._build_tasks(simple_plan)).plan("A")
    task_e = Task("E", sleep=1)
    task_c = Task("C", depends=[task_e])
    task_d = Task("D", sleep=1)
    task_a = Task("A", depends=[task_c, task_d, task_e])
    assert plan == [
        task_e,
        task_c,
        task_d,
        task_a,
    ]


def test_planner_plan_with_args():
    complex_plan = {
        "A": [{"depends": ["C arg:argument_to_C", "D"]}],
        "B": [{"depends": ["A"]}],  # I'm forcing it to be always a list here
        "C": [{"run": "{arg}"}],
        "D": [{"sleep": 1}],
    }
    plan = Planner(YAMLParser("none")._build_tasks(complex_plan)).plan("B")
    task_d = Task("D", sleep=1)
    task_c = Task("C arg:argument_to_C", run="argument_to_C")
    task_a = Task("A", depends=[task_c, task_d])
    task_b = Task("B", depends=[task_a])
    assert plan == [
        task_c,
        task_d,
        task_a,
        task_b,
    ]


def test_planner_plan_with_several_args():
    complex_plan = {
        "A": [{"depends": ["C arg:argument_to_C arg2:argument_to_C_2", "D"]}],
        "B": [{"depends": ["A"]}],
        "C": [{"run": "{arg} {arg2}"}],
        "D": [{"sleep": 1}],
    }
    plan = Planner(YAMLParser("none")._build_tasks(complex_plan)).plan("B")
    task_c = Task(
        "C arg:argument_to_C arg2:argument_to_C_2", run="argument_to_C argument_to_C_2",
    )
    task_d = Task("D", sleep=1)
    task_a = Task("A", depends=[task_c, task_d])
    task_b = Task("B", depends=[task_a])
    assert plan == [
        task_c,
        task_d,
        task_a,
        task_b,
    ]


def test_planner_plan_with_several_weirdly_ordered_args():
    complex_plan = {
        "A": [{"depends": ["C arg2:argument_to_C_2 arg:{argA}", "D"]}],
        "B": [{"depends": ["A argA:argument_to_A"]}],
        "C": [{"run": "{arg} {arg2}"}],
        "D": [{"sleep": 1}],
    }
    plan = Planner(YAMLParser("none")._build_tasks(complex_plan)).plan("B")
    task_c = Task(
        "C arg2:argument_to_C_2 arg:argument_to_A argA:argument_to_A",
        run="argument_to_A argument_to_C_2",
    )
    task_d = Task("D argA:argument_to_A", sleep=1)
    task_a = Task("A argA:argument_to_A", depends=[task_c, task_d],)
    task_b = Task("B", depends=[task_a])
    assert plan == [
        task_c,
        task_d,
        task_a,
        task_b,
    ]
