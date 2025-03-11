import os, re, json, time, argparse, spacy
from dotenv import load_dotenv
import pandas as pd
from agent_tools import regex_message_parser, strip_string, TEXT_TAG_REGEX_PATTERN, token_usage_message_parser
from langchain_core.runnables import Runnable
from collections.abc import Callable
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

# load keys from local settings file
if (os.getenv("PY_ENV") == "DEVELOPMENT"):
    load_dotenv()

# set up parser
parser = argparse.ArgumentParser(
    prog="paraphrase",
    description="Given a set of texts as input, performs text transformations to make the input text conform to given linguistic constraints."
)

parser.add_argument("input", help="a TSV file containing the texts to paraphrase")
parser.add_argument("-c", "--constraints", help="a plain-text file containing the linguistic constraints to follow when paraphrasing", required=True)
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="completions")
parser.add_argument('-o', '--output', help="(optional) output file")
parser.add_argument('-d', '--debug', action='store_true', help="(optional) log additional information")
parser.add_argument('-g', '--groq', action='store_true', help="(optional) run on groq cloud")
parser.add_argument('-t', '--type', help="(optional) how the paraphrase should be performed, default is fulltext", 
                   choices=['fulltext', 'bysentence', 'nocot'],
                   type=str,
                   default='fulltext')
parser.add_argument("-s", "--sentencizer", 
                   help="language used to initialize the sentencizer (required if paraphrasing bysentence)", 
                   choices=['italian', 'english', 'russian'],
                   type=str)
parser.add_argument("-r", "--retries", 
                   help="maximum number of retries if model fails to respond as expected", 
                   type=int,
                   default=0)

def validate_args(args):
    """Validate command line arguments"""
    if not (os.path.isfile(args.input) and (os.path.splitext(args.input)[-1].lower() == ".tsv")):
        print("Error: the input file does not exist or is not a supported format!")
        exit(2)

    if not os.path.isfile(args.constraints):
        print("Error: the constraints file provided does not exist!")
        exit(2)

    output_file = args.output if args.output else f"{os.path.splitext(args.input)[0]}_paraphrases_{args.type}.tsv"
    if os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file))):
        print(f"Error: an output file with path '{output_file}' already exists!")
        exit(2)

    if args.type == "bysentence" and not args.sentencizer:
        print("Error: --sentencizer is required when using --by-sentence!")
        exit(2)
        
    if args.retries < 0:
        print("Error: --retries must be a non-negative integer!")
        exit(2)

    return output_file

def load_spacy_model(language):
    """Load appropriate spacy model based on language"""
    spacy.prefer_gpu = True
    match language:
        case 'italian':
            return spacy.load("it_core_news_lg")
        case 'english':
            return spacy.load("en_core_web_trf")
        case 'russian':
            return spacy.load("ru_core_news_lg")

