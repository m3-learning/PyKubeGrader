import time
from typing import Callable, Tuple

import panel as pn

from ..telemetry import ensure_responses, score_question, update_responses
from ..utils import shuffle_questions
from ..widgets.style import drexel_colors, raw_css

# Pass the custom CSS to Panel
pn.extension(design="material", global_css=[drexel_colors], raw_css=[raw_css])

# Add the custom CSS to Panel
pn.config.raw_css.append(raw_css)


class MultiSelectQuestion:
    def __init__(
        self,
        title: str,
        style: Callable[
            [list[str], list[list[str]], list[bool]],
            Tuple[list[pn.pane.HTML], list[pn.Column]],
        ],
        question_number: int,
        keys: list[str],
        options: list[list[str]],
        descriptions: list[str],
        points: int,
    ):
        responses = ensure_responses()

        self.points = points
        self.question_number = question_number
        self.style = style

        self.true_keys = keys  # Debugging; update later

        flat_index = 0
        self.keys: list[str] = []
        for i, _ in enumerate(keys):
            for _ in options[i]:
                flat_index += 1  # Start at 1
                self.keys.append(f"q{question_number}_{flat_index}")

        try:
            seed: int = responses["seed"]
        except ValueError:
            raise ValueError(
                "You must submit your student info before starting the exam"
            )

        # Dynamically assigning attributes based on keys, with default values from responses
        for key in self.keys:
            setattr(self, key, responses.get(key, False))

        self.initial_vals = [getattr(self, key) for key in self.keys]

        description_widgets, self.widgets = style(
            descriptions, options, self.initial_vals
        )

        self.submit_button = pn.widgets.Button(name="Submit", button_type="primary")
        self.submit_button.on_click(self.submit)

        widget_pairs = shuffle_questions(description_widgets, self.widgets, seed)

        # Panel layout
        question_header = pn.pane.HTML(
            f"<h2>Question {self.question_number}: {title}</h2>"
        )
        question_body = pn.Column(
            *[
                pn.Row(desc_widget, checkbox_set)
                for desc_widget, checkbox_set in widget_pairs
            ]
        )

        self.layout = pn.Column(question_header, question_body, self.submit_button)

    def submit(self, _) -> None:
        responses_flat: list[bool] = []
        self.responses_nested: list[list[bool]] = []
        self.names_nested: list[list[str]] = []  # Debugging; update later

        for row in self.widgets:
            next_selections: list[bool] = []
            next_names: list[str] = []  # Debugging; update later

            for widget in row.objects:
                # Skip HTML widgets
                if isinstance(widget, pn.pane.HTML):
                    continue

                if isinstance(widget, pn.widgets.Checkbox):
                    next_selections.append(widget.value)
                    if widget.value:
                        next_names.append(widget.name)  # Debugging; update later
                    responses_flat.append(widget.value)  # For flat list of responses

            # Append all responses for this widget at once, forming a list of lists
            self.responses_nested.append(next_selections)
            self.names_nested.append(next_names)  # Debugging; update later

        self.record_responses(responses_flat)

        score_question()  # Debugging; update later

    def record_responses(self, responses_flat: list[bool]) -> None:
        for key, value in zip(self.keys, responses_flat):
            update_responses(key, value)

        # Debugging; update later
        for k, v in zip(self.true_keys, self.names_nested):
            update_responses(k, v)

        self.submit_button.name = "Responses Submitted"
        time.sleep(1)
        self.submit_button.name = "Submit"

    def show(self):
        return self.layout
