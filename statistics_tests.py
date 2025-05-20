import pandas as pd
import numpy as np
from scipy.stats import f_oneway, kruskal, shapiro, levene
from scikit_posthocs import posthoc_dunn, posthoc_tukey_hsd
import os, math, itertools
import math

# --- SECTION 2 - Statistical tests
###
# Chosen statistical tests are:
#     * Omnibus
#         * ANOVA (1-Way) for metrics for which ANOVA h. are verified
#         * Kruskal-Wallis for others
#     * Post-hocs
#         * (ANOVA) Turkey HSD and Cohen's d for effect size
#         * (Kruskal) Dunn test and Rank-biserial correlation for effect size
##

# --- helpers
def has_normal_distribution(data: list, alpha: float = 0.05) -> bool:
    """
    Given a set of groups of data, check if
    all those groups present a normal distribution
    using Shapiro's test.
    
    Arguments:
        data (list): the list of groups to test
        alpha (float): p_value threshold
        
    Returns:
        bool: True if all groups are normally distributed
    """
    shapiro_test = []
    for elem in data:
        statistic, p_value = shapiro(elem)
        shapiro_test.append(p_value > alpha)
    return all(shapiro_test)

def has_homogeneous_variance(data: list, alpha: float = 0.05) -> bool:
    """
    Given a set of groups of data, check if
    the variance between those group is homogeneous
    using Levene's test
    
    Arguments:
        data (list): the list of groups to test
        alpha (float): p_value threshold
        
    Returns:
        bool: True if variance between groups is homogeneous
    """
    statistic, p_value = levene(*tuple(data))
    return p_value > alpha

def cohens_d(s1: pd.Series, s2: pd.Series) -> float:
    """
    Given two pandas series, returns the Cohen's d
    effect size
    Arguments:
        s1 (Series): the first series
        s2 (Series): the second series
        
    Returns:
        float: Cohen's d effect size
    """
    results = 0

    n1, n2 = len(s1), len(s2) # sample sizes
    var1, var2 = np.var(s1, ddof=1), np.var(s2, ddof=1) # per series variance

    mean1, mean2 = np.mean(s1), np.mean(s2)
    
    # pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    # cohen's d if std > 0
    if pooled_std > 0: 
        results = abs(mean1 - mean2) / pooled_std

    return results

def rank_biserial_correlation(s1: pd.Series, s2: pd.Series) -> float:
    """
    Given two pandas series, returns the rank biserial correlation
    effect size
    Arguments:
        s1 (Series): the first series
        s2 (Series): the second series
        
    Returns:
        float: Rank biserial correlation effect size
    """
    # get combined ranks
    combined = pd.concat([s1, s2])
    ranks = combined.rank()
    
    # split the ranks back to the original groups
    n1 = len(s1)
    n2 = len(s2)
    r1 = ranks[:n1].mean()
    r2 = ranks[n1:].mean()
    
    # calculate the rank biserial correlation
    r = 2 * (r2 - r1) / (n1 + n2)
    
    return abs(r)

