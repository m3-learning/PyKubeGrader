import pandas as pd


def merge_bb_learn_data(
    bblearn_csv: str,
    grades_csv: str,
    out_csv: str = "merged_bblearn_grades.csv",
    include_grades_columns: list[str] = ["Weighted Average Grade w Final"],
) -> pd.DataFrame:
    try:
        bblearn_df = pd.read_csv(bblearn_csv)
    except:
        bblearn_df = pd.read_excel(bblearn_csv)
    try:
        grades_df = pd.read_csv(grades_csv)
    except:
        grades_df = pd.read_excel(grades_csv)

    # Rename first column of grades_df to match bblearn_df's 'Username' column
    grades_df.rename(columns={grades_df.columns[0]: "Username"}, inplace=True)

    # Merge on 'Username' instead of 'student_id'
    merged_df = pd.merge(
        bblearn_df,
        grades_df[["Username"] + include_grades_columns],
        on="Username",
        how="left",
    )
    merged_df.to_csv(out_csv, index=False)
    return merged_df
