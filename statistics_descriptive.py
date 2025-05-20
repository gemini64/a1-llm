import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os, itertools

# --- SECTION 1 - Descriptive Statistics
###
# Using a split approach to represent
# descriptive statistics for our key metrics.
#
# So:
#     * for normally distributed data (percentages) -> mean and std
#     * for non-normally distributed data -> median and Q1, Q3 quartiles
#     * for errors -> error frequencies
#     (this cause error counts tend to have a left-skewed distribution)
###

# --- i/o references
INPUT_FILE = "analysis_report.xlsx"
OUTPUT_DIR = "./statistics_descriptive_100"

# table renames
GROUP_TABLE_NAME = {
    "letter": "Strategy",
    "model": "Model"
}

X_TICKS_RENAMES = {
    "letter": {
        "a": "1-Step COT",
        "b": "1-Step",
        "c": "2-Step COT",
        "d": "2-Step",
    },
    "model": {
        "gpt4o": "gpt4o",
        "gpt4o-mini": "gpt4o-mini",
        "llama": "Llama-3.3",
    }
}

# errors frequency bins
errors_frequency_bins = {
    "0": (0,0),
    "1": (1,1),
    "2": (2,2),
    "3+": (3,float('inf'))
}

# --- read data
df = pd.read_excel(INPUT_FILE, header=0)

# separate by language & test by group
idioms = df["idiom"].unique()
group_labels = ["letter", "model"]

