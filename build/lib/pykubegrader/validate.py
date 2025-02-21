import base64
import json
import os
import re
import sys
from datetime import datetime

import nacl.public
import numpy as np
import requests
from requests.auth import HTTPBasicAuth

#
# Primary function
#


def validate_logfile(
    filepath: str,
    assignment_id: str,
    question_max_scores: dict[int, int],
    free_response_questions: int = 0,
    username: str = "student",
    password: str = "capture",
    base_url: str = "https://engr-131-api.eastus.cloudapp.azure.com",
    key_box=None,
) -> None:
    login_data = {
        "username": username,
        "password": password,
    }

    if key_box is None:
        # Generate box from private and public keys
        key_box = generate_keys()

    decrypted_log, log_reduced = read_logfile(filepath, key_box)

    # For debugging; to be commented out
    # with open(".output_reduced.log", "w") as f:
    #     f.writelines(f"{item}\n" for item in log_reduced)

    # Initialize question scores based on max scores
    question_scores = {key: 0 for key in question_max_scores}

    # Iterate over log to find the last entries for student info fields
    # This gets the student name etc.
    last_entries: dict[str, str | float] = {}
    for entry in log_reduced:
        # Split on commas and strip whitespace
        parts = [part.strip() for part in entry.split(",")]

        # This just overwrites, so the last iteration sticks
        if parts[0] == "info" and len(parts) == 4:
            field_name = parts[1]
            field_value = parts[2]
            last_entries[field_name] = field_value

    # For debugging; to be commented out
    # print(f"Keys in last_entries dict: {last_entries.keys()}")

    # Check if the assignment id is in the log file
    if "assignment" not in last_entries or assignment_id != last_entries["assignment"]:
        sys.exit(
            "Your log file is not for the correct assignment. Please submit the correct log file."
        )

    # TODO: Revisit this; we may no longer require as much info
    required_student_info = ["drexel_id", "first_name", "last_name", "drexel_email"]
    for field in required_student_info:
        if last_entries.get(field) is None:
            sys.exit("Missing required student information")

    # Initialize code and data lists
    log_execution: list[str] = []
    log_data: list[str] = []

    # Splitting the data into code and responses
    for entry in decrypted_log:
        # Splitting the data into code and responses
        if "code run:" in entry:
            log_execution.append(entry)
        else:
            log_data.append(entry)

    # Extracting timestamps and converting them to datetime objects
    # TODO: Check why we're using log_reduced instead of decrypted_log
    timestamps = [
        datetime.strptime(row.split(",")[-1].strip(), "%Y-%m-%d %H:%M:%S")
        for row in log_reduced
    ]

    # Getting the earliest and latest times
    last_entries["start_time"] = min(timestamps).strftime("%Y-%m-%d %H:%M:%S")
    last_entries["end_time"] = max(timestamps).strftime("%Y-%m-%d %H:%M:%S")
    delta = max(timestamps) - min(timestamps)
    minutes_rounded = round(delta.total_seconds() / 60, 2)
    last_entries["elapsed_minutes"] = minutes_rounded

    # Collect student info dict
    student_info = {key.upper(): value for key, value in last_entries.items()}

    # Write info dict to info.json
    # TODO: Try/except block here?
    with open("info.json", "w") as file:
        # print("Writing to info.json")
        json.dump(student_info, file)

    # Modified list comprehension to filter as per the criteria
    free_response = [
        entry
        for entry in log_reduced
        if entry.startswith("q")
        and entry.split("_")[0][1:].isdigit()
        and int(entry.split("_")[0][1:]) > free_response_questions
    ]

    # Initialize a dictionary to hold question entries.
    q_entries = []

    # Iterate over the number of free response questions.
    for i in range(1, free_response_questions + 1):
        # Collect entries for each question in a list.
        entries = [
            entry
            for j in range(1, get_entries_len(log_data, i))
            if (entry := get_last_entry(log_data, f"q{i}_{j}")) != ""
        ]

        # Store the list of entries in the dictionary, keyed by question number.
        q_entries += entries

    q_entries += free_response

    # Parse the data
    parsed_data: list[list[str]] = [
        [part.strip() for part in line.split(",")] for line in q_entries
    ]

    unique_question_IDs = set(row[0] for row in parsed_data)

    # Initialize a dictionary to hold the maximum score for each unique value
    max_scores = {unique_value: 0 for unique_value in unique_question_IDs}

    # Loop through each row in the data
    for score_entry in parsed_data:
        unique_value = score_entry[0]
        score = int(score_entry[1])
        # possible_score = float(row[3])
        # Update the score if it's higher than the current maximum
        if score > max_scores[unique_value]:
            max_scores[unique_value] = score

    # Loop through the max_scores dictionary and sum scores for each question
    for unique_value, score in max_scores.items():
        # Extract question number (assuming it's the number immediately after 'q')
        question_number = int(unique_value.split("_")[0][1:])
        question_scores[question_number] += score

    # Sorting the dictionary by keys
    question_max_scores = {
        key: int(np.round(question_max_scores[key]))
        for key in sorted(question_max_scores)
    }

    # Sorting the dictionary by keys
    question_scores = {
        key: int(np.round(question_scores[key])) for key in sorted(question_scores)
    }

    # Creating the dictionary structure
    result_structure: dict[str, list[dict]] = {
        "tests": [],
    }

    # Adding entries for each question
    for question_number in question_scores.keys():
        question_entry = {
            "name": f"Question {question_number}",
            "score": question_scores[question_number],
            "max_score": question_max_scores[question_number],
            # "visibility": "visible",
            # "output": "",
        }
        result_structure["tests"].append(question_entry)

    # Write results dict to results.json
    with open("results.json", "w") as file:
        print("Writing to results.json")
        json.dump(result_structure, file, indent=4)

    login_url = f"{base_url}/login"
    verify_login(login_data, login_url)

    # The file to be uploaded. Ensure the path is correct.
    file_path = "results.json"

    # Construct data payload as a dict
    final_data = {
        "assignment": assignment_id,
        "student_email": last_entries.get("drexel_email"),
        # "original_file_name": file_path,
        "start_time": last_entries["start_time"],
        "end_time": last_entries["end_time"],
        # "flag": last_entries["flag"],
        # "submission_mechanism": "jupyter_notebook",
        # "log_file": loginfo,
        "scores": result_structure["tests"],
    }

    # Files to be uploaded. The key should match the name expected by the server.
    _files = {
        "file": (file_path, open(file_path, "rb")),
    }

    post_url = f"{base_url}/upload-score"

    # Make the POST request with data and files
    response = requests.post(
        url=post_url,
        json=final_data,
        # files=files,
        auth=HTTPBasicAuth(login_data["username"], login_data["password"]),
    )

    # Print messages for the user
    submission_message(response)


