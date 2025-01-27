import os
import random
from typing import Any, Optional

import panel as pn

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")


def list_of_lists(options: list[Any]) -> bool:
    return all(isinstance(elem, list) for elem in options)


def shuffle_options(options: list[Any], seed: int) -> None:
    """
    Shuffle options in list[Optional[str]] or list[list[Optional[str]]].
    Shuffling is done in place.
    We annotate options as list[Any] just to keep Mypy happy.

    Args:
        options (list[Any]): List of options to shuffle
        seed (int): Seed for RNG

    Returns:
        None
    """
    random.seed(seed)

    if list_of_lists(options):
        for i in range(len(options)):
            inner_list: list[Optional[str]] = options[i]
            random.shuffle(inner_list)
    else:
        random.shuffle(options)


def shuffle_questions(
    desc_widgets: list[pn.pane.HTML],
    dropdowns: list[pn.widgets.Select] | list[pn.Column],
    seed: int,
) -> list[tuple[pn.pane.HTML, pn.widgets.Select | pn.Column]]:
    random.seed(seed)

    # Combine widgets into pairs
    widget_pairs = list(zip(desc_widgets, dropdowns))

    random.shuffle(widget_pairs)
    return widget_pairs
