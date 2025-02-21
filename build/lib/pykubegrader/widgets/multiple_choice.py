from typing import Tuple

import panel as pn

from ..utils import list_of_lists
from ..widgets_base.select import SelectQuestion

#
# Style function
#


def MCQ(
    descriptions: list[str],
    options: list[str] | list[list[str]],
    initial_vals: list[str],
) -> Tuple[list[pn.pane.HTML], list[pn.widgets.RadioButtonGroup]]:
    desc_width = "350px"

    desc_widgets = [
        pn.pane.HTML(
            f"<div style='text-align: left; width: {desc_width};'><b>{desc}</b></div>"
        )
        for desc in descriptions
    ]

    radio_buttons = [
        pn.widgets.RadioBoxGroup(
            options=option,
            value=value,
            width=300,
        )
        for value, option in zip(
            initial_vals,
            options if list_of_lists(options) else [options] * len(initial_vals),
        )
    ]

    return desc_widgets, radio_buttons


#
# Question class
#


class MCQuestion(SelectQuestion):
    def __init__(
        self,
        title="Select the option that matches the definition:",
        style=MCQ,
        question_number=2,
        keys=["MC1", "MC2", "MC3", "MC4"],
        options=[
            ["List", "Dictionary", "Tuple", "Set"],
            ["return", "continue", "pass", "break"],
            ["*", "^", "**", "//"],
            [
                "list.add(element)",
                "list.append(element)",
                "list.insert(element)",
                "list.push(element)",
            ],
        ],
        descriptions=[
            "Which of the following stores key:value pairs?",
            "The following condition returns to the next iteration of the loop",
            "Which operator is used for exponentiation in Python?",
            "Which method is used to add an element to the end of a list in Python?",
        ],
        points=2,
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
