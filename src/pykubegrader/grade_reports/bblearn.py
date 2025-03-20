import pandas as pd

def merge_bb_learn_data(bblearn_csv: str, grades_csv: str,
                        out_csv: str = 'merged_bblearn_grades.csv',
                        include_grades_columns: list[str] = ['Weighted Average Grade w Final']) -> pd.DataFrame:
    """
    Merges Blackboard Learn grade data with grades from another CSV/Excel file.

    Args:
        bblearn_csv (str): Path to the Blackboard Learn CSV/Excel file containing student data
        grades_csv (str): Path to the CSV/Excel file containing grades to merge
        out_csv (str, optional): Output path for merged CSV file. Defaults to 'merged_bblearn_grades.csv'
        include_grades_columns (list[str], optional): List of grade columns to include from grades_csv. 
            Defaults to ['Weighted Average Grade w Final']

    Returns:
        pd.DataFrame: DataFrame containing the merged data from both input files

    Raises:
        Exception: If either input file cannot be read as CSV or Excel
    """
    try:
        bblearn_df = pd.read_csv(bblearn_csv)
    except:
        try:
            bblearn_df = pd.read_excel(bblearn_csv)
        except Exception as e:
            raise Exception(f"Could not read {bblearn_csv}: {str(e)}")
            
    try:
        grades_df = pd.read_csv(grades_csv)
    except:
        try:
            grades_df = pd.read_excel(grades_csv)
        except Exception as e:
            raise Exception(f"Could not read {grades_csv}: {str(e)}")

    # Rename first column of grades_df to match bblearn_df's 'Username' column
    grades_df.rename(columns={grades_df.columns[0]: 'Username'}, inplace=True)
    
    # Merge on 'Username' instead of 'student_id'
    merged_df = pd.merge(bblearn_df, grades_df[['Username'] + include_grades_columns], on='Username', how='left')
    merged_df.to_csv(out_csv, index=False)
    return merged_df
