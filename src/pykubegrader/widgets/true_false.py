from typing import List, Tuple

import panel as pn

from ..widgets_base.select import SelectQuestion
from .style import drexel_colors, raw_css

# Pass the custom CSS to Panel
pn.extension(design="material", global_css=[drexel_colors], raw_css=[raw_css])

#
# Style function
#


def TFStyle(
    descriptions: List[str],
    options: List[str] | List[List[str]],
    initial_vals: List[str],
) -> Tuple[List[pn.pane.HTML], List[pn.widgets.RadioBoxGroup]]:
    """
    Creates a styled True/False question layout with descriptions and radio buttons.

    Args:
        descriptions (List[str]): List of question descriptions.
        options (List[str] or List[List[str]]): List of options, either as a single list or list of lists.
        initial_vals (List[str]): Initial selected values for each question.

    Returns:
        Tuple[List[pn.pane.HTML], List[pn.widgets.RadioBoxGroup]]: Styled description panes and radio button groups.
    """
    desc_width = "100%"  # Responsive width for descriptions
    # button_width = "100%"  # Responsive width for radio buttons

    # Create description widgets
    desc_widgets = [
        pn.pane.HTML(
            f"""
            <div style="text-align: left; width: {desc_width}; padding: 10px 0;">
                <b>{desc}</b>
            </div>
            """,
            sizing_mode="stretch_width",
        )
        for desc in descriptions
    ]

    # Create radio button groups
    radio_buttons = [
        pn.widgets.RadioBoxGroup(
            options=option,
            value=value,
            width_policy="max",  # Automatically scales to fit content
            sizing_mode="stretch_width",  # Make width responsive
        )
        for value, option in zip(
            initial_vals,
            options if isinstance(options[0], list) else [options] * len(initial_vals),
        )
    ]

    return desc_widgets, radio_buttons


#
# Question class
#


class TFQuestion(SelectQuestion):
    def __init__(
        self,
        title="Select if the statement is True or False",
        style=TFStyle,
        question_number=2,
        keys=["MC1", "MC2", "MC3", "MC4"],
        options=None,
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
            options=[["True", "False"] for _ in range(len(keys))],
            descriptions=descriptions,
            points=points,
        )
