# Extend the Material Design with custom Drexel colors
drexel_colors = """
:root {
    --panel-primary-color: #07294D; /* Drexel Blue */
    --design-primary-color: #07294D; /* Drexel Blue */
    --design-primary-text-color: #FFFFFF; /* White text on primary */
    --design-secondary-color: #FFC600; /* Drexel Gold */
    --design-secondary-text-color: #07294D; /* Blue text on secondary */
    --design-background-color: #F8F8F8; /* Soft background */
    --design-background-text-color: #07294D; /* Blue text on background */
    --design-surface-color: #FFFFFF; /* White surface */
    --design-surface-text-color: #07294D; /* Blue text on surface */
}
:host {
    --design-primary-color: #07294D; /* Drexel Blue */
    --design-primary-text-color: #FFFFFF; /* White text on primary */
    --design-secondary-color: #FFC600; /* Drexel Gold */
    --design-secondary-text-color: #07294D; /* Blue text on secondary */
    --design-background-color: #F8F8F8; /* Soft background */
    --design-background-text-color: #07294D; /* Blue text on background */
    --design-surface-color: #FFFFFF; /* White surface */
    --design-surface-text-color: #07294D; /* Blue text on surface */}
"""

raw_css = """
/* Styling for the labels */
.bk-input-group label {
  color: #07294D !important; /* Drexel Blue label text color */
}

/* Styling for CheckBoxGroup and RadioBoxGroup inputs */
.bk-input-group input[type="radio"] {
  accent-color: #07294D !important; /* Drexel Blue accent for inputs */
}

input[type='checkbox']:checked {
    accent-color: #07294D !important;
}

input[type='checkbox'] {
    width: 16px;
    height: 16px;
    margin-right: 8px;
}
"""
