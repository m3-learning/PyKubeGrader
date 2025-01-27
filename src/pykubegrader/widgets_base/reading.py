import copy
from typing import Optional

import panel as pn

from ..telemetry import ensure_responses, score_question, update_responses
from ..utils import shuffle_options


class ReadingPython:
    def __init__(
        self,
        title: str,
        question_number: int,
        options: dict,
    ) -> None:
        # Load responses from JSON (or create file if it doesn't exist)
        responses = ensure_responses()

        self.question_number = question_number

        default = None

        # Dynamically assign attributes based on keys, with default values from responses
        for num in range(len(options["lines_to_comment"]) + options["n_rows"]):
            key = f"q{question_number}_{num + 1}"

            # Dynamically assign the value from the responses file for persistence
            if num < len(options["lines_to_comment"]):
                setattr(self, key, responses.get(key, default))
            else:
                setattr(
                    self,
                    key,
                    responses.get(key, [default] * (len(options["table_headers"]) - 1)),
                )

        # Checks that a seed was assigned to responses
        try:
            seed: int = responses["seed"]
        except ValueError:
            raise ValueError(
                "You must submit your student info before starting the exam"
            )

        #
        # Question title
        #

        question_title = pn.pane.HTML(f"<h2>Question {question_number}: {title}</h2>")

        #
        # Comment dropdowns
        #

        shuffle_options(options["comments_options"], seed)

        self.dropdowns_for_comments: dict[str, pn.widgets.Select] = {
            line: pn.widgets.Select(
                options=options["comments_options"],
                name=f"Line {line}:",
                value=getattr(self, f"q{question_number}_{i_comments + 1}"),
                width=600,
            )
            for i_comments, line in enumerate(options["lines_to_comment"])
        }

        comment_dropdowns = pn.Column(*self.dropdowns_for_comments.values())

        #
        # Execution dropdowns
        #

        # Instructions
        execution_instructions = pn.pane.HTML(
            "<h3>For each step, select the appropriate response:</h3>"
        )

        # Header row
        header_row = pn.Row(
            *[
                pn.pane.HTML(f"<strong>{header}</strong>", width=150)
                for header in options["table_headers"]
            ]
        )

        # Make a deep copy of the lines to comment and add a null value to the beginning
        # This is to provide the null response to the question
        line_comment: list[int | str] = copy.deepcopy(options["lines_to_comment"])
        line_comment.insert(0, "")

        dropdown_options = [
            line_comment,
            options["variables_changed"],
            options["current_values"],
            options["datatypes"],
        ]

        # Function to create a row with dropdowns
        def create_row(step: int) -> pn.Row:
            widgets_list = [
                pn.pane.HTML(f"Step {step + 1}", width=150)
                if i == 0
                else pn.widgets.Select(
                    options=dropdown_options[i - 1],
                    value=getattr(
                        self,
                        f"q{question_number}_{len(options['lines_to_comment']) + step + 1}",
                    )[i - 1],
                    width=150,
                )
                for i in range(len(options["table_headers"]))
            ]

            return pn.Row(*widgets_list)

        # Generate rows dynamically based on n_rows
        self.rows = [create_row(step) for step in range(options["n_rows"])]

        # Combine header and rows
        execution_steps = pn.Column(header_row, *self.rows)

        # Submit button
        self.submit_button = pn.widgets.Button(name="Submit")
        self.submit_button.on_click(self.submit)

        # Combine everything into a single layout
        self.layout = pn.Column(
            question_title,
            comment_dropdowns,
            execution_instructions,
            execution_steps,
            self.submit_button,
        )

    def submit(self, _) -> None:
        # Get section 1 responses
        self.output_comments: list[str] = []
        for out in self.dropdowns_for_comments.values():
            self.output_comments.append(out.value if isinstance(out.value, str) else "")

        # Get section 2 responses
        self.output_execution: list[list[Optional[str | int]]] = []

        for row in self.rows[:]:
            row_value: list[Optional[str | int]] = []

            for box in row.objects:
                if isinstance(box, pn.widgets.Select):
                    row_value.append(box.value)

            if not any(row_value):
                continue

            self.output_execution.append(row_value)

        # Persist responses to JSON
        i = 0
        for comment_val in self.output_comments:
            i += 1
            update_responses(f"q{self.question_number}_{i}", comment_val)

        for exec_val in self.output_execution:
            i += 1
            update_responses(f"q{self.question_number}_{i}", exec_val)

        score_question()  # Debugging; update later

        print("Responses recorded successfully")

    def show(self):
        return self.layout
