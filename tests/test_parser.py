from pake.parser import YAMLParser
from pake.task import Task


def test_builds_a_task():
    """Note that testing the parser is... horrible, since the parsing of arguments
and dependencies is deferred to the actual evaluation of the plan. So, better
to just test it as part of the Planner tests, where it is used as well"""
    plan = {
        "A": [{"depends": ["C arg:argument_to_C arg2:argument_to_C_2", "D"]}],
        "B": [{"depends": ["A"]}],
        "C": [{"run": "{arg} {arg2}"}],
        "D": [{"sleep": 1}],
    }

    parsed = YAMLParser("none")._build_tasks(plan)
    print(parsed)
    task_c = Task("C", run="{arg} {arg2}",)
    task_c_ = Task("C arg:argument_to_C arg2:argument_to_C_2",)
    task_d = Task("D", sleep=1)
    task_d_ = Task("D")
    task_a = Task("A", depends=[task_c_, task_d_])
    task_a_ = Task("A")
    task_b = Task("B", depends=[task_a_])
    assert parsed == {
        "C": task_c,
        "D": task_d,
        "A": task_a,
        "B": task_b,
    }
