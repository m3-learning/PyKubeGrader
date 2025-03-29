from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple, Union

from pykubegrader.grade_reports.assignments import AssignmentType


@dataclass
class GradeConfig:
    """
    Configuration class to represent grading scheme and student management.

    Attributes:
        assignment_types (List[AssignmentType]): List of assignment categories.
        global_extensions_AVL (Dict[str, int]): Global extensions available (minutes) keyed by student ID.
        custom_grade_adjustments (Dict[Tuple[str, int], Callable[[float], float]]): Custom grade adjustments per assignment type and week.
        globally_exempted_assignments (List[Tuple[str, int]]): List of globally exempted assignments by type and week.
        aliases (Dict[str, List[str]]): Alternative names for assignment types.
        skipped_assignments (Dict[Tuple[str, int], Any]): Assignments explicitly skipped.
        dropped_assignments (List[str]): List of assignment types where the lowest score is dropped.
        duplicated_scores (List[List[Tuple[int, str]]]): Scores that should be duplicated from one assignment to another.
        skipped_users (List[str]): Users to exclude from reports (e.g., teaching assistants).
        optional_drop_week (List[int]): Weeks eligible for dropping the lowest score.
        optional_drop_assignments (List[Tuple[str, int]]): Assignments eligible for dropping the lowest score.
        exclude_from_running_avg (List[str]): Assignments excluded from running average calculations.
        max_week (int): Maximum number of weeks in the grading period.
        students_to_include (List[str]): List of student IDs to include in the report.
        grade_ranges (List[Tuple[int, int, str]]): Grade thresholds defining letter grades.
    """

    assignment_types: List[AssignmentType]
    global_extensions_AVL: Dict[str, int]
    custom_grade_adjustments: Dict[Tuple[str, int], Callable[[float], float]]
    globally_exempted_assignments: List[Tuple[str, int]]
    aliases: Dict[str, List[str]]
    skipped_assignments: Dict[Tuple[str, int], Any]
    dropped_assignments: List[str]
    duplicated_scores: List[List[Tuple[int, str]]]
    skipped_users: List[str]
    optional_drop_week: List[int]
    optional_drop_assignments: List[Tuple[str, int]]
    exclude_from_running_avg: List[str]
    max_week: int
    students_to_include: List[str]
    grade_ranges: List[Tuple[int, int, str]]


# Example usage
grade_config = GradeConfig(
    assignment_types=[
        AssignmentType("quiz", True, 0.15),
        AssignmentType("final", False, (0.2, 0.4)),
    ],
    global_extensions_AVL={"student123": 2880},  # 48 hours
    custom_grade_adjustments={
        ("quiz", 7): lambda score: min(score / 28 * 100, 100.0),
    },
    globally_exempted_assignments=[("quiz", 6)],
    aliases={"quiz": ["quiz", "test"]},
    skipped_assignments={},
    dropped_assignments=["quiz"],
    duplicated_scores=[[(7, "lab"), (7, "homework")]],
    skipped_users=["TA1", "TA2"],
    optional_drop_week=[1],
    optional_drop_assignments=[("homework", 7)],
    exclude_from_running_avg=["final"],
    max_week=10,
    students_to_include=["student123", "student456"],
    grade_ranges=[(90, 100, "A"), (80, 90, "B"), (0, 80, "F")],
)

# from typing import Any

# from pykubegrader.grade_reports.assignments import assignment_type

# # Assignment types, weekly, and weight
# # Total of 1st values in tuple should add up to 1.0
# assignment_type_list = [
#     assignment_type("readings", True, 0.15),
#     assignment_type("lecture", True, 0.15),
#     assignment_type("practicequiz", True, 0.015),
#     assignment_type("quiz", True, 0.15),
#     assignment_type("homework", True, 0.15),
#     assignment_type("lab", True, 0.15),
#     assignment_type("labattendance", True, 0.05),
#     assignment_type("practicemidterm", False, 0.015),
#     assignment_type("midterm", False, 0.15),
#     assignment_type("practicefinal", False, 0.02),
#     assignment_type("final", False, (0.2, 0.4)),
# ]

# global_extensions_AVL = {"ld895": 48*60, "te348": 48*60}

# # Custom grade adjustments, key is a tuple of assignment type and week, value is a lambda function that takes the score and returns the adjusted score
# custom_grade_adjustments = {
#     ("lecture", 3): lambda score: 100.0 if score > 0 else 0.0,
#     ("lecture", 4): lambda score: 100.0 if score > 0 else 0.0,
#     ("lecture", 5): lambda score: 100.0 if score > 0 else 0.0,
#     ("lecture", 7): lambda score: 100.0,
#     ("lecture", 9): lambda score: 100.0 if score > 0 else 0.0,
#     ("quiz", 7): lambda score: min(score / 28 * 100, 100.0),
#     ("labattendance", 2): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 1): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 3): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 4): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 5): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 6): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 7): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 8): lambda score: 100.0 if score > 0 else 0.0,
#     ("labattendance", 9): lambda score: 100.0 if score > 0 else 0.0,
#     ("practicequiz", 9): lambda score: min(score / 20 * 100, 100.0),
# }

