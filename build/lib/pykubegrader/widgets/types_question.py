from typing import Tuple

import panel as pn

from ..utils import list_of_lists
from ..widgets_base.select import SelectQuestion

#
# Style function
#


def MultipleChoice(
    descriptions: list[str],
    options: list[str] | list[list[str]],
    initial_vals: list[str],
) -> Tuple[list[pn.pane.HTML], list[pn.widgets.Select]]:
    desc_width = "350px"

    desc_widgets = [
        pn.pane.HTML(
            f"<div style='text-align: left; width: {desc_width};'><b>{desc}</b></div>"
        )
        for desc in descriptions
    ]

    dropdowns = [
        pn.widgets.Select(options=option, value=value, width=300)
        for value, option in zip(
            initial_vals,
            options if list_of_lists(options) else [options] * len(initial_vals),
        )
    ]

    return desc_widgets, dropdowns


#
# Question class
#


class TypesQuestion(SelectQuestion):
    def __init__(
        self,
        title="Select the option that matches the definition:",
        style=MultipleChoice,
        question_number=1,
        keys=["types1", "types2", "types3", "types4", "types5", "types6"],
        options=[
            "None",
            "list",
            "function",
            "dictionary",
            "array",
            "variable",
            "integer",
            "string",
            "tuple",
            "iterator",
            "float",
            "object",
            "class",
            "module",
            "package",
            "instance",
        ],
        descriptions=[
            "An ordered, mutable collection of items, defined with [ ]",
            "A file containing Python definitions and statements",
            "A collection of elements of the same type, allowing for efficient storage and manipulation of sequences of data",
            "An immutable and ordered collection of elements in Python, which can contain mixed data types",
            "A sequence of Unicode characters",
            "A data type that represents real numbers with a decimal point",
        ],
        points=3,
    ):
        super().__init__(
            title=title,
            style=style,
            question_number=question_number,
            keys=keys,
            options=options,
            descriptions=descriptions,
            points=points,
        )
