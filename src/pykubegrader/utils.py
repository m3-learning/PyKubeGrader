import os
import random
from typing import Optional, Tuple

import panel as pn

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")


def list_of_lists(options: list) -> bool:
    return all(isinstance(elem, list) for elem in options)


def shuffle_options(
    options: list[Optional[str]] | list[list[Optional[str]]], seed: int
) -> list[Optional[str]] | list[list[Optional[str]]]:
    random.seed(seed)
    random.shuffle(options)

    if list_of_lists(options):
        for i in range(len(options)):
            inner_list: list[Optional[str]] = options[i]  # type: ignore
            random.shuffle(inner_list)

    return options


def shuffle_questions(
    desc_widgets: list[pn.pane.HTML],
    dropdowns: list[pn.widgets.Select] | list[pn.Column],
    seed: int,
) -> list[Tuple[pn.pane.HTML, pn.widgets.Select | pn.Column]]:
    random.seed(seed)

    # Combine widgets into pairs
    widget_pairs = list(zip(desc_widgets, dropdowns))

    random.shuffle(widget_pairs)
    return widget_pairs
