import os
import re
import socket

import numpy as np
import panel as pn

from ..telemetry import ensure_responses, update_responses

#
# Constants
#

EMAIL_PATTERN = re.compile(r"[a-z]+\d+@drexel\.edu")

KEYS = [
    "first_name",
    "last_name",
    "drexel_id",
    "drexel_email",
    "hostname",
    "ip_address",
    "jupyter_user",
    "seed",
]

#
# Form class
#


class StudentInfoForm:
    def __init__(self, **kwargs) -> None:
        self.first_name = kwargs.get("first_name", "")
        self.last_name = kwargs.get("last_name", "")
        self.drexel_id = kwargs.get("drexel_id", "")
        self.drexel_email = kwargs.get("drexel_email", "")
        self.hostname = kwargs.get("hostname", "")
        self.ip_address = kwargs.get("ip_address", "")
        self.jupyter_user = kwargs.get("jupyter_user", "")
        self.seed = kwargs.get("seed", np.random.randint(0, 100))

        self.first_name_widget = pn.widgets.TextInput(
            name="First Name", value=self.first_name
        )
        self.last_name_widget = pn.widgets.TextInput(
            name="Last Name", value=self.last_name
        )
        self.drexel_id_widget = pn.widgets.TextInput(
            name="Drexel ID", value=self.drexel_id
        )
        self.drexel_email_widget = pn.widgets.TextInput(
            name="Drexel Email", value=self.drexel_email
        )

        self.submit_button = pn.widgets.Button(
            name="Submit", button_type="primary", styles=dict(margin_top="1.5em")
        )
        self.submit_button.on_click(self.submit)

        self.message = pn.pane.Str("")  # Placeholder for status message

        self.layout = pn.Column(
            "# Student Information Form",
            self.first_name_widget,
            self.last_name_widget,
            self.drexel_id_widget,
            self.drexel_email_widget,
            self.submit_button,
            self.message,
        )

    def submit(self, _) -> None:
        info = ensure_responses()

        info["first_name"] = self.first_name_widget.value.strip()
        info["last_name"] = self.last_name_widget.value.strip()
        info["drexel_id"] = self.drexel_id_widget.value.strip()
        info["drexel_email"] = self.drexel_email_widget.value.strip()

        info["hostname"] = socket.gethostname()
        info["jupyter_user"] = os.environ.get("JUPYTERHUB_USER", "Not on JupyterHub")

        if "seed" not in info:
            info["seed"] = np.random.randint(0, 100)

        try:
            info["ip_address"] = socket.gethostbyname(info["hostname"])
        except socket.gaierror:
            info["ip_address"] = "IP unavailable"

        try:
            for key in KEYS:
                if info[key] == "":
                    raise ValueError(f"Missing form input: {key}")

            if not EMAIL_PATTERN.fullmatch(info["drexel_email"]):
                raise ValueError(f"Invalid email format: {info['drexel_email']}")

            email_prefix = info["drexel_email"].split("@")[0]
            if info["drexel_id"] != email_prefix:
                raise ValueError(
                    f"Drexel ID {info['drexel_id']} does not match email {info['drexel_email']}"
                )

            for key in KEYS:
                update_responses(key, info[key])

            self.message.object = "Student info recorded successfully!"
            self.message.style = {"color": "green"}
        except ValueError as e:
            self.message.object = str(e)
            self.message.style = {"color": "red"}

    def show(self):
        return self.layout
