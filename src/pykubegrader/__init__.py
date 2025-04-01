from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

try:
    dist_name = "PyKubeGrader"  # Change if project is renamed
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
from pykubegrader import build
from pykubegrader import graders
from pykubegrader import initialize
from pykubegrader import log_parser
from pykubegrader import telemetry
from pykubegrader import widgets
from pykubegrader import widgets_base

from pykubegrader.build import (FastAPINotebookBuilder, FolderCleaner,
                                MarkdownToNotebook, NotebookProcessor,
                                QuestionCollator, api_notebook_builder,
                                build_folder, check_for_heading, clean_folder,
                                clean_notebook, collate, ensure_imports,
                                extract_MCQ, extract_SELECT_MANY, extract_TF,
                                extract_config_from_notebook, extract_files,
                                extract_question, extract_raw_cells,
                                find_first_code_cell, generate_mcq_file,
                                generate_select_many_file, generate_tf_file,
                                jupyterhub_user, main, markdown_questions,
                                password, passwords, replace_cell_source,
                                replace_cells_between_markers, sanitize_string,
                                student_ids, update_initialize_assignment,
                                user,)
from pykubegrader.graders import (calculate_late_submission, late_assignments,)
from pykubegrader.initialize import (build_assignment_tag,
                                     check_api_connection, generate_user_seed,
                                     get_jhub_user, initialize_assignment,
                                     initialize_telemetry, move_dotfiles,
                                     print_api_response, print_assignment_info,
                                     username_to_seed,)
from pykubegrader.log_parser import (LogParser, LogParserResults, parse,)
from pykubegrader.telemetry import (ensure_responses, log_encrypted,
                                    log_variable, responses,
                                    set_responses_json,)
from pykubegrader.widgets import (EMAIL_PATTERN, KEYS, MCQ, MCQuestion,
                                  MultiSelect, MultipleChoice,
                                  ReadingPythonQuestion, SelectMany,
                                  StudentInfoForm, TFQuestion, TFStyle,
                                  TypesQuestion, drexel_colors,
                                  multiple_choice, process_questions_and_codes,
                                  question_processor, raw_css,
                                  reading_question, select_many, student_info,
                                  style, true_false, types_question,)
from pykubegrader.widgets_base import (MultiSelectQuestion, ReadingPython,
                                       SelectQuestion, multi_select, reading,
                                       select,)

__all__ = ['EMAIL_PATTERN', 'FastAPINotebookBuilder', 'FolderCleaner', 'KEYS',
           'LogParser', 'LogParserResults', 'MCQ', 'MCQuestion',
           'MarkdownToNotebook', 'MultiSelect', 'MultiSelectQuestion',
           'MultipleChoice', 'NotebookProcessor', 'QuestionCollator',
           'ReadingPython', 'ReadingPythonQuestion', 'SelectMany',
           'SelectQuestion', 'StudentInfoForm', 'TFQuestion', 'TFStyle',
           'TypesQuestion', 'api_notebook_builder', 'build',
           'build_assignment_tag', 'build_folder', 'calculate_late_submission',
           'check_api_connection', 'check_for_heading', 'clean_folder',
           'clean_notebook', 'collate', 'drexel_colors', 'ensure_imports',
           'ensure_responses', 'extract_MCQ', 'extract_SELECT_MANY',
           'extract_TF', 'extract_config_from_notebook', 'extract_files',
           'extract_question', 'extract_raw_cells', 'find_first_code_cell',
           'generate_mcq_file', 'generate_select_many_file',
           'generate_tf_file', 'generate_user_seed', 'get_jhub_user',
           'graders', 'initialize', 'initialize_assignment',
           'initialize_telemetry', 'jupyterhub_user', 'late_assignments',
           'log_encrypted', 'log_parser', 'log_variable', 'main',
           'markdown_questions', 'move_dotfiles', 'multi_select',
           'multiple_choice', 'parse', 'password', 'passwords',
           'print_api_response', 'print_assignment_info',
           'process_questions_and_codes', 'question_processor', 'raw_css',
           'reading', 'reading_question', 'replace_cell_source',
           'replace_cells_between_markers', 'responses', 'sanitize_string',
           'select', 'select_many', 'set_responses_json', 'student_ids',
           'student_info', 'style', 'telemetry', 'true_false',
           'types_question', 'update_initialize_assignment', 'user',
           'username_to_seed', 'widgets', 'widgets_base']