# iterate over languages
for idiom, group_by in itertools.product(idioms, group_labels):
    sub_df = df[df["idiom"] == idiom]

    # --- extend and remove N/A data
    # drop columns with N/A
    sub_df = sub_df.dropna(axis="columns", how="all")

    # setup our metrics groups
    percentage_metrics = ["A1_allpos_percent", "A2_allpos_percent"]
    non_normal_metrics = ["diff"]
    errors_metrics = [ x for x in sub_df.columns.values.tolist() if x.startswith("errors_") ]

    # add errors_totals
    sub_df["errors_total"] = df[errors_metrics].sum(axis=1)
    sub_df["original_errors_total"] = df[[f"original_{x}" for x in errors_metrics]].sum(axis=1)
    errors_metrics.append("errors_total")

    # also add in diff metrics
    diff_tagets = percentage_metrics + errors_metrics
    diff_metrics = [f"diff_{x}" for x in diff_tagets ]
    for metric in diff_tagets:
        sub_df[f"diff_{metric}"] = sub_df[metric] - sub_df[f"original_{metric}"]

    # total error counts metrics
    error_metrics_total = ["errors_total", "original_errors_total"]

    # and these are all our metrics
    key_metrics = percentage_metrics + non_normal_metrics + errors_metrics + diff_metrics

    # --- descriptive statis
    descriptive_stats = pd.DataFrame()

    # iterate over groups
    for group_name, subset in sub_df.groupby(group_by):

        for metric in key_metrics:
            row_data = {
                'group': group_name,
                'metric': metric,
                'count': len(subset),
                'min': subset[metric].min(),
                'max': subset[metric].max(),
                'mean': subset[metric].mean(),
                'std': subset[metric].std(),
                'sem': subset[metric].sem(),
                'median': subset[metric].median(),
                'q1': subset[metric].quantile(0.25),
                'q3': subset[metric].quantile(0.75)
            }

            # additional data for error counts
            if metric in errors_metrics:
                for key, value in errors_frequency_bins.items():
                    row_data[f'{key}_errors_percent'] = (subset[metric].between(*value, inclusive='both')).mean() * 100

            # add entry
            descriptive_stats = pd.concat([descriptive_stats, pd.DataFrame([row_data])])

    # output descriptive stats table
    outdir = os.path.join(OUTPUT_DIR, idiom, group_by)
    os.makedirs(outdir, exist_ok=True)
    descriptive_stats.to_csv(os.path.join(outdir, "descriptive_stats.tsv"), sep="\t", encoding="utf-8", index=False)
    
    # --- figures
    # - a. lingustic metrics - boxplots
    linguistic_y_labels = {
        "diff": "Diff. (0-100)",
        "A1_allpos_percent": "Coverage (%)",
    }

    linguistic_titles = {
        "diff": "Linguistic Diff.",
        "A1_allpos_percent": "A1 Coverage (%)",
    }

    linguistic_metrics = ["diff", "A1_allpos_percent"]
    plt.figure(figsize=(10, 6))
    for i, metric in enumerate(linguistic_metrics):
        plt.subplot(1, 2, i+1)
        ax = sns.boxplot(x=group_by, y=metric, data=sub_df)
        plt.title(linguistic_titles.get(metric, metric))
        plt.xlabel(GROUP_TABLE_NAME.get(group_by, group_by))
        plt.ylabel(linguistic_y_labels.get(metric, metric))
        # rename ticks
        ticks_labels = ax.get_xticklabels()
        ticks_renames = [X_TICKS_RENAMES[group_by].get(x.get_text(),x) for x in ticks_labels]
        ax.set_xticklabels(ticks_renames)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "linguistic_metrics.png"), dpi=300)

    # - b. A1 Coverage Delta
    # coverage
    plt.figure(figsize=(12, 5))

    # boxplot
    plt.subplot(1, 2, 1)
    ax_1 = sns.boxplot(x=group_by, y='diff_A1_allpos_percent', data=sub_df)
    plt.title("A1 Coverage Delta (%)")
    plt.xlabel(GROUP_TABLE_NAME.get(group_by, group_by))
    plt.ylabel("Coverage Delta (%)")
    # rename ticks
    ticks_labels = ax_1.get_xticklabels()
    ticks_renames = [X_TICKS_RENAMES[group_by].get(x.get_text(),x) for x in ticks_labels]
    ax_1.set_xticklabels(ticks_renames)

    # Coverage change
    plt.subplot(1, 2, 2)
    means = pd.Series(descriptive_stats[descriptive_stats["metric"] == "diff_A1_allpos_percent"]["mean"].values, index=descriptive_stats[descriptive_stats["metric"] == "diff_A1_allpos_percent"]["group"])
    stderr = pd.Series(descriptive_stats[descriptive_stats["metric"] == "diff_A1_allpos_percent"]["sem"].values, index=descriptive_stats[descriptive_stats["metric"] == "diff_A1_allpos_percent"]["group"])

    # create bars
    bars = plt.bar(means.index, means.values)
    plt.errorbar(x=range(len(means)), y=means.values, yerr=stderr.values, 
                fmt='none', c='black', capsize=5)
    
    plt.xticks(range(len(means.index)), [X_TICKS_RENAMES[group_by].get(x, x) for x in means.index])

    # assign colors
    for j, bar in enumerate(bars):
        if means.values[j] >= 0:
            bar.set_color('green')
        else:
            bar.set_color('red')

    # horizontal line at y=0
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    # labels and title
    plt.title("A1 Coverage Change")
    plt.xlabel(GROUP_TABLE_NAME.get(group_by, group_by))
    plt.ylabel("A1 Mean Change (%)")

    y_min, y_max = plt.ylim()

    # percentage of improvement as text with improved positioning
    for j, mod in enumerate(sub_df[group_by].unique()):
        improved_pct = (sub_df[sub_df[group_by] == mod]['diff_A1_allpos_percent'] >= 0).mean() * 100
        
        # Different positioning strategy based on whether bar is positive or negative
        if means.values[j] <= 0:
            # For negative bars: place text below the bar
            y_pos = means.values[j] - stderr.values[j] - 0.1
            va = 'top'
        else:
            # For positive bars: place text above the bar
            y_pos = means.values[j] + stderr.values[j] + 0.05 + (j * 0.05)
            va = 'bottom'
        
        plt.text(j, y_pos, f"{improved_pct:.0f}% imp.", ha='center', va=va, fontsize=9)

    # Calculate appropriate margins
    top_margin = max(0.2, (y_max - y_min) * 0.25)  # At least 0.2 or 25% of current range
    bottom_margin = max(0.2, (y_max - y_min) * 0.15)  # At least 0.2 or 15% of current range

    plt.ylim(y_min - bottom_margin, y_max + top_margin)

    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "vocabulary_delta.png"), dpi=300)

    # - c. errors delta
    plt.figure(figsize=(12, 5))

    # boxplot
    plt.subplot(1, 2, 1)
    ax_1 = sns.boxplot(x=group_by, y='diff_errors_total', data=sub_df)
    plt.title("Errors Delta")
    plt.xlabel(GROUP_TABLE_NAME.get(group_by, group_by))
    plt.ylabel("Errors Delta")
    # rename ticks
    ticks_labels = ax_1.get_xticklabels()
    ticks_renames = [X_TICKS_RENAMES[group_by].get(x.get_text(),x) for x in ticks_labels]
    ax_1.set_xticklabels(ticks_renames)

    # errors count change
    plt.subplot(1, 2, 2)
    # Group by modality and calculate mean and standard error
    means = pd.Series(descriptive_stats[descriptive_stats["metric"] == "diff_errors_total"]["mean"].values, index=descriptive_stats[descriptive_stats["metric"] == "diff_errors_total"]["group"])
    stderr = pd.Series(descriptive_stats[descriptive_stats["metric"] == "diff_errors_total"]["sem"].values, index=descriptive_stats[descriptive_stats["metric"] == "diff_errors_total"]["group"])

    # create bars
    bars = plt.bar(means.index, means.values)
    plt.errorbar(x=range(len(means)), y=means.values, yerr=stderr.values, 
                fmt='none', c='black', capsize=5)
    
    plt.xticks(range(len(means.index)), [X_TICKS_RENAMES[group_by].get(x, x) for x in means.index])

    # negative is better - fewer errors
    for j, bar in enumerate(bars):
        if means.values[j] <= 0:
            bar.set_color('green')
        else:
            bar.set_color('red')

    # horizontal line at y=0
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    # labels and title
    plt.title("Errors Count Change")
    plt.xlabel(GROUP_TABLE_NAME.get(group_by, group_by))
    plt.ylabel("Mean Errors Count Change")

    # Get current y-axis limits before adding labels
    y_min, y_max = plt.ylim()

    # percentage of improvements as text with improved positioning
    for j, mod in enumerate(sub_df[group_by].unique()):
        improved_pct = (sub_df[sub_df[group_by] == mod]['diff_errors_total'] >= 0).mean() * 100
        
        # Different positioning strategy based on whether bar is positive or negative
        if means.values[j] <= 0:
            # For negative bars: place text below the bar
            y_pos = means.values[j] - stderr.values[j] - 0.1
            va = 'top'
        else:
            # For positive bars: place text above the bar with staggered heights
            y_pos = means.values[j] + stderr.values[j] + 0.05 + (j * 0.05)
            va = 'bottom'
        
        plt.text(j, y_pos, f"{improved_pct:.0f}% imp.", ha='center', va=va, fontsize=9)

    # Adjust y-axis limits to make room for the labels
    # Calculate appropriate margins
    top_margin = max(0.3, (y_max - y_min) * 0.30)  # At least 0.3 or 30% of current range
    bottom_margin = max(0.2, (y_max - y_min) * 0.15)  # At least 0.2 or 15% of current range

    plt.ylim(y_min - bottom_margin, y_max + top_margin)

    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "errors_delta.png"), dpi=300)

    # - e. errors distributions
    plt.figure(figsize=(15, 10))
    for i, error_type in enumerate(errors_metrics):
        plt.subplot(2, 3, i+1)
        
        # table name for display
        if error_type == 'errors_total':
            clean_name = 'Total Errors'
        else:
            clean_name = error_type.replace('errors_', '').capitalize() + " Errors"
        
        # get the actual data for this error type to analyze distribution
        error_values = sub_df[error_type]
        max_error = int(error_values.max())
        
        # --- create appropriate bins based on actual data distribution
        error_bins = {}
        
        # include 0, 1, 2 as individual bins
        error_bins["0"] = (0, 0)
        error_bins["1"] = (1, 1)
        error_bins["2"] = (2, 2)
        
        # for total errors, append additional bins
        if error_type == 'errors_total':
            # only add more specific bins if data actually contains those values
            if max_error >= 3:
                error_bins["3"] = (3, 3)
            if max_error >= 4:
                # if we have values > 3
                error_bins["4+"] = (4, float('inf'))
        else:
            # for other error types, if max > 2
            if max_error > 2:
                error_bins["3+"] = (3, float('inf'))
        
        # compute percentages for each group and each bin
        percentages_data = []
        
        unique_groups = sorted(sub_df[group_by].unique())
        
        for group_name in unique_groups:
            group_data = sub_df[sub_df[group_by] == group_name]
            
            for bin_label, (bin_min, bin_max) in error_bins.items():
                percentage = (group_data[error_type].between(
                    bin_min, bin_max, inclusive='both')).mean() * 100
                    
                percentages_data.append({
                    'group': group_name,
                    'bin': bin_label,
                    'percentage': percentage
                })
        
        # convert to DataFrame
        plot_df = pd.DataFrame(percentages_data)
        
        # convert to pivot table
        pivot_df = plot_df.pivot(index='bin', columns='group', values='percentage')
        
        # reorder frequency bins
        pivot_df = pivot_df.reindex(error_bins.keys())
        
        # plot data
        ax = pivot_df.plot(kind='bar', ax=plt.gca())
        
        # rename legend items
        handles, labels = ax.get_legend_handles_labels()
        renamed_labels = [X_TICKS_RENAMES[group_by].get(label, label) for label in labels]
        ax.legend(handles, renamed_labels, title=GROUP_TABLE_NAME.get(group_by, group_by))
        
        plt.title(f"{clean_name} Distribution")
        plt.xlabel("Errors Count")
        plt.ylabel("Percentage of Texts (%)")
        plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "errors_frequencies.png"), dpi=300)

    # - f. correlation matrices
    metrics_df = sub_df[key_metrics]
    corr_df = metrics_df.corr(method="spearman") # as this seems the most appropriate method
    corr_df = corr_df.style.background_gradient(cmap='coolwarm', axis=None)

    corr_df.to_excel(os.path.join(outdir, "correlation_matrix.xlsx"), engine="openpyxl", index=True)