def dataframe_to_latex(df, caption="", label="", float_format="%.3f", bold_significant=False):
    """
    Convert a pandas DataFrame to a LaTeX table.
    
    Arguments:
        df (DataFrame): The DataFrame to convert
        caption (str): Caption for the LaTeX table
        label (str): Label for the LaTeX table
        float_format (str): Format string for floating point numbers
        bold_significant (bool): Whether to bold significant values (for p_values < 0.05)
        
    Returns:
        str: LaTeX table code
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Bold significant p_values if requested
    if bold_significant and 'p_value' in df_copy.columns and 'significant' in df_copy.columns:
        df_copy['p_value'] = df_copy.apply(
            lambda row: f"\\textbf{{{float_format % row['p_value']}}}" if row['significant'] else float_format % row['p_value'],
            axis=1
        )
    
    # Start LaTeX table
    latex = "\\begin{table}[htbp]\n\\centering\n"
    
    # Add caption and label if provided
    if caption:
        latex += f"\\caption{{{caption}}}\n"
    if label:
        latex += f"\\label{{{label}}}\n"
    
    # Table header
    latex += "\\begin{tabular}{" + "l" * len(df_copy.columns) + "}\n"
    latex += "\\hline\n"
    
    # Column names
    latex += " & ".join([col.replace("_", "\\_") for col in df_copy.columns]) + " \\\\\n"
    latex += "\\hline\n"
    
    # Convert rows to LaTeX
    for _, row in df_copy.iterrows():
        row_values = []
        for col, val in row.items():
            # Skip already formatted cells (like bolded p_values)
            if isinstance(val, str) and "\\textbf" in val:
                row_values.append(val)
            # Format float values
            elif isinstance(val, float):
                row_values.append(float_format % val)
            # Replace underscores in string values
            elif isinstance(val, str):
                row_values.append(val.replace("_", "\\_"))
            # Everything else
            else:
                row_values.append(str(val))
        
        latex += " & ".join(row_values) + " \\\\\n"
    
    # End LaTeX table
    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"
    
    return latex

def run_statistics_test(metric: str, data: list) -> dict:
    """
    Runs the appropriate omnibus test on input data
    and returns an analysis report
    """
    # check for ANOVA h.
    normal_distibution = has_normal_distribution(data)
    homogeneous_variance = has_homogeneous_variance(data)
    anova_applicable = homogeneous_variance and normal_distibution

    # run test
    statistic, p_value = f_oneway(*tuple(data)) if anova_applicable else kruskal(*tuple(data))
    significant = p_value < 0.05

    # setup data to return
    results = {
        "metric": metric,
        "test": "ANOVA" if anova_applicable else "Kruskal-Wallis",
        "normal_distribution": normal_distibution,
        "homogeneous_variance": homogeneous_variance,
        "statistic": statistic,
        "p_value": p_value,
        "significant": significant
    }
    return results

def run_integrated_analysis(df: pd.DataFrame, metric: str, group_col: str, test_type: str, alpha=0.05) -> pd.DataFrame:
    """
    Runs posthoc tests and calculates effect sizes
    """
    groups = df.groupby(group_col)
    group_names = list(groups.groups.keys())
    
    # run appropriate posthoc test
    if test_type == "ANOVA":
        posthoc_df = posthoc_tukey_hsd(df, val_col=metric, group_col=group_col)
        effect_size_name = "Cohen's d"
    else:
        # bonferroni correction should not be needed in our case
        # posthoc_df = posthoc_dunn(df, val_col=metric, group_col=group_col, p_adjust="bonferroni")
        posthoc_df = posthoc_dunn(df, val_col=metric, group_col=group_col)
        effect_size_name = "r (biserial)"
    
    # set up output
    rows = []
    
    for group1_name, group2_name in itertools.combinations(group_names, 2):
        # get p_value from posthoc
        p_value = posthoc_df.loc[group1_name, group2_name]
        is_significant = p_value < alpha
        
        # get data for both groups on test metric
        group1_data = groups.get_group(group1_name)[metric]
        group2_data = groups.get_group(group2_name)[metric]
        
        # setup basic data structure
        row = {
            'group_1': group1_name,
            'group_2': group2_name,
            'p_value': p_value,
            'significant': is_significant,
            'test': test_type,
            'effect_size_type': effect_size_name,
            'effect_size': None,
            'magnitude': "Not significant"
        }
        
        # include descriptive statistics for effect size interpretation
        mean1 = np.mean(group1_data)
        mean2 = np.mean(group2_data)
        row['group_1_mean'] = mean1
        row['group_2_mean'] = mean2
        row['mean_diff'] = abs(mean1 - mean2)
        median1 = np.median(group1_data)
        median2 = np.median(group2_data)
        row['group_1_median'] = median1
        row['group_2_median'] = median2
        row['median_diff'] = abs(median1 - median2)
        
        # calculate effect sizes
        if test_type == "ANOVA":
            # cohen's d
            effect_size = cohens_d(group1_data, group2_data)
                
            # interpretation
            if effect_size < 0.2:
                interp = "Negligible"
            elif effect_size < 0.5:
                interp = "Small"
            elif effect_size < 0.8:
                interp = "Medium"
            else:
                interp = "Large"
            
        else:
            # rank biserial
            effect_size = rank_biserial_correlation(group1_data, group2_data)
            
            # interpretation
            if effect_size < 0.1:
                interp = "Negligible"
            elif effect_size < 0.3:
                interp = "Small"
            elif effect_size < 0.5:
                interp = "Medium"
            else:
                interp = "Large"
        
        # add calculated effect size and interpretation if significant
        row['effect_size'] = effect_size
        if is_significant:
            row['magnitude'] = interp
        
        rows.append(row)
    
    # convert to dataframe for output
    results_df = pd.DataFrame(rows)
    
    # reorder columns and return
    column_order = [
        'group_1', 'group_2', 'test', 'p_value', 'significant',
        'effect_size_type', 'effect_size', 'magnitude',
        'group_1_mean','group_2_mean', 'mean_diff',
        'group_1_median', 'group_2_median', 'median_diff'
    ]
    
    return results_df[column_order]

def generate_tests_summary(df, group_by, tests_df, posthocs_dict) -> pd.DataFrame:
    """
    Generates a summary table with omnibus test data and statistically
    relevant effect sizes.
    """
    metrics_renames = {
        "diff": "Diff.",
        "A1_allpos_percent": "A1 Coverage (%)",
        "diff_A1_allpos_percent": "A1 Coverage Delta (%)",
        "errors_total": "Errors",
        "diff_errors_total": "Errors Delta"
    }

    continous_metrics = ["A1_allpos_percent", "diff_A1_allpos_percent", "diff"]

    groups_renames = {
        "letter": {
            "a": "1-Step COT",
            "b": "1-Step",
            "c": "2-Step COT",
            "d": "2-Step"
        },
        "model": {
            "gpt4o": "gpt4o",
            "gpt4o-mini": "gpt4o-mini",
            "llama": "Llama-3.3-70b",
        }
    }

    table_columns = list(df[group_by].unique()) + ["Kruskal-Wallis", "Dunn post-hocs"]
    table_indices = metrics_renames.keys()
    table = pd.DataFrame(columns=table_columns, index=table_indices)

    # fill with data
    for idx in table_indices:
        to_insert_series = []
        # means
        for group_name in df[group_by].unique():
            if idx in continous_metrics:
                idx_mean = "{:.2f}".format(df[df[group_by]==group_name][idx].mean())
                idx_std = "{:.3f}".format(df[df[group_by]==group_name][idx].std())

                mean_str = f"{idx_mean} ({idx_std})"
                if (idx == "diff_A1_allpos_percent"):
                    improved_percent = (df[df[group_by]==group_name][idx] >= 0).mean() * 100
                    improved_percent = "{:.0f}".format(improved_percent)
                    mean_str += f"\n{improved_percent}% imp."
                to_insert_series.append(mean_str)
            if "errors" in idx:
                idx_mean = "{:.1f}".format(df[df[group_by]==group_name][idx].mean())
                idx_std = "{:.2f}".format(df[df[group_by]==group_name][idx].std())
                
                mean_str = f"{idx_mean} ({idx_std})"

                if (idx == "diff_errors_total"):
                    improved_percent = (df[df[group_by]==group_name][idx] <= 0).mean() * 100
                    improved_percent = "{:.0f}".format(improved_percent)
                    mean_str += f"\n{improved_percent}% imp."

                to_insert_series.append(mean_str)
        
        # omnibus
        omnibus_stat = "{:.4f}".format(tests_df[tests_df["metric"]==idx]['statistic'][0])
        omnibus_p = "{:.6f}".format(tests_df[tests_df["metric"]==idx]['p_value'][0])

        omnibus_str = f"h = {omnibus_stat}\np = {omnibus_p}"
        to_insert_series.append(omnibus_str)

        # posthocs
        posthocs_str = None
        if idx in posthocs_dict and posthocs_dict[idx] is not None:
            all_effects = posthocs_dict[idx]
            relevant_effects = all_effects[(all_effects["magnitude"] != "Not significant") & (all_effects["magnitude"] != "Negligible")]

            effects_str = []
            for df_index, row in relevant_effects.iterrows():
                magnitude_notation = ""
                match row["magnitude"]:
                    case "Small":
                        magnitude_notation = "*"
                    case "Medium":
                        magnitude_notation = "**"
                    case "Large":
                        magnitude_notation = "***"

                group_1_str = groups_renames[group_by][row["group_1"]]
                group_2_str = groups_renames[group_by][row["group_2"]]
                effects_str.append(f"{group_1_str}/{group_2_str}{magnitude_notation}")

            posthocs_str = "\n".join(effects_str)

        to_insert_series.append(posthocs_str)
        table.loc[idx] = pd.Series(to_insert_series, index=table.columns)

    # rename
    table = table.rename(columns=groups_renames[group_by])
    table = table.rename(index=metrics_renames)

    return table

def summary_df_to_latex(df, caption=None, label=None, title=None, notes=None):
    """
    Convert a DataFrame to a LaTeX table with proper formatting.
    - Left-aligns all cell text
    - Properly positions the caption
    - Handles newlines in cells and escapes LaTeX special characters
    - Adds horizontal lines between rows for better readability
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to convert to LaTeX
    caption : str, optional
        Caption for the table
    label : str, optional
        Label for cross-referencing
    title : str, optional
        Optional title to display above the column names
    notes : str, optional
        Notes to add below the table
        
    Returns:
    --------
    str : LaTeX code for the table
    """
    # Start building the LaTeX table
    latex_lines = []
    
    # Begin table environment
    latex_lines.append("\\begin{table}[htbp]")
    latex_lines.append("\\centering")
    
    # Add caption if provided (before the tabular for better positioning)
    if caption:
        latex_lines.append(f"\\caption{{{escape_latex(caption)}}}")
    
    # Add label if provided
    if label:
        latex_lines.append(f"\\label{{{label}}}")
    
    # Calculate the number of columns (including the index column)
    num_cols = len(df.columns) + 1
    
    # Begin tabular environment
    # First column left-aligned (for index), last column wider with p{} type for text wrapping
    column_format = "l" + "l" * (num_cols - 1)
    latex_lines.append(f"\\begin{{tabular}}{{{column_format}}}")
    
    # Add toprule
    latex_lines.append("\\toprule")
    
    # Add title if provided (spanning all columns)
    if title:
        latex_lines.append(f"\\multicolumn{{{num_cols}}}{{c}}{{\\textbf{{{title}}}}} \\\\")
        latex_lines.append("\\midrule")
    
    # Add header row (centered headers even though cells are left-aligned)
    header_cells = []
    # First add an empty cell for the index column header
    header_cells.append("")
    
    # Then add centered multicolumn cells for each column header
    for col in df.columns:
        escaped_col = escape_latex(col)
        header_cells.append(f"\\multicolumn{{1}}{{c}}{{\\textbf{{{escaped_col}}}}}")
    
    header_row = " & ".join(header_cells)
    latex_lines.append(header_row + " \\\\")
    latex_lines.append("\\midrule")
    
    # Add data rows
    for idx_num, (idx, row) in enumerate(df.iterrows()):
        # Start with the index (left column) in bold
        row_str = f"\\textbf{{{escape_latex(str(idx))}}}"
        
        # Add each cell value
        for col in df.columns:
            cell_value = row[col]
            if cell_value is None or pd.isna(cell_value):
                cell_value = ""
            else:
                cell_value = str(cell_value)
                # Handle multiline cells
                if "\n" in cell_value:
                    lines = cell_value.split("\n")
                    # Escape each line and join with LaTeX newline
                    escaped_lines = [escape_latex(line) for line in lines]
                    cell_value = "\\\\ ".join(escaped_lines)
                    
                    # For the last column, don't need parbox since we're using p{} column type
                    if col == df.columns[-1]:  # Last column
                        cell_value = f"\\parbox[t]{{0.45\\textwidth}}{{{cell_value}}}"
                    else:
                        # Other columns still use parbox
                        cell_value = f"\\parbox[t]{{0.2\\textwidth}}{{{cell_value}}}"
                else:
                    cell_value = escape_latex(cell_value)
            
            row_str += f" & {cell_value}"
            
        # Add the row
        latex_lines.append(row_str + " \\\\")
        
        # Add a horizontal line after each row (except the last one)
        if idx_num < len(df) - 1:
            latex_lines.append("\\midrule")
    
    # Add bottom rule
    latex_lines.append("\\bottomrule")
    
    # End tabular environment
    latex_lines.append("\\end{tabular}")
    
    # Add notes if provided
    if notes:
        latex_lines.append("\\vspace{0.5em}")
        latex_lines.append("\\begin{flushleft}")
        latex_lines.append(f"\\small{{\\textit{{Note:}} {escape_latex(notes)}}}")
        latex_lines.append("\\end{flushleft}")
    
    # End table environment
    latex_lines.append("\\end{table}")
    
    return "\n".join(latex_lines)

def escape_latex(text):
    """
    Escape LaTeX special characters in a string.
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Define LaTeX special characters and their escaped versions
    special_chars = {
        '%': '\\%',
        '&': '\\&',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',
    }
    
    # Escape backslash first
    if '\\' in text:
        text = text.replace('\\', special_chars['\\'])
    
    # Escape all other special characters
    for char, escape_seq in special_chars.items():
        if char != '\\' and char in text:
            text = text.replace(char, escape_seq)
    
    return text

