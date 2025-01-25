import pandas as pd
from build.passwords import password, jupyterhub_user, user
import requests
from requests.auth import HTTPBasicAuth


def format_assignment_table(assignments):
    # Create DataFrame
    df = pd.DataFrame(assignments)

    # Replacements for normalization
    replacements = {
        "practicequiz": "practice quiz",
        "practice-quiz": "practice quiz",
        "attend": "attendance",
        "attendance": "attendance",
    }

    # Remove assignments of type 'test'
    remove_assignments = ["test"]

    # Apply replacements
    df["assignment_name"] = df["assignment_type"].replace(replacements)

    # Filter out specific assignment types
    df = df[~df["assignment_type"].isin(remove_assignments)]

    # Sort by week number and assignment name
    df = df.sort_values(by=["assignment_name", "week_number"]).reset_index(drop=True)

    return df

def get_student_grades(
    student_username, api_base_url="https://engr-131-api.eastus.cloudapp.azure.com/"
):
    params = {"username": student_username}
    res = requests.get(
        url=api_base_url.rstrip("/") + "/student-grades-testing",
        params=params,
        auth=HTTPBasicAuth(user(), password()),
    )

    [assignments, sub] = res.json()
    
    return pd.DataFrame(assignments), pd.DataFrame(sub)

def filter_assignments(df, max_week=None, exclude_types=None):
    """
    Remove assignments with week_number greater than max_week
    or with specific assignment types.

    :param df: DataFrame containing assignments.
    :param max_week: Maximum allowed week_number (int).
    :param exclude_types: A single assignment type or a list of assignment types to exclude.
    :return: Filtered DataFrame.
    """
    if max_week is not None:
        df = df[df["week_number"] <= max_week]

    if exclude_types is not None:
        # Ensure exclude_types is a list
        if not isinstance(exclude_types, (list, tuple, set)):
            exclude_types = [exclude_types]
        df = df[~df["assignment_type"].isin(exclude_types)]

    return df


# import os
# import numpy as np
# import pandas as pd
# import socket
# import requests
# from IPython.core.interactiveshell import ExecutionInfo
# from requests import Response
# from requests.auth import HTTPBasicAuth
# from requests.exceptions import RequestException
# from pykubegrader.graders.late_assignments import calculate_late_submission


# api_base_url = os.getenv("DB_URL")
# student_user = "admin" # os.getenv("user_name_student")
# student_pw = "TrgpUuadm2PWtdgtC7Yt" # os.getenv("keys_student")

# from_hostname = socket.gethostname().removeprefix("jupyter-")
# from_env = os.getenv("JUPYTERHUB_USER")
# params = {"username": from_env}

# letteronly = lambda s: re.sub(r'[^a-zA-Z]', '', s)
# start_date='2025-01-06'

# # get assignment information
# res = requests.get(
#     url=api_base_url.rstrip("/") + "/assignments",
#     auth=HTTPBasicAuth(student_user, student_pw),)
# res.raise_for_status()
# assignments = res.json()

# # get submission information
# res = requests.get(
#     url=api_base_url.rstrip("/") + "/testing/get-all-assignment-subs",
#     auth=HTTPBasicAuth('testing', 'Vok8WzmuCMVYULw3tqzJ'),
# )
# subs = res.json()
# student_subs = [sub for sub in subs if sub['student_email']==from_env]

# # set up new df format
# weights = {'homework':0.15, 'lab':0.15, 'lecture':0.15, 'quiz':0.15, 'readings':0.15,
#         # 'midterm':0.15, 'final':0.2
#         'labattendance':0.05,  'practicequiz':0.05, }
# assignment_types = list(set([a['assignment_type'] for a in assignments]))+['Running Avg']
# inds = [f'week{i+1}' for i in range(11)]+['Running Avg']
# restruct_grades = {k: np.zeros(len(inds)) for k in assignment_types}
# restruct_grades['inds']=inds
# new_weekly_grades = pd.DataFrame(restruct_grades)

# for assignment in assignments:
#     # get the assignment from all submissions
#     subs = [ sub for sub in student_subs if \
#             letteronly(sub['assignment_type'])==letteronly(assignment['assignment_type']) and \
#             sub['week_number']==assignment['week_number'] ]
#     if len(subs)==0: continue
#     if len(subs)>1:

#     # get due date from assignment
#     due_date = datetime.datetime.strptime(assignment['due_date'], "%Y-%m-%d %H:%M:%S")
#     for sub in subs:
#         entry_date = datetime.strptime(sub['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
#         if entry_date <= due_date:
#         else after_due).append(entry)
#         calculate_late_submission(due = due_date, # '2025-01-21T18:59:59Z'.
#                             submitted = subs"%Y-%m-%d %H:%M:%S".
#     - Q0 (float): Initial value (default is 100).
#     - Q_min (float): Minimum value (default is 40).
#     - k (float): Decay constant per minute (default is 6.88e-5).

#     # get max from before due date

#     # get max score from after due date and calculate
#     print(sub['assignment'])
#     print(subs)
# return
# # fill out grades
# new_weekly_grades.set_index('inds',inplace=True)
# splitted = [col_name.split('-')+[grades[col_name][0]] for col_name in grades.columns]
# for week,assignment,grade in splitted: new_weekly_grades.loc[week,assignment] = grade

# # Calculate the current week (1-based indexing)
# start_date = datetime.strptime(start_date, "%Y-%m-%d")
# today = datetime.now()
# days_since_start = (today - start_date).days
# current_week = days_since_start // 7 + 1

# # Get average until current week
# new_weekly_grades.iloc[-1] = new_weekly_grades.iloc[:current_week-1].mean()

# # make new dataframe with the midterm, final, and running average
# max_key_length = max(len(k) for k in weights.keys())
# total = 0
# for k, v in weights.items():
#     grade = new_weekly_grades.get(k, pd.Series([0])).iloc[-1]
#     total+=grade*v
#     print(f'{k:<{max_key_length}}:\t {grade:.2f}')
# print(f'\nTotal: {total}') # exclude midterm and final

# return new_out
