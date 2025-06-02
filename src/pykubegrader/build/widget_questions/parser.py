from dataclasses import dataclass, field


@dataclass
class WidgetQuestionParser:
    """
    A parser for widget questions in Jupyter notebooks.

    This class is responsible for parsing and extracting widget questions from Jupyter notebook cells.
    It tracks sections of widget questions marked by specific start and end tags, and maintains
    the state of the current section being processed.

    Attributes:
        sections (list): A list of dictionaries, each containing a section of widget questions.
        current_section (dict): The dictionary representing the section currently being processed.
        within_section (bool): Flag indicating whether the parser is currently within a question section.
        subquestion_number (int): Counter for tracking the current subquestion number.
        start_label (str): The tag that marks the beginning of a widget question section.
        end_label (str): The tag that marks the end of a widget question section.
    """

    sections: list = field(default_factory=list)
    current_section: dict = field(default_factory=dict)
    within_section: bool = False
    subquestion_number: int = 0
    start_label: str = "# BEGIN MULTIPLE CHOICE"
    end_label: str = "# END MULTIPLE CHOICE"

    def process_raw_cell(self, raw_content: str) -> bool:
        """
        Processes a raw cell from a Jupyter notebook to identify section markers.

        This method checks if the raw content contains the start or end label for a widget question section.
        If a start label is found, it initializes a new section. If an end label is found, it finalizes
        the current section and adds it to the list of sections.

        Args:
            raw_content (str): The content of the raw cell to process.

        Returns:
            bool: True if a start or end label was found and processed, False otherwise.
        """
        if self.start_label in raw_content:
            self.start_new_section()
            return True
        elif self.end_label in raw_content:
            self.end_current_section()
            return True
        return False

    def start_new_section(self) -> None:
        """
        Initializes a new section for widget questions.

        This method sets the within_section flag to True, resets the subquestion_number to 0,
        and initializes an empty dictionary for the current_section to store question data.

        Returns:
            None
        """
        self.within_section = True
        self.subquestion_number = 0
        self.current_section = {}

    def end_current_section(self) -> None:
        """
        Finalizes the current section of widget questions.

        This method sets the within_section flag to False, indicating that we are no longer
        within a widget question section. If the current_section contains any questions,
        it adds the current_section to the list of sections.

        Returns:
            None
        """
        self.within_section = False
        if self.current_section:
            self.sections.append(self.current_section)

    def increment_subquestion_number(self) -> None:
        """
        Increments the subquestion number.

        This method increases the subquestion_number by one, which is used to track
        the number of subquestions within the current widget question section.

        Returns:
            None
        """
        self.subquestion_number += 1