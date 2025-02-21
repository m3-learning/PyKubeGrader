from ..widgets_base.reading import ReadingPython


class ReadingPythonQuestion(ReadingPython):
    def __init__(
        self,
        title="Reading, Commenting, and Interpreting Python Code",
        question_number=4,
        key="READING1",
        options={
            # General list of 15 potential comments with only one correct per line
            "comments_options": [
                None,
                "Initializes a list `numbers` with integers and floats",
                "Initializes the variable `total` with a value of 0",
                "A `for` loop that iterates through an iterator `numbers`",
                "`while` loop that continues to iterate until `total` is less than 9",
                "Adds and assigns the variable `total` with the value of `num` plus 1",
                "Statement that ends the `for` loop",
                "Initializes a dictionary `numbers` with integers and floats",
                "Initializes the class `total` with a value of 0",
                "A `for` loop that iterates through an iterator `num`",
                "`while` loop that continues to iterate until `total` is less than or equal to 9",
                "Adds the variable `total` with the value of `num` plus 1",
                "Statement that ends the `while` loop",
                "`while` loop that continues to iterate while `total` is less than 9",
                "Initializes a list `numbers` with integers and floats",
            ],
            "n_rows": 12,  # Number of lines to show
            "n_required": 8,  # Number of rows required to respond
            # Lines of code that require commenting
            "lines_to_comment": [1, 2, 4, 5, 6, 7],
            # Table headers
            "table_headers": [
                "Step",
                "Line Number",
                "Variable Changed",
                "Current Value",
                "DataType",
            ],
            # Variables Changed
            "variables_changed": ["", "None", "numbers", "num", "total", "if", "else"],
            "current_values": [
                "",
                "None",
                "[5, 4.0]",
                "[5.0, 4.0]",
                "5.0",
                "6.0",
                "5",
                "6",
                "4.0",
                "4",
                "11.0",
                "11",
                "12",
                "12.0",
                "0",
                "0.0",
                "True",
                "False",
                "N/A",
            ],
            "datatypes": [
                "",
                "NoneType",
                "list",
                "dictionary",
                "tuple",
                "set",
                "string",
                "float",
                "integer",
                "boolean",
                "N/A",
            ],
        },
        points=[20, 25],
    ):
        super().__init__(
            title=title,
            question_number=question_number,
            options=options,
        )
