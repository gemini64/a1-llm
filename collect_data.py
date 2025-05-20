import os, subprocess
import pandas as pd
import logging

# logging settings
logging.basicConfig(
    filename='collect_data.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# root dir
OUTPUT_DIR = "./vikidia_100"

languages = ["en", "it"]
models = ["gpt4o", "gpt4o-mini", "llama"]
strategies = ["a", "b", "c", "d"]

paraphrase_flags = ""
simplification_flags = ""

openai_models = {
    "gpt4o": "gpt-4o-2024-11-20",
    "gpt4o-mini": "gpt-4o-mini-2024-07-18"
}

# --- main config
config = {
    "input_file": {
        "en": "./vikidia_en_100.tsv",
        "it": "./vikidia_it_100.tsv",
    },
    "paraphrase_tool": "paraphrase.py",
    "simplification_tool": "lexical_simplify.py",
    "grammar_tool": "./eval.py",
    "lexical_tool": "./lexical_analyzer.py",
    "tools_language": {
        "en": "english",
        "it": "italian"
    },
    "tools_taskfiles": {
        "en": "./analysis_tasks/english_analysis_tasks.json",
        "it": "./analysis_tasks/italian_analysis_tasks.json"
    },
    "tools_dictionaries": {
        "en": "./inventories/word_lists/merged_oxford_3000_plus_5000.json",
        "it": "./inventories/word_lists/perugia.json"
    },
    "tools_stopwords": {
        "en": "./inventories/stopwords/stopwords_english.json",
        "it": "./inventories/stopwords/stopwords_italian.json"
    },
    "tools_retries": "3",
    "paraphrase_constraints": {
        "en": {
            "a": "./inventories/constraints_english_w_vocab.md",
            "b": "./inventories/constraints_english_w_vocab.md",
            "c": "./inventories/constraints_english.md",
            "d": "./inventories/constraints_english.md"
        },
        "it": {
            "a": "./inventories/constraints_italian_w_vocab.md",
            "b": "./inventories/constraints_italian_w_vocab.md",
            "c": "./inventories/constraints_italian.md",
            "d": "./inventories/constraints_italian.md"
        }
    },
}

def run_subprocess(args, description):
    """This is just a wrapper to prevent the program
    to stop if any of the subprocesses fail."""
    success = False
    try:
        logging.info(f"Running: {description}")
        print(f"Running: {description}")
        result = subprocess.run(args)
        if result.returncode == 0:
            logging.info(f"Completed successfully: {description}")
            print(f"Completed successfully: {description}")
            success = True
        else:
            logging.error(f"Failed with return code {result.returncode}: {description}")
            print(f"Failed with return code {result.returncode}: {description}")
    except Exception as e:
        logging.error(f"Exception running {description}: {e}")
        print(f"Exception running {description}: {e}")
    
    return success

def get_last_completed(outdir, language, model):
    """Check which reports have already been successfully
    created"""
    completed_strategies = []
    for strategy in strategies:
        final_report = os.path.join(outdir, language, model, f"{strategy}.tsv")
        grammar_output = os.path.join(outdir, language, model, f"{strategy}_grammar.tsv")
        lexical_output = os.path.join(outdir, language, model, f"{strategy}_lexical.tsv")
        
        if (os.path.exists(final_report) and 
            os.path.exists(grammar_output) and 
            os.path.exists(lexical_output)):
            completed_strategies.append(strategy)
    return completed_strategies

# --- processing loop
for language in languages:
    # make outdirs
    outdir = os.path.join(OUTPUT_DIR, language)
    os.makedirs(outdir, exist_ok=True)

    # --- loop over models
    for model in models:
        # set model name via env
        match model:
            case "gpt4o":
                os.environ["OPENAI_MODEL"] = openai_models.get(model, "")
                print(f"Using OpenAI model: {os.getenv('OPENAI_MODEL')}")
                paraphrase_flags = ""
                simplification_flags = ""
            case "gpt4o-mini":
                os.environ["OPENAI_MODEL"] = openai_models.get(model, "")
                print(f"Using OpenAI model: {os.getenv('OPENAI_MODEL')}")
                paraphrase_flags = ""
                simplification_flags = ""
            case "llama":
                # assuming GROQ_MODEL has been set in the .env file
                print(f"Using Groq model: {os.getenv('GROQ_MODEL')}")
                paraphrase_flags = "-g"
                simplification_flags = "-g"
        
        # make outdirs
        outdir = os.path.join(OUTPUT_DIR, language, model)
        os.makedirs(outdir, exist_ok=True)
        
        # check completed reports
        completed = get_last_completed(OUTPUT_DIR, language, model)
        
        # --- loop over strategies
        for strategy in strategies:
            if strategy in completed:
                logging.info(f"Skipping completed: [{language}] x [{model}] x [{strategy}]")
                print(f"Skipping completed: [{language}] x [{model}] x [{strategy}]")
                continue

            # fetch needed variables
            input_file = config["input_file"][language]
            paraphrase_constraints = config["paraphrase_constraints"][language][strategy]
            paraphrase_tool = config["paraphrase_tool"]
            simplification_tool = config["simplification_tool"]
            tools_language = config["tools_language"][language]
            tools_retries = config["tools_retries"]

            logging.info(f"Starting: [{language}] x [{model}] x [{strategy}]")
            print(f"Starting: [{language}] x [{model}] x [{strategy}]")

            final_report = os.path.join(outdir, f"{strategy}.tsv")
            if not os.path.exists(final_report):
                match strategy:
                    # a - single step paraphrase with cot
                    case "a":
                        par_output = os.path.join(outdir, f"{language}_{model}_paradvocab.tsv")
                        if not os.path.exists(par_output):
                            paraphrase_args = ["python", paraphrase_tool,
                                            input_file,
                                            "-c", paraphrase_constraints,
                                            "-l", "text",
                                            "-s", tools_language,
                                            "-r", tools_retries,
                                            "-t", "fulltext",
                                            "-o", par_output,
                                            "-d",
                                            ]
                            if paraphrase_flags != "":
                                paraphrase_args.append(paraphrase_flags)

                            success = run_subprocess(paraphrase_args, f"Paraphrase for [{language}] x [{model}] x [{strategy}]")
                            
                            if not success or not os.path.exists(par_output):
                                logging.error(f"Paraphrase failed or output file not created: {par_output}")
                                print(f"Paraphrase failed or output file not created: {par_output}")
                                continue
                        
                        final_report = os.path.join(outdir, f"{strategy}.tsv")
                        if not os.path.exists(final_report):
                            try:
                                if os.path.exists(par_output):
                                    final_df = pd.read_csv(par_output, sep="\t", encoding="utf-8", header=0)
                                    final_df = final_df[["paraphrase"]]
                                    final_df = final_df.rename(columns={"paraphrase": "text"})
                                    final_df.to_csv(final_report, sep="\t", index=False, encoding="utf-8")
                                    logging.info(f"Created final report: {final_report}")
                                    print(f"Created final report: {final_report}")
                                else:
                                    logging.error(f"Cannot create final report - paraphrase output missing: {par_output}")
                                    print(f"Cannot create final report - paraphrase output missing: {par_output}")
                            except Exception as e:
                                logging.error(f"Error creating final report: {e}")
                                print(f"Error creating final report: {e}")

                    # b - single step paraphrase without cot
                    case "b":
                        par_output = os.path.join(outdir, f"{language}_{model}_paradvocab_nocot.tsv")
                        if not os.path.exists(par_output):
                            paraphrase_args = ["python", paraphrase_tool,
                                            input_file,
                                            "-c", paraphrase_constraints,
                                            "-l", "text",
                                            "-s", tools_language,
                                            "-r", tools_retries,
                                            "-t", "nocot",
                                            "-o", par_output,
                                            "-d",
                                            ]
                            if paraphrase_flags != "":
                                paraphrase_args.append(paraphrase_flags)

                            success = run_subprocess(paraphrase_args, f"Paraphrase for [{language}] x [{model}] x [{strategy}]")

                            if not success or not os.path.exists(par_output):
                                logging.error(f"Paraphrase failed or output file not created: {par_output}")
                                print(f"Paraphrase failed or output file not created: {par_output}")
                                continue
                        
                        final_report = os.path.join(outdir, f"{strategy}.tsv")
                        if not os.path.exists(final_report):
                            try:
                                if os.path.exists(par_output):
                                    final_df = pd.read_csv(par_output, sep="\t", encoding="utf-8", header=0)
                                    final_df = final_df[["paraphrase"]]
                                    final_df = final_df.rename(columns={"paraphrase": "text"})
                                    final_df.to_csv(final_report, sep="\t", index=False, encoding="utf-8")
                                    logging.info(f"Created final report: {final_report}")
                                    print(f"Created final report: {final_report}")
                                else:
                                    logging.error(f"Cannot create final report - paraphrase output missing: {par_output}")
                                    print(f"Cannot create final report - paraphrase output missing: {par_output}")
                            except Exception as e:
                                logging.error(f"Error creating final report: {e}")
                                print(f"Error creating final report: {e}")

                    # c - two steps with cot
                    case "c":
                        par_output = os.path.join(outdir, f"{language}_{model}_par.tsv")
                        if not os.path.exists(par_output):
                            paraphrase_args = ["python", paraphrase_tool,
                                            input_file,
                                            "-c", paraphrase_constraints,
                                            "-l", "text",
                                            "-s", tools_language,
                                            "-r", tools_retries,
                                            "-t", "fulltext",
                                            "-o", par_output,
                                            "-d",
                                            ]
                            if paraphrase_flags != "":
                                paraphrase_args.append(paraphrase_flags)

                            success = run_subprocess(paraphrase_args,  f"Paraphrase for [{language}] x [{model}] x [{strategy}]")
                            
                            if not success or not os.path.exists(par_output):
                                logging.error(f"Paraphrase failed or output file not created: {par_output}")
                                print(f"Paraphrase failed or output file not created: {par_output}")
                                continue

                        simpl_output = os.path.join(outdir, f"{language}_{model}_vocab.tsv")
                        if not os.path.exists(simpl_output) and os.path.exists(par_output):
                            simpl_args = ["python", simplification_tool,
                                        par_output,
                                        "-l", "paraphrase",
                                        "-t", "simplified",
                                        "-c", "A1",
                                        "-p", tools_language,
                                        "-r", tools_retries,
                                        "-o", simpl_output,
                                        "-d",
                                        ]
                            if simplification_flags != "":
                                simpl_args.append(simplification_flags)

                            success = run_subprocess(simpl_args, f"Simplify [{language}] x [{model}] x [{strategy}]")
                            
                            if not success or not os.path.exists(simpl_output):
                                logging.error(f"Simplification failed or output file not created: {simpl_output}")
                                print(f"Simplification failed or output file not created: {simpl_output}")
                                continue

                        final_report = os.path.join(outdir, f"{strategy}.tsv")
                        if not os.path.exists(final_report):
                            try:
                                if os.path.exists(simpl_output):
                                    final_df = pd.read_csv(simpl_output, sep="\t", encoding="utf-8", header=0)
                                    final_df = final_df[["simplified"]]
                                    final_df = final_df.rename(columns={"simplified": "text"})
                                    final_df.to_csv(final_report, sep="\t", index=False, encoding="utf-8")
                                    logging.info(f"Created final report: {final_report}")
                                    print(f"Created final report: {final_report}")
                                else:
                                    logging.error(f"Cannot create final report - simplification output missing: {simpl_output}")
                                    print(f"Cannot create final report - simplification output missing: {simpl_output}")
                            except Exception as e:
                                logging.error(f"Error creating final report: {e}")
                                print(f"Error creating final report: {e}")

                    # d - two steps without cot
                    case "d":
                        par_output = os.path.join(outdir, f"{language}_{model}_par_nocot.tsv")
                        if not os.path.exists(par_output):
                            paraphrase_args = ["python", paraphrase_tool,
                                            input_file,
                                            "-c", paraphrase_constraints,
                                            "-l", "text",
                                            "-s", tools_language,
                                            "-r", tools_retries,
                                            "-t", "nocot",
                                            "-o", par_output,
                                            "-d",
                                            ]
                            if paraphrase_flags != "":
                                paraphrase_args.append(paraphrase_flags)

                            success = run_subprocess(paraphrase_args,  f"Paraphrase for [{language}] x [{model}] x [{strategy}]")
                            
                            if not success or not os.path.exists(par_output):
                                logging.error(f"Paraphrase failed or output file not created: {par_output}")
                                print(f"Paraphrase failed or output file not created: {par_output}")
                                continue

                        simpl_output = os.path.join(outdir, f"{language}_{model}_vocab_nocot.tsv")
                        if not os.path.exists(simpl_output) and os.path.exists(par_output):
                            simpl_args = ["python", simplification_tool,
                                        par_output,
                                        "-l", "paraphrase",
                                        "-t", "simplified",
                                        "-c", "A1",
                                        "-p", tools_language,
                                        "-r", tools_retries,
                                        "-o", simpl_output,
                                        "-d",
                                        ]
                            if simplification_flags != "":
                                simpl_args.append(simplification_flags)

                            success = run_subprocess(simpl_args, f"Simplify [{language}] x [{model}] x [{strategy}]")
                            
                            if not success or not os.path.exists(simpl_output):
                                logging.error(f"Simplification failed or output file not created: {simpl_output}")
                                print(f"Simplification failed or output file not created: {simpl_output}")
                                continue

                        final_report = os.path.join(outdir, f"{strategy}.tsv")
                        if not os.path.exists(final_report):
                            try:
                                if os.path.exists(simpl_output):
                                    final_df = pd.read_csv(simpl_output, sep="\t", encoding="utf-8", header=0)
                                    final_df = final_df[["simplified"]]
                                    final_df = final_df.rename(columns={"simplified": "text"})
                                    final_df.to_csv(final_report, sep="\t", index=False, encoding="utf-8")
                                    logging.info(f"Created final report: {final_report}")
                                    print(f"Created final report: {final_report}")
                                else:
                                    logging.error(f"Cannot create final report - simplification output missing: {simpl_output}")
                                    print(f"Cannot create final report - simplification output missing: {simpl_output}")
                            except Exception as e:
                                logging.error(f"Error creating final report: {e}")
                                print(f"Error creating final report: {e}")

            # redefine variable to avoid scoping issues
            final_report = os.path.join(outdir, f"{strategy}.tsv")
            
            # step 2 - paraphrase analysis
            grammar_tool = config["grammar_tool"]
            lexical_tool = config["lexical_tool"]

            task_file = config["tools_taskfiles"][language]
            dictionary = config["tools_dictionaries"][language]
            stopwords = config["tools_stopwords"][language]

            if os.path.exists(final_report):
                # 2a - grammar analysis
                grammar_output = os.path.join(outdir, f"{strategy}_grammar.tsv")
                if not os.path.exists(grammar_output): 
                    grammar_args = ["python", grammar_tool,
                        final_report,
                        "-t", task_file,
                        "-p", tools_language,
                        "-l", "text",
                        "-r", tools_retries,
                        "-o", grammar_output,
                        "-d"
                    ]

                    success = run_subprocess(grammar_args, f"Running grammar analysis for [{language}] x [{model}] x [{strategy}]")
                    
                    if not success or not os.path.exists(grammar_output):
                        logging.error(f"Grammar analysis failed or output file not created: {grammar_output}")
                        print(f"Grammar analysis failed or output file not created: {grammar_output}")

                # 2b - lexical analysis
                lexical_output = os.path.join(outdir, f"{strategy}_lexical.tsv")
                if not os.path.exists(lexical_output): 
                    lexical_args = ["python", lexical_tool,
                        final_report,
                        "-w", dictionary,
                        "-s", stopwords,
                        "-p", tools_language,
                        "-l", "text",
                        "-o", lexical_output,
                    ]

                    success = run_subprocess(lexical_args, f"Running lexical analysis for [{language}] x [{model}] x [{strategy}]")
                    
                    if not success or not os.path.exists(lexical_output):
                        logging.error(f"Lexical analysis failed or output file not created: {lexical_output}")
                        print(f"Lexical analysis failed or output file not created: {lexical_output}")

# --- summary
print("\nsummary:")
for language in languages:
    for model in models:
        for strategy in strategies:
            outdir = os.path.join(OUTPUT_DIR, language, model)
            final_report = os.path.join(outdir, f"{strategy}.tsv")
            grammar_output = os.path.join(outdir, f"{strategy}_grammar.tsv")
            lexical_output = os.path.join(outdir, f"{strategy}_lexical.tsv")
            
            print(f"[{language}] x [{model}] x [{strategy}]:")
            print(f"\tfinal report: {'OK' if os.path.exists(final_report) else 'KO'}")
            print(f"\tgrammar analysis: {'OK' if os.path.exists(grammar_output) else 'KO'}")
            print(f"\tlexical lexical: {'OK' if os.path.exists(lexical_output) else 'KO'}")