def get_prompt_template(paraphrase_type: str):
    """Return appropriate prompt template based on processing mode"""
    base_message = """# Task:
Check if the given {text_type} complies with the constraints provided; generate a paraphrase when necessary.

# Original {text_type}:
{input_text}

# Constraints checking:
Check {check_scope} againts ALL the constraints.
- If it violates no constraint, keep it as is.
- If it violates one or more constraints, paraphrase {action_scope}.

# Paraphrasing:
- A paraphrase must preserve the original semantic meaning and minimize information loss.
- A paraphrase must replace each non-constraints conformant element with an equivalent conformant alternative.
- If a paraphrase that preserves the original meaning and completely conforms to the given constraints cannot be formulated, then the non conformant text should be removed.

{output_format}

# Constraints:
{constraints}"""

    output_format_fulltext = """# Output format:
1. Provide step-by-step reasoning:
- List each constraint checked
- For any violations found:
    - Quote the problematic text
    - Explain which constraint it violates
    - Give a paraphrase for that specific violation (if any can be formulated)
- If no violations are found, state this explicitly

2. End your response with:
<text>[Your final version of the text here - either the original if no changes were needed, or your paraphrased version if changes were made]</text>

Note: The final version MUST be enclosed in <text> tags, regardless of whether changes were made to the original text."""

    output_format_bysentence = """# Output format:
1. Provide step-by-step reasoning:
- List each constraint checked
- For any violations found:
    - Quote the problematic text
    - Explain which constraint it violates
    - Give a paraphrase for that specific violation (if any can be formulated)
- If no violations are found, state this explicitly

2. End your response with:
<text>[Your final version of the sentence here - either the original if no changes were needed, or your paraphrased version if changes were made]</text>

Note: The final version MUST be enclosed in <text> tags, regardless of whether changes were made to the original sentence."""

    output_format_nocot = """# Output format:
Format your response as shown below, no additional comment is needed:

<text>[Your final version of the text here - either the original if no changes were needed, or your paraphrased version if changes were made]</text>

Note: The final version MUST be enclosed in <text> tags, regardless of whether changes were made to the original text."""

    match paraphrase_type:
        case "bysentence":
            message = base_message.format(
                text_type="sentence",
                check_scope="the given sentence",
                action_scope="it",
                input_text="{input_text}",
                constraints="{constraints}",
                output_format=output_format_bysentence
            )
        case "fulltext":
            message = base_message.format(
                text_type="text",
                check_scope="each sentence",
                action_scope="or remove it",
                input_text="{input_text}",
                constraints="{constraints}",
                output_format=output_format_fulltext
            )
        case "nocot":
            message = base_message.format(
                text_type="text",
                check_scope="each sentence",
                action_scope="or remove it",
                input_text="{input_text}",
                constraints="{constraints}",
                output_format=output_format_nocot
            )

    return ChatPromptTemplate.from_messages([("user", message)])

def setup_llm(use_groq):
    """Configure and return appropriate LLM"""
    model = "gpt-4o-2024-11-20"
    temperature = 0
    top_p = 0.95

    if use_groq:
        return ChatGroq(
            model=os.getenv("GROQ_MODEL"),
            temperature=temperature,
            model_kwargs={"top_p": top_p}
        )
    else:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            top_p=top_p
        )

def process_text(
    text: str,
    chain: Runnable,
    message_parser: Callable[...,str],
    token_parser: Callable[...,int],
    constraints: str,
    max_iterations: int,
    max_retries: int,
    use_groq: bool):
    """Process a single text chunk (sentence or full text) with retry mechanism
    
    Arguments:
        Arguments:
        text (str): the input text to paraphrase
        chain (Runnable): the LLM text processing chain
        message_parser (Callable[..., dict]): AIMessage output parser, should return a string
        token_parser (Callable[..., dict]): AIMessage token parser, given an AIMessage, returns the amount of consumed tokens
        constraints (str): the linguistic constraints list
        max_iterations (int): the upper limit to the iterative paraphrase process
        max_retries (int): maximum number of retries if the model output is invalid
        use_groq (bool): set to True to run inference on groq cloud models"""

    current = text
    messages = []
    iteration = None
    token_usage = 0
    warnings = []
    last_good_response = None  # Track the last good response
    
    for i in range(1, max_iterations):
        iteration = i
        retry_count = 0
        successful = False
        
        # Add the user message for this iteration
        messages.append({
            "role": "user",
            "content": current
        })
        
        # Try to get a valid response with retries
        while retry_count <= max_retries and not successful:
            # Invoke the model
            results = chain.invoke({
                "input_text": current,
                "constraints": constraints
            })
            
            # Record the response
            messages.append({
                "role": "assistant",
                "content": results.content
            })
            
            # --- this is to keep consumption within free tier limits
            if use_groq:
                time.sleep(30)
            
            # Update token usage
            token_usage += token_parser(results)
            
            # Try to extract the text content with the parser
            message_content = message_parser(results)
            
            if message_content is not None:
                # We got a valid response with matching <text> tags
                last_good_response = message_content
                successful = True
            else:
                # Parser returned None (no <text> tags found) - need to retry
                retry_count += 1
                if retry_count <= max_retries:
                    # Document the retry in messages
                    retry_message = f"Retry {retry_count}/{max_retries}: No <text> tags found in response, retrying..."
                    messages.append({
                        "role": "system",
                        "content": retry_message
                    })

                else:
                    # Max retries reached, use last good response or mark as error
                    if last_good_response:
                        warning = f"WARNING: Iteration {i}: Failed to find <text> tags after {max_retries} retries. Using last good response."
                        warnings.append(warning)
                        message_content = last_good_response
                        successful = True  # Consider it successful since we're using a valid response
                    else:
                        warning = f"ERROR: Iteration {i}: Failed to find <text> tags after {max_retries} retries. No good previous response available. Using original text."
                        warnings.append(warning)
                        message_content = current
                        successful = True  # Mark as successful to exit the retry loop, but with an error value
            
        # Check if we should continue iterations (text hasn't changed)
        if compare_texts(message_content, current):
            break
        else:
            # Update current text for next iteration
            current = message_content
    
    return current, iteration, messages, token_usage, warnings

