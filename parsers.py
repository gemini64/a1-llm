import copy
from pos_tagger import POSTagger, Language, TAGMethod
from agent_tools import is_regular_it_verb

# Eval template
italian_eval_report = {
    "conform": True,
    "pronouns_conform": True,
    "numbers_conform": True,
    "verbs_conform": True,
    "syntax_conform": True,
    "error_messages": []
}

allowed_pronouns_categories = ["personale", "possessivo", "dimostrativo", "interrogativo", "indefinito"]
allowed_ordinal_numbers = ["primo", "prima", "primi", "prime", "secondo", "seconda", "secondi", "seconde", "terzo", "terza", "terzi", "terze", "1°", "2°", "3°","1′", "2′", "3′"]
allowed_voices = ["attiva"]
allowed_mood_tense_combinations = {
    "indicativo": ["presente", "passato prossimo"],
    "infinito": ["presente"],
    "imperativo": ["presente"]
}

allowed_main_clauses = ["dichiarativa", "volitiva", "interrogativa"]
allowed_coordinate_clauses = ["copulativa", "avversativa", "esplicativa"]
allowed_subordinate_clauses = ["causale", "temporale", "finale", "condizionale", "relativa"]

# Error messages
pronouns_error_message = """The input text contains the pronoun '{text}' with 'kind' = '{kind}'. This pronoun category does not belong to the A1 inventory."""
numbers_error_message = """The input text contains the ordinal number '{text}' which is outside of the A1 inventory allowed range for ordinal numbers."""
verbs_regular_error_message = """The input text contains the verb '{lemma}', (ref -> '{text}') which is an irregular verb."""
verbs_voice_error_message = """The input text contains the verb '{text}' which has 'voice' = 'passiva'."""
verbs_mood_tense_imperative_error_message = """The input text contains the verb '{text}', which has 'mood' = '{mood}', 'person' = '{person}' and 'number' = '{number}'. This combination is outside of the verbs specifications listed in the A1 inventory."""
verbs_mood_tense_error_message = """The input text contains the verb '{text}', which has 'mood' = '{mood}' and 'tense' = '{tense}'. This combination is outside of the verbs specifications listed in the A1 inventory."""
main_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a main clause '{main_clause_text}' with 'function' = '{main_clause_function}', which is outside of the specifications of the A1 inventory."""
main_clause_volitive_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a main clause '{main_clause_text}' with 'function' = '{main_clause_function}', which is allowed according to the A1 inventory, however it does not seem to contain a verb in 'imperative' mood, which is a requirement."""
coordinate_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a coordinate clause '{coordinate_clause_text}' with 'type' = '{coordinate_clause_type}', which is outside of the specifications of the A1 inventory."""
subordinate_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a subordinate clause '{subordinate_clause_text}' with 'function' = '{subordinate_clause_function}', which is outside of the specifications of the A1 inventory."""
subordinate_clause_conditional_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a subordinate clause '{subordinate_clause_text}' with 'function' = '{subordinate_clause_function}', which is allowed according to the A1 inventory, however it does not seem to be introduced by 'se', which is a requirement."""

def parse_italian_analysis(input: dict) -> bool:
    results = copy.deepcopy(italian_eval_report)
    """Given a text analysis report, performs a
    rule-based evaluation to check if the italian A1
    invetory constraints are satisfied."""

    # check pronouns
    for pronoun in input["pronouns"]:
        text = pronoun["text"].lower()
        kind = pronoun["kind"].lower()

        # 1 - pronoun outside of allowed categories
        if (not (kind in set(allowed_pronouns_categories))):
            results["conform"] = False
            results["pronouns_conform"] = False

            results["error_messages"].append(pronouns_error_message.format(text = text, kind = kind))
    
    # check numbers
    for number in input["numbers"]:
        text = number["text"].lower()
        kind = number["kind"].lower()

        # 1 - Number is ordinal and outside of allowed range
        if (kind == "ordinale"):
            if (not (kind in set(allowed_ordinal_numbers))):
                results["conform"] = False
                results["numbers_conform"] = False

                results["error_messages"].append(numbers_error_message.format(text = text))
    
    # check verbs
    for verb in input["verbs"]:
        text = verb["text"].lower()
        lemma = verb["lemma"].lower()
        voice = verb["voice"].lower()
        mood = verb["mood"].lower()
        tense = verb["tense"].lower()

        # 1 - Main verb is irregular
        if (not is_regular_it_verb(verb=lemma, check_allowed=True)):
            results["conform"] = False
            results["verbs_conform"] = False

            results["error_messages"].append(verbs_regular_error_message.format(text = text, lemma=lemma))
        
        # 2 - Main verb is not in active voice
        if (not (voice in set(allowed_voices))):
            results["conform"] = False
            results["verbs_conform"] = False

            results["error_messages"].append(verbs_voice_error_message.format(text = text))

        # 3 - Verb is conjugated in a mood/tense combination out of inventory
        ## Note: if in imperative mood, also have to check person
        if mood == "imperativo":
            if (not verb["person"].lower() == "second"):
                results["conform"] = False
                results["verbs_conform"] = False

                results["error_messages"].append(verbs_mood_tense_imperative_error_message.format(text = text, mood = mood, person = verb["person"], number = verb["number"]))

        else:
            if (not (mood in set(allowed_mood_tense_combinations.keys()))):
                results["conform"] = False
                results["verbs_conform"] = False

                results["error_messages"].append(verbs_mood_tense_error_message.format(text = text, mood = mood, tense = tense))
            else:
                if (not( tense in set(allowed_mood_tense_combinations[mood]))):
                    results["conform"] = False
                    results["verbs_conform"] = False

                    results["error_messages"].append(verbs_mood_tense_error_message.format(text = text, mood = mood, tense = tense))

    # syntax
    for sentence in input["syntactical_analysis"]["sentences"]:
        sentence_text = sentence["content"]
        sentence_type = sentence["type"].lower()
        sentence_clauses = sentence["clauses"]

        # 1 - Main clause outside of allowed clause functions
        main_clause = sentence_clauses["main_clause"]
        main_clause_text = main_clause["content"]
        main_clause_function = main_clause["function"].lower()

        if (not(main_clause_function in set(allowed_main_clauses))):
            results["conform"] = False
            results["syntax_conform"] = False

            results["error_messages"].append(main_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, main_clause_text=main_clause_text, main_clause_function=main_clause_function))

        # 1A - Check verb within volitive clause
        if (main_clause_function == "volitiva"):
            tokens = POSTagger(language=Language.IT, method=TAGMethod.TINT).tag_text(main_clause_text)
            has_imperative = False
            for token in tokens:
                if token["pos"] == "VERB":
                    for verb in input["verbs"]:
                        if (verb["text"].lower().includes(token["text"].lower())):
                            if(verb["mood"].lower() == "imperativo"):
                                has_imperative = True
                                break

                if has_imperative:
                    break
            
            if(not has_imperative):
                results["conform"] = False
                results["syntax_conform"] = False

                results["error_messages"].append(main_clause_volitive_error_message.format(type=sentence_type, sentence_text=sentence_text, main_clause_text=main_clause_text, main_clause_function=main_clause_function))

        # 2 - Coordinate clauses outside of allowed types
        for coordinate_clause in sentence_clauses["coordinate_clauses"]:
            coordinate_clause_text = coordinate_clause["content"]
            coordinate_clause_type = coordinate_clause["type"].lower()

            if (not(coordinate_clause_type in set(allowed_coordinate_clauses))):
                results["conforintransitive_conform"] = False

                results["error_messages"].append(coordinate_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, coordinate_clause_text=coordinate_clause_text, coordinate_clause_type=coordinate_clause_type))
        

        # 3 - Subordinate clauses outside of allowed functions
        for subordinate_clause in sentence_clauses["subordinate_clauses"]:
            subordinate_clause_text = subordinate_clause["content"]
            subordinate_clause_function = subordinate_clause["function"].lower()

            if (not(subordinate_clause_function in set(allowed_subordinate_clauses))):
                results["conform"] = False
                results["syntax_conform"] = False

                results["error_messages"].append(subordinate_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, subordinate_clause_text=subordinate_clause_text, subordinate_clause_function=subordinate_clause_function))

            # 3A - Conditinal subordinate clauses additional check
            if (subordinate_clause_function == "condizionale"):
                content = subordinate_clause_text.lower()

                if(not content.startswith("se")):
                    results["conform"] = False
                    results["syntax_conform"] = False

                    results["error_messages"].append(subordinate_clause_conditional_error_message.format(type=sentence_type, sentence_text=sentence_text, subordinate_clause_text=subordinate_clause_text, subordinate_clause_function=subordinate_clause_function))

    return results