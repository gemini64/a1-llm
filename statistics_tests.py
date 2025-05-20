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

# --- i/o references
INPUT_FILE = "analysis_report.xlsx"
OUTPUT_DIR = "./statistics_tests_100"

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
    
    # Save integrated results for significant metrics
    for metric in integrated_results.keys():
        integrated_results[metric].to_csv(os.path.join(outdir, f"posthoc_{metric}.tsv"), sep="\t", index=False, encoding="utf-8")

    summary_df = generate_tests_summary(sub_df, group_by, tests_stats, integrated_results)
    summary_df.to_csv(os.path.join(outdir, f"significant_effects_summary.tsv"), sep="\t", index=True, encoding="utf-8")
        
    print(f"Results for [{idiom}] x [{group_by}] saved to {outdir}")

print("Analysis complete!")