def compare_texts(text1: str, text2: str) -> bool:
    """Compares two strings. If their content matches,
    excluding whitespaces and newlines, returns True
    
    Arguments:
        text1 (str): the first text
        text2 (str): the second text
        
    Returns:
        bool: whether the two input texts match"""
    processed_text1 = ' '.join(text1.split())
    processed_text2 = ' '.join(text2.split())
    
    # Compare the processed texts
    return processed_text1 == processed_text2

def main():
    # Parse and validate arguments
    args = parser.parse_args()
    output_file = validate_args(args)

    # Load data
    with open(args.constraints, "r", encoding="utf-8") as f_in:
        constraints = f_in.read()

    df = pd.read_csv(args.input, sep="\t", encoding="utf-8", header=0)
    if args.label not in df:
        print(f"Error: no column named '{args.label}' exists in '{args.input}'!")
        exit(2)

    df = df[[args.label]]
    df.rename(columns={args.label: 'texts'}, inplace=True)

    # Setup processing pipeline
    nlp = load_spacy_model(args.sentencizer) if args.type == "bysentence" else None
    prompt_template = get_prompt_template(args.type)
    llm = setup_llm(args.groq)
    
    # Setup chain and parsers
    message_parser = regex_message_parser(regex=TEXT_TAG_REGEX_PATTERN)
    token_parser = token_usage_message_parser
    chain = prompt_template | llm

    max_iterations = 10
    paraphrases = []
    iterations = []
    messages = []
    tokens = []
    all_warnings = []  # List to collect warnings

    # Process texts
    for input_text in df['texts']:
        if args.type == "bysentence":
            # Process sentence by sentence
            documents = nlp(input_text)
            sentences = [strip_string(sent.text) for sent in documents.sents]
            
            session_text = []
            session_messages = []
            session_iterations = []
            session_tokens = 0
            session_warnings = []

            for sentence in sentences:
                current, sent_iter, sent_messages, sent_tokens, warnings = process_text(
                    sentence, chain, message_parser, token_parser, constraints,
                    max_iterations, args.retries, args.groq
                )
                session_text.append(current)
                session_iterations.append(sent_iter)
                session_messages.append(sent_messages)
                session_tokens += sent_tokens
                session_warnings.extend(warnings)

            paraphrases.append(" ".join(session_text))
            iterations.append(session_iterations)
            messages.append(session_messages)
            tokens.append(session_tokens)
            all_warnings.append(session_warnings)
        else:
            # Process entire text at once
            current, iteration, message_session, token_usage, warnings = process_text(
                input_text, chain, message_parser, token_parser, constraints,
                max_iterations, args.retries, args.groq
            )
            paraphrases.append(current)
            iterations.append(iteration)
            messages.append(message_session)
            tokens.append(token_usage)
            all_warnings.append(warnings)

    # Add results to dataframe
    df.insert(len(df.columns), "paraphrases", paraphrases)

    if args.debug:
        if args.type == "bysentence":
            df.insert(len(df.columns), "iterations", 
                     list(map(lambda x: json.dumps(x, ensure_ascii=False), iterations)))
            df.insert(len(df.columns), "total_iterations", 
                     list(map(lambda x: sum(x), iterations)))
            df.insert(len(df.columns), "warnings", list(map(lambda x: json.dumps(x, ensure_ascii=False), all_warnings)))
        else:
            df.insert(len(df.columns), "iterations", iterations)
            df.insert(len(df.columns), "warnings", all_warnings)
        
        df.insert(len(df.columns), "tokens", tokens)
        df.insert(len(df.columns), "messages", 
                 list(map(lambda x: json.dumps(x, ensure_ascii=False), messages)))

    # Write results
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()