def read_logfile(filepath: str, key_box=None) -> tuple[list[str], list[str]]:
    if key_box is None:
        key_box = generate_keys()

    with open(filepath, "r") as logfile:
        encrypted_lines = logfile.readlines()

    decrypted_log: list[str] = []
    for line in encrypted_lines:
        if "Encrypted Output: " in line:
            trimmed = line.split("Encrypted Output: ")[1].strip()
            decoded = base64.b64decode(trimmed)
            decrypted = key_box.decrypt(decoded).decode()
            decrypted_log.append(decrypted)

    # Decoding the log file
    # data_: list[str] = drexel_jupyter_logger.decode_log_file(self.filepath, key=key)
    # _loginfo = str(decrypted_log)

    # Where possible, we should work with this reduced list of relevant entries
    # Here we take only lines with student info or question scores
    log_reduced = [
        entry
        for entry in decrypted_log
        if re.match(r"info,", entry) or re.match(r"q\d+_\d+,", entry)
    ]

    return decrypted_log, log_reduced


#
# Helper functions
#


def generate_keys() -> nacl.public.Box:
    with open(".server_private_key.bin", "rb") as priv_file:
        server_private_key_bytes = priv_file.read()
    server_priv_key = nacl.public.PrivateKey(server_private_key_bytes)

    with open(".client_public_key.bin", "rb") as pub_file:
        client_public_key_bytes = pub_file.read()
    client_pub_key = nacl.public.PublicKey(client_public_key_bytes)

    box = nacl.public.Box(server_priv_key, client_pub_key)

    return box


def get_entries_len(data: list[str], question_number: int) -> int:
    """function to get the unique entries by length

    Args:
        data (list): list of all the data records
        question_number (int): question number to evaluate

    Returns:
        int: length of the unique entries
    """

    # Set for unique qN_* values
    unique_qN_values = set()

    for entry in data:
        if entry.startswith(f"q{question_number}_"):
            # Split the string by commas and get the value part
            parts = [part.strip() for part in entry.split(",")]
            # The value is the third element after splitting (?)
            value = parts[0].split("_")[1]
            unique_qN_values.add(value)

    return len(unique_qN_values) + 1


def get_last_entry(data: list[str], field_name: str) -> str:
    for entry in data[::-1]:
        parts = [part.strip() for part in entry.split(",")]
        if parts[0] == field_name:
            return entry
    return ""


def submission_message(response: requests.Response) -> None:
    if response.status_code == 200:
        print("Data successfully uploaded to the server")
        print(response.text)
    else:
        print(f"Failed to upload data. Status code: {response.status_code}")
        print(response.text)
        print(
            "There is something wrong with your log file or your submission. Please contact an instructor for help."
        )

    if os.path.exists("results.json"):
        # os.remove("results.json")
        # Let's keep results.json for now, for debugging
        pass
    else:
        print("results.json was not present")


def verify_login(login_data: dict[str, str], login_url: str) -> None:
    login_response = requests.post(
        login_url, auth=HTTPBasicAuth(login_data["username"], login_data["password"])
    )

    if login_response.status_code == 200:
        print("Login successful")
    else:
        Exception("Login failed")
