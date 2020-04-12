import pytest
from pake.task import Task


def test_args_dict():
    sample = ["arg1:item1", "arg2:item2"]
    assert Task._args_dict(sample) == {"arg1": "item1", "arg2": "item2"}


@pytest.mark.parametrize("parameter", ["run", "message", "sleep"])
def test_double_interpolate_task_(parameter):
    dic = {"name": "C", parameter: "{arg1} {arg2}"}
    task = Task(**dic)
    args = ["arg1:argument_to_C", "arg2:argument_to_C_2"]
    task.with_args(args)
    print(task)
    assert getattr(task, parameter) == "argument_to_C argument_to_C_2"
    assert task.name == "C arg1:argument_to_C arg2:argument_to_C_2"