# --- i/o references
INPUT_FILE = "analysis_report.xlsx"
OUTPUT_DIR = "./tests_100"

# output format
OUTPUT_LATEX = True

# --- read data
df = pd.read_excel(INPUT_FILE, header=0)

# separate by language & test by group
idioms = df["idiom"].unique()
group_labels = ["letter", "model"]

for idiom, group_by in itertools.product(idioms, group_labels):
    print(f"Processing {idiom}...")
    sub_df = df[df["idiom"] == idiom]

    # drop columns with N/A
    sub_df = sub_df.dropna(axis="columns", how="all")

    # setup our metrics groups
    percentage_metrics = ["A1_allpos_percent", "A2_allpos_percent"]
    #non_normal_metrics = ["diff", "meaning", "language"]
    non_normal_metrics = ["diff"]
    errors_metrics = [x for x in sub_df.columns.values.tolist() if x.startswith("errors_")]
    original_errors_metrics = [x for x in sub_df.columns.values.tolist() if x.startswith("original_errors_")]

    # add in the sum of error counts
    sub_df["errors_total"] = sub_df[errors_metrics].sum(axis=1)
    errors_metrics.append("errors_total")

    # also add in the sum of errors on original sentence
    sub_df["original_errors_total"] = sub_df[original_errors_metrics].sum(axis=1)
    original_errors_metrics.append("original_errors_total")

    # diff errors metric
    sub_df["diff_errors_total"] = sub_df["errors_total"] - sub_df["original_errors_total"]
    errors_metrics.append("diff_errors_total")

    # diff percentage metric
    sub_df["diff_A1_allpos_percent"] = sub_df["A1_allpos_percent"] - sub_df["original_A1_allpos_percent"]
    percentage_metrics.append("diff_A1_allpos_percent")

    # and these are all our key metrics
    key_metrics = percentage_metrics + non_normal_metrics + errors_metrics

    # --- ok now we setup a dataframe for our statistical tests and a dict for integrated results
    tests_stats = pd.DataFrame()
    integrated_results = {}

    # and test each metric
    for metric in key_metrics:
        print(f"\tTesting {metric}...")

        # extract data
        grouped_data = sub_df.groupby(group_by)[metric]
        series_data = [series.to_list() for group_name, series in grouped_data]

        # A. statistical test
        results = run_statistics_test(metric, series_data)
        tests_stats = pd.concat([tests_stats, pd.DataFrame([results])])

        # B. integrated posthoc and effect sizes, if applicable
        if results["significant"]:
            test_type = results["test"]
            # Run integrated analysis with posthoc tests and effect sizes
            integrated_results[metric] = run_integrated_analysis(sub_df, metric, group_by, test_type)

    # Save results
    outdir = os.path.join(OUTPUT_DIR, idiom, group_by)
    os.makedirs(outdir, exist_ok=True)
    
    # Save main test results
    tests_stats.to_csv(os.path.join(outdir, "omnibus.tsv"), sep="\t", index=False, encoding="utf-8")

    # Create LaTeX version of omnibus tests
    if OUTPUT_LATEX:
        omnibus_latex = dataframe_to_latex(
            tests_stats, 
            caption=f"Omnibus Statistical Tests for {idiom} on {group_by}", 
            label=f"tab:omnibus-{idiom}-{group_by}",
            bold_significant=True
        )
        with open(os.path.join(outdir, "omnibus.tex"), 'w', encoding='utf-8') as f:
            f.write(omnibus_latex)
    
    # Save integrated results for significant metrics
    for metric in integrated_results.keys():
        integrated_results[metric].to_csv(os.path.join(outdir, f"posthoc_{metric}.tsv"), sep="\t", index=False, encoding="utf-8")

        for metric in integrated_results.keys():
            integrated_results[metric].to_csv(os.path.join(outdir, f"posthoc_{metric}.tsv"), sep="\t", index=False, encoding="utf-8")
            
            # Create LaTeX version of posthoc tests
            if OUTPUT_LATEX:
                posthoc_latex = dataframe_to_latex(
                    integrated_results[metric],
                    caption=f"Posthoc Tests for {metric} ({idiom} on {group_by})",
                    label=f"tab:posthoc-{idiom}-{group_by}-{metric.replace('_', '-')}",
                    bold_significant=True
                )
                with open(os.path.join(outdir, f"posthoc_{metric}.tex"), 'w', encoding='utf-8') as f:
                    f.write(posthoc_latex)

    summary_df = generate_tests_summary(sub_df, group_by, tests_stats, integrated_results)
    summary_df.to_csv(os.path.join(outdir, f"significant_effects_summary.tsv"), sep="\t", index=True, encoding="utf-8")

    if OUTPUT_LATEX:
        latex_code = summary_df_to_latex(
            summary_df,
            title="Table Title",
            caption="Table Caption",
            label="tab:table_label",
            notes="* indicates small effect size, ** indicates medium effect size, *** indicates large effect size. 'imp.' stands for improvement rate."
        )

        # Save to file
        with open(os.path.join(outdir, f"significant_effects_summary.tex"), "w") as f:
            f.write(latex_code)
        
    print(f"Results for [{idiom}/{group_by}] saved to {outdir}")

print("Analysis complete!")