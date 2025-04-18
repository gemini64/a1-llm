import os, json, time, argparse
from dotenv import load_dotenv
import pandas as pd
from utils import regex_message_parser, TEXT_TAG_REGEX_PATTERN, token_usage_message_parser
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
    prog="lexical_simplify",
    description="Simplifies the vocabulary of input texts to make them suitable for L2 language learners."
)

parser.add_argument("input", help="a TSV file containing the texts to simplify")
parser.add_argument("-l", "--label", help="(optional) the label of the column that contains input data", default="text")
parser.add_argument("-t", "--target", help="(optional) the target column name for simplified output", default="simplified")
parser.add_argument('-o', '--output', help="(optional) output file")
parser.add_argument('-d', '--debug', action='store_true', help="(optional) log additional information")
parser.add_argument('-g', '--groq', action='store_true', help="(optional) run on groq cloud")
parser.add_argument('-r', '--retries', 
                   help="maximum number of retries if model fails to respond as expected", 
                   type=int,
                   default=0)
parser.add_argument('-c', '--cefr', 
                   help="(optional) specify CEFR level for vocabulary simplification (default: A1)", 
                   choices=['A1', 'A2', 'B1', 'B2'],
                   type=str,
                   default='A1')

def validate_args(args):
    """Validate command line arguments"""
    if not (os.path.isfile(args.input) and (os.path.splitext(args.input)[-1].lower() == ".tsv")):
        print("Error: the input file does not exist or is not a supported format!")
        exit(2)

    output_file = args.output if args.output else f"{os.path.splitext(args.input)[0]}_simplified.tsv"
    if os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file))):
        print(f"Error: an output file with path '{output_file}' already exists!")
        exit(2)
        
    if args.retries < 0:
        print("Error: --retries must be a non-negative integer!")
        exit(2)

    return output_file

def get_prompt_template(cefr_level: str) -> ChatPromptTemplate:
    """Return appropriate prompt template based on language and CEFR level
    
    Arguments:
        cefr_level (str): CEFR level for vocabulary simplification (A1, A2, etc.)
            
    Returns:
        ChatPromptTemplate: Chain-ready prompt template
    """
    # Base prompt template with placeholders for language-specific details
    base_message = """# Task
Adapt the vocabulary choice of a given text for a target audience of CEFR {cefr_level}-level language learners.

# Instructions
- Aim to use basic, high-frequency vocabulary typical of {cefr_level} level.
- Maintain the original text's core information and meaning.
- Prioritize clarity and comprehension.
- Keep capitalized proper names as they are.
- In exceptional circumstances, you can remove particularly uninformative proper names.
- When you encounter a word that a {cefr_level} student is not expected to know: either explain it with simple words, replace it with a simpler alternative. Remove it only if it is not essential to the main message.

# Input
{input_text}

# Output format
Format your response as shown below, no additional comment is needed:

<text>[Your final version of the adapted text here - use the original text if no changes were needed]</text>

Note: The final version MUST be wrapped in <text> tags, regardless of whether changes were made to the original text."""

    # Format the template with language and CEFR level
    message = base_message.format(
        cefr_level=cefr_level,
        input_text="{input_text}"  # chain placeholder
    )

    return ChatPromptTemplate.from_messages([("user", message)])

def setup_llm(use_groq):
    """Configure and return appropriate LLM"""
    model = "gpt-4o-2024-11-20"
    temperature = 0
    top_p = 1.00

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

def simplify_text(
    text: str,
    chain: Runnable,
    message_parser: Callable[...,str],
    token_parser: Callable[...,int],
    max_retries: int,
    use_groq: bool):
    """Simplify a single text with retry mechanism
    
    Arguments:
        text (str): the input text to simplify
        chain (Runnable): the LLM text processing chain
        message_parser (Callable[..., dict]): AIMessage output parser, should return a string
        token_parser (Callable[..., dict]): AIMessage token parser, returns the amount of consumed tokens
        max_retries (int): maximum number of retries if the model output is invalid
        use_groq (bool): set to True to run inference on groq cloud models
        
    Returns:
        tuple: (simplified_text, messages, token_usage, warnings)
    """
    messages = []
    token_usage = 0
    warnings = []
    simplified_text = None
    retry_count = 0
    successful = False
    
    # Add the user message
    messages.append({
        "role": "user",
        "content": text
    })
    
    # Try to get a valid response with retries
    while retry_count <= max_retries and not successful:
        # Invoke the model
        results = chain.invoke({
            "input_text": text
        })
        
        # Record the response
        messages.append({
            "role": "assistant",
            "content": results.content
        })
        
        # --- this is to keep consumption within free tier limits for Groq
        if use_groq:
            time.sleep(30)
        
        # Update token usage
        token_usage += token_parser(results)
        
        # Try to extract the text content with the parser
        message_content = message_parser(results)
        
        if message_content is not None:
            # We got a valid response with matching <text> tags
            simplified_text = message_content
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
                warnings.append(f"WARNING: Retry {retry_count}/{max_retries} - No <text> tags found in response.")
            else:
                # Max retries reached, using original text as fallback
                warning = f"ERROR: Failed to find <text> tags after {max_retries+1} attempts. Using original text."
                warnings.append(warning)
                simplified_text = text
                successful = True  # Mark as successful to exit the retry loop
    
    return simplified_text, messages, token_usage, warnings

def main():
    # Parse and validate arguments
    args = parser.parse_args()
    output_file = validate_args(args)

    # Load data
    df = pd.read_csv(args.input, sep="\t", encoding="utf-8", header=0)
    if args.label not in df:
        print(f"Error: no column named '{args.label}' exists in '{args.input}'!")
        exit(2)

    # Keep all original columns (preserves the structure from paraphrase output)
    df_simplified = df.copy()

    # Setup processing pipeline
    prompt_template = get_prompt_template(args.cefr)
    llm = setup_llm(args.groq)
    
    # Setup chain and parsers
    message_parser = regex_message_parser(regex=TEXT_TAG_REGEX_PATTERN)
    token_parser = token_usage_message_parser
    chain = prompt_template | llm

    simplified_texts = []
    all_messages = []
    all_tokens = []
    all_warnings = []

    counter = 0
    for input_text in df_simplified[args.label]:
        counter += 1
        print(f"INFO\tSimplifying sample [{counter}/{len(df_simplified[args.label])}]")
        
        # Process the text with simplification
        simplified, messages, tokens, warnings = simplify_text(
            input_text, chain, message_parser, token_parser, args.retries, args.groq
        )
        
        simplified_texts.append(simplified)
        all_messages.append(messages)
        all_tokens.append(tokens)
        all_warnings.append(warnings)

    # Add results to dataframe
    df_simplified[args.target] = simplified_texts

    if args.debug:
        df_simplified[f"{args.target}_tokens"] = all_tokens
        df_simplified[f"{args.target}_messages"] = list(map(lambda x: json.dumps(x, ensure_ascii=False), all_messages))
        df_simplified[f"{args.target}_warnings"] = list(map(lambda x: json.dumps(x, ensure_ascii=False), all_warnings))

    # Write results
    df_simplified.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()