# # Exempted assignments, key is a tuple of assignment type and week
# globally_exempted_assignments = [
#     ("labattendance", 1),
#     ("readings", 6),
#     ("quiz", 6),
#     ("practicequiz", 6),
#     ("lecture", 6),
#     ("homework", 5),
#     ("lab", 5),
#     ("labattendance", 5),
#     ("homework", 10),
#     ("lab", 10),
#     ("quiz", 9),
#     ("quiz", 10),
#     ("practicequiz", 10),
#     ("readings", 10),
# ]

# # Common Assignment Aliases, these are other names used for the same assignment category
# aliases = {
#     "practicequiz": [
#         "practice quiz",
#         "practice-quiz",
#         "practice quiz",
#         "practice_quiz",
#         "practicequiz",
#     ],
#     "final": ["finalexam"],
#     "labattendance": ["labattendance", "attendance", "attend"],
# }

# # Skipped assignments, key is a tuple of assignment type and week
# skipped_assignments: dict[tuple, Any] = {}

# # Dropped assignments a list of assignments which lowest score will be dropped
# dropped_assignments = [
#     "readings",
#     "lecture",
#     "practicequiz",
#     "quiz",
#     "homework",
#     "lab",
#     "labattendance",
# ]

# # Duplicated scores, a list of tuples of assignment types and weeks where the scores will be duplicated
# duplicated_scores = [[(7, "lab"), (7, "homework")], [(9, "lab"), (9, "homework")]]

# # TAs and other users to skip in class grade report
# skipped_users = [
#     "JCA",
#     "jca92",
#     "cnp68",
#     "dak329",
#     "xz498",
#     "ag4328",
#     "rg897",
#     "jce63",
#     "qt49",
# ]

# # Optional drop week, a list of weeks where the lowest score will be dropped
# optional_drop_week = [1]

# # Optional drop assignments, a list of tuples of assignment types and weeks where the lowest score will be dropped
# optional_drop_assignments = [("lab", 7), ("homework", 7)]

# # Excluded from running average, a list of assignment types that will be excluded from the running average calculation, These assignments are not included as exempt when the due date is in the future
# exclude_from_running_avg = ["final", "practicefinal"]

# max_week = 10

