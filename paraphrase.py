import os, re, json, time, argparse, spacy
from dotenv import load_dotenv
import pandas as pd
from agent_tools import regex_message_parser, strip_string, TEXT_TAG_REGEX_PATTERN, token_usage_message_parser
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
parser.add_argument('--by-sentence', action='store_true', help="process text sentence by sentence")
parser.add_argument("-s", "--sentencizer", 
                   help="language used to initialize the sentencizer (required if --by-sentence is used)", 
                   choices=['italian', 'english', 'russian'],
                   type=str)

def validate_args(args):
    """Validate command line arguments"""
    if not (os.path.isfile(args.input) and (os.path.splitext(args.input)[-1].lower() == ".tsv")):
        print("Error: the input file does not exist or is not a supported format!")
        exit(2)

    if not os.path.isfile(args.constraints):
        print("Error: the constraints file provided does not exist!")
        exit(2)

    output_file = args.output if args.output else f"{os.path.splitext(args.input)[0]}_paraphrases{'_sentences' if args.by_sentence else ''}.tsv"
    if os.path.exists(output_file) or not os.path.exists(os.path.dirname(os.path.abspath(output_file))):
        print(f"Error: an output file with path '{output_file}' already exists!")
        exit(2)

    if args.by_sentence and not args.sentencizer:
        print("Error: --sentencizer is required when using --by-sentence!")
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

def get_prompt_template(by_sentence=False):
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

# Output format:
1. Provide step-by-step reasoning:
- List each constraint checked
- For any violations found:
    - Quote the problematic text
    - Explain which constraint it violates
    - Give a paraphrase for that specific violation (if any can be formulated)
- If no violations are found, state this explicitly

2. End your response with:
<text>[Your final version of the {text_type} here - either the original if no changes were needed, or your paraphrased version if changes were made]</text>

Note: The final version MUST be enclosed in <text> tags, regardless of whether changes were made to the original {text_type}.

# Constraints:
{constraints}"""

    if by_sentence:
        message = base_message.format(
            text_type="sentence",
            check_scope="the given sentence",
            action_scope="it",
            input_text="{input_text}",
            constraints="{constraints}"
        )
    else:
        message = base_message.format(
            text_type="text",
            check_scope="each sentence",
            action_scope="or remove it",
            input_text="{input_text}",
            constraints="{constraints}"
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
    text,
    chain,
    message_parser,
    token_parser,
    constraints,
    max_iterations,
    use_groq):
    """Process a single text chunk (sentence or full text)"""
    current = text
    messages = []
    iteration = None
    token_usage = 0

    for i in range(1, max_iterations):
        iteration = i
        
        messages.append({
            "role": "user",
            "content": current
        })

        results = chain.invoke({
            "input_text": current,
            "constraints": constraints
        })

        messages.append({
            "role": "assistant",
            "content": results.content
        })

        if use_groq:
            time.sleep(30)

        token_usage += token_parser(results)
        message_content = message_parser(results)
        
        if message_content is None:
            current = "ERROR"
            break
        elif compare_texts(message_content, current):
            break
        else:
            current = message_content

    return current, iteration, messages, token_usage

def compare_texts(text1, text2):
    # Remove extra whitespace and newlines by:
    # 1. Converting all whitespace (including newlines) to single spaces
    # 2. Removing leading/trailing whitespace
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
    nlp = load_spacy_model(args.sentencizer) if args.by_sentence else None
    prompt_template = get_prompt_template(args.by_sentence)
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

    # Process texts
    for input_text in df['texts']:
        if args.by_sentence:
            # Process sentence by sentence
            documents = nlp(input_text)
            sentences = [strip_string(sent.text) for sent in documents.sents]
            
            session_text = []
            session_messages = []
            session_iterations = []
            session_tokens = 0

            for sentence in sentences:
                current, sent_iter, sent_messages, sent_tokens = process_text(
                    sentence, chain, message_parser, token_parser, constraints,
                    max_iterations, args.groq
                )
                session_text.append(current)
                session_iterations.append(sent_iter)
                session_messages.append(sent_messages)
                session_tokens += sent_tokens

            paraphrases.append(" ".join(session_text) if "ERROR" not in session_text else "ERROR")
            iterations.append(session_iterations)
            messages.append(session_messages)
            tokens.append(session_tokens)
        else:
            # Process entire text at once
            current, iteration, message_session, token_usage = process_text(
                input_text, chain, message_parser, token_parser, constraints,
                max_iterations, args.groq
            )
            paraphrases.append(current)
            iterations.append(iteration)
            messages.append(message_session)
            tokens.append(token_usage)

    # Add results to dataframe
    df.insert(len(df.columns), "paraphrases", paraphrases)

    if args.debug:
        if args.by_sentence:
            df.insert(len(df.columns), "iterations", 
                     list(map(lambda x: json.dumps(x, ensure_ascii=False), iterations)))
            df.insert(len(df.columns), "total_iterations", 
                     list(map(lambda x: sum(x), iterations)))
        else:
            df.insert(len(df.columns), "iterations", iterations)
        
        df.insert(len(df.columns), "tokens", tokens)
        df.insert(len(df.columns), "messages", 
                 list(map(lambda x: json.dumps(x, ensure_ascii=False), messages)))

    # Write results
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()