# students_to_include = [
#     "ka3232",
#     "ta669",
#     "va438",
#     "fa577",
#     "aa4925",
#     "mka75",
#     "naa325",
#     "bca48",
#     "ma4253",
#     "jcb428",
#     "thb37",
#     "rsb328",
#     "ab4947",
#     "ceb427",
#     "abb97",
#     "jeb499",
#     "sb4677",
#     "rtb79",
#     "bb3379",
#     "bab454",
#     "cab589",
#     "kmb669",
#     "ctb84",
#     "jeb522",
#     "kmb673",
#     "jab864",
#     "mhc77",
#     "vc466",
#     "jic42",
#     "tac347",
#     "gmc344",
#     "dcc342",
#     "mc4553",
#     "mc4545",
#     "gc828",
#     "mc4558",
#     "ac4632",
#     "jsc382",
#     "abc363",
#     "vtc29",
#     "jc4764",
#     "kc3822",
#     "mcc435",
#     "ac4626",
#     "bc987",
#     "nc937",
#     "klc465",
#     "nac369",
#     "ejc346",
#     "ic428",
#     "rjc395",
#     "ld895",
#     "md3922",
#     "ged46",
#     "cmd556",
#     "dd3399",
#     "md3894",
#     "pd584",
#     "vad45",
#     "jxd25",
#     "jd3853",
#     "jrd389",
#     "te348",
#     "ate33",
#     "ce527",
#     "ne358",
#     "ye42",
#     "kef324",
#     "rf533",
#     "dbf45",
#     "zsf27",
#     "kf555",
#     "mf3347",
#     "cf926",
#     "bf488",
#     "lmf359",
#     "tag332",
#     "ag4429",
#     "ksg62",
#     "jlg498",
#     "hg486",
#     "hag43",
#     "bjg89",
#     "dtg48",
#     "ogg26",
#     "ag4433",
#     "jsg375",
#     "ag4384",
#     "mg3893",
#     "idg26",
#     "avg64",
#     "ech78",
#     "jwh93",
#     "uh37",
#     "mh3879",
#     "ghh35",
#     "cth62",
#     "wh433",
#     "msh345",
#     "hjh52",
#     "jph355",
#     "jjh386",
#     "ch3489",
#     "jwh94",
#     "jh4293",
#     "bh875",
#     "pdh49",
#     "ash337",
#     "sh3723",
#     "jh4357",
#     "mmh427",
#     "kh3446",
#     "jh4334",
#     "aki36",
#     "vj329",
#     "tj563",
#     "mnk55",
#     "svk42",
#     "mek446",
#     "ck996",
#     "kk3584",
#     "lbk47",
#     "amk557",
#     "erk72",
#     "jrk376",
#     "hk867",
#     "jsk336",
#     "pk676",
#     "cmk443",
#     "mnk57",
#     "lk694",
#     "hk862",
#     "vnk24",
#     "tjk356",
#     "el886",
#     "nl582",
#     "sl3923",
#     "sl3896",
#     "cml497",
#     "ctl56",
#     "mll344",
#     "msl343",
#     "rl877",
#     "ql95",
#     "rl889",
#     "bcl68",
#     "jjl432",
#     "yl3438",
#     "gl538",
#     "bjl93",
#     "nl572",
#     "gpm62",
#     "am5493",
#     "tsm322",
#     "sam688",
#     "vmm86",
#     "jjm577",
#     "am5463",
#     "am5485",
#     "nem87",
#     "dm3735",
#     "dgm49",
#     "rlm349",
#     "bm3358",
#     "mjm856",
#     "wom23",
#     "rm3698",
#     "dm3745",
#     "apm326",
#     "asm488",
#     "fm496",
#     "lnm77",
#     "am5456",
#     "jm5354",
#     "mem579",
#     "cam664",
#     "mm5767",
#     "evm45",
#     "nam385",
#     "in67",
#     "can96",
#     "jn898",
#     "mdn58",
#     "tn495",
#     "nan74",
#     "jn899",
#     "aen58",
#     "aeo52",
#     "kmo89",
#     "sbo34",
#     "to398",
#     "olo25",
#     "alo54",
#     "cjp359",
#     "msp364",
#     "bjp83",
#     "nrp76",
#     "akp99",
#     "dpp52",
#     "kkp59",
#     "mmp388",
#     "pkp44",
#     "smp497",
#     "tp858",
#     "sp3937",
#     "lap387",
#     "sp3899",
#     "ap3994",
#     "sp3898",
#     "ahp75",
#     "mp3798",
#     "map538",
#     "aeq29",
#     "sr3747",
#     "jlr478",
#     "lbr42",
#     "dr3282",
#     "ar3985",
#     "zr75",
#     "vjr35",
#     "car448",
#     "ar3949",
#     "tdr56",
#     "jdr345",
#     "akr85",
#     "er695",
#     "arr362",
#     "apr73",
#     "mlr432",
#     "nar335",
#     "dr3276",
#     "dtr47",
#     "ms5738",
#     "js5543",
#     "js5546",
#     "cws57",
#     "gcs68",
#     "oms45",
#     "ts3586",
#     "ts3632",
#     "cs3899",
#     "ys832",
#     "hss55",
#     "ws475",
#     "cps323",
#     "ks4365",
#     "als594",
#     "bas457",
#     "ts3593",
#     "as5978",
#     "djs522",
#     "js5495",
#     "sjs495",
#     "nss328",
#     "ks4293",
#     "cks58",
#     "rps72",
#     "jns338",
#     "ns3586",
#     "pas379",
#     "mns89",
#     "aas466",
#     "js5247",
#     "as5973",
#     "ars583",
#     "gks48",
#     "dat85",
#     "bmt73",
#     "bt628",
#     "at3638",
#     "lt633",
#     "nt652",
#     "att72",
#     "dtt48",
#     "trt59",
#     "su98",
#     "mau43",
#     "au76",
#     "ku55",
#     "jsv36",
#     "mv638",
#     "aev54",
#     "tav44",
#     "knv38",
#     "sw3543",
#     "crw355",
#     "ow57",
#     "snw67",
#     "maw523",
#     "gjw53",
#     "iw329",
#     "jw3933",
#     "krw94",
#     "ex33",
#     "jy634",
#     "hy448",
#     "jy623",
#     "hy439",
#     "saz53",
#     "az627",
#     "hz463",
#     "ckz27",
#     "jz898",
#     "nz357",
#     "yz922",
#     "az643",
#     "rz365",
# ]

# grade_ranges = [
#     (97, 150, "A+"),
#     (93, 97, "A"),
#     (90, 93, "A-"),
#     (87, 90, "B+"),
#     (83, 87, "B"),
#     (80, 83, "B-"),
#     (77, 80, "C+"),
#     (73, 77, "C"),
#     (70, 73, "C-"),
#     (65, 70, "D+"),
#     (60, 65, "D"),
#     (0, 60, "F"),
# ]
