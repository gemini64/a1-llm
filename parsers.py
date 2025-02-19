import copy
from pos_tagger import POSTagger, Language, TAGMethod
from agent_tools import is_regular_it_verb

# --- italian

# --- template
italian_eval_template = {
    "conform": True,
    "pronouns_conform": True,
    "numbers_conform": True,
    "verbs_conform": True,
    "error_messages": []
}

# --- control references
italian_allowed_pronouns_categories = [ "personale", "possessivo", "dimostrativo", "interrogativo", "indefinito" ]
italian_allowed_ordinal_numbers = ["primo", "prima", "primi", "prime", "secondo", "seconda", "secondi", "seconde", "terzo", "terza", "terzi", "terze", "1°", "2°", "3°", "1′", "2′", "3′", "1ª", "2ª", "3ª", "1º", "2º", "3º", "i", "ii", "iii", "primo (1º)", "primo (1°)", "prima (1ª)", "secondo (2º)", "secondo (2°)", "seconda (2ª)", "terzo (3º)", "terzo (3°)", "terza (3ª)" ]
italian_allowed_voices = ["attiva"]
italian_allowed_mood_tense_combinations = {
    "indicativo": ["presente", "passato prossimo"],
    "infinito": ["presente"],
    "imperativo": ["presente"],
    "condizionale": ["presente"]
}

italian_allowed_main_clauses = ["dichiarativa", "volitiva", "interrogativa"]
italian_allowed_coordinate_clauses = ["copulativa", "avversativa", "esplicativa"]
italian_allowed_subordinate_clauses = ["causale", "temporale", "finale", "condizionale", "relativa"]

# --- Error messages
italian_pronouns_error_message = """The input text contains the pronoun '{text}' with 'kind' = '{kind}'. This pronoun category does not belong to the A1 inventory."""
italian_numbers_error_message = """The input text contains the ordinal number '{text}', which falls outside of the A1 inventory allowed range."""
italian_verbs_regular_error_message = """The input text contains the verb '{lemma}', (ref -> '{text}') which is an irregular verb."""
italian_verbs_voice_error_message = """The input text contains the verb '{text}' which has 'voice' = 'passiva'."""
italian_verbs_mood_p_n_error_message = """The input text contains the verb '{text}', which has 'mood' = '{mood}', 'person' = '{person}' and 'number' = '{number}'. This combination falls outside of the verb specifications listed in the A1 inventory."""
italian_verbs_mood_tense_p_n_error_message = """The input text contains the verb '{text}', which has 'mood' = '{mood}', tense = '{tense}', 'person' = '{person}' and 'number' = '{number}'. This combination falls outside of the verb specifications listed in the A1 inventory."""
italian_verbs_mood_tense_error_message = """The input text contains the verb '{text}', which has 'mood' = '{mood}' and 'tense' = '{tense}'. This combination falls outside of the verb specifications listed in the A1 inventory."""
italian_main_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a main clause '{main_clause_text}' with 'function' = '{main_clause_function}', which falls outside of the specifications of the A1 inventory."""
italian_main_clause_volitive_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a main clause '{main_clause_text}' with 'function' = '{main_clause_function}', which is allowed according to the A1 inventory, however it does not seem to contain a verb in 'imperative' mood, which is a requirement."""
italian_coordinate_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a coordinate clause '{coordinate_clause_text}' with 'type' = '{coordinate_clause_type}', which falls outside of the specifications of the A1 inventory."""
italian_subordinate_clause_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a subordinate clause '{subordinate_clause_text}' with 'function' = '{subordinate_clause_function}', which falls outside of the specifications of the A1 inventory."""
italian_subordinate_clause_conditional_error_message = """The sentence '{sentence_text}' (with 'type' = '{type}') contains a subordinate clause '{subordinate_clause_text}' with 'function' = '{subordinate_clause_function}', which is allowed according to the A1 inventory, however it does not seem to be introduced by 'se', which is a requirement."""

def parse_italian_analysis(input: dict, check_syntax: bool = False) -> dict:
    results = copy.deepcopy(italian_eval_template)
    """Given a text analysis report, performs a
    rule-based evaluation to check if the italian A1
    invetory constraints are satisfied."""

    # --- grammar
    # check pronouns
    for pronoun in input["pronouns"]:
        text = pronoun["text"].lower()
        kind = pronoun["kind"].lower()

        # 1 - pronoun outside of allowed categories
        if (kind not in italian_allowed_pronouns_categories):
            results["conform"] = False
            results["pronouns_conform"] = False

            results["error_messages"].append(italian_pronouns_error_message.format(text = text, kind = kind))
    
    # check numbers
    for number in input["numbers"]:
        text = number["text"].lower()
        kind = number["kind"].lower()

        # 1 - Number is ordinal and outside of allowed range
        if (kind == "ordinale"):
            if (text not in italian_allowed_ordinal_numbers):
                results["conform"] = False
                results["numbers_conform"] = False

                results["error_messages"].append(italian_numbers_error_message.format(text = text))
    
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

            results["error_messages"].append(italian_verbs_regular_error_message.format(text = text, lemma=lemma))
        
        # 2 - Main verb is not in active voice
        if (voice not in italian_allowed_voices):
            results["conform"] = False
            results["verbs_conform"] = False

            results["error_messages"].append(italian_verbs_voice_error_message.format(text = text))

        # 3 - Verb is conjugated in a mood/tense combination out of inventory
        ## Note: if in imperative mood, also have to check person
        match mood:
            case "imperativo":
                person = verb["person"].lower()
                number = verb["number"].lower()

                if ( person != "second" ):
                    results["conform"] = False
                    results["verbs_conform"] = False

                    results["error_messages"].append(italian_verbs_mood_p_n_error_message.format(text = text, mood = mood, person = person, number = number))

            case "condizionale":
                person = verb["person"].lower()
                number = verb["number"].lower()

                if ((lemma != "volere") or
                    (tense not in italian_allowed_mood_tense_combinations["condizionale"]) or
                    (person != "first") or
                    (number != "singular") ):
                    results["conform"] = False
                    results["verbs_conform"] = False

                    results["error_messages"].append(italian_verbs_mood_tense_p_n_error_message.format(text = text, mood = mood, tense = tense, person = person, number = number))

            case _:
                if (mood not in set(italian_allowed_mood_tense_combinations.keys())):
                    results["conform"] = False
                    results["verbs_conform"] = False

                    results["error_messages"].append(italian_verbs_mood_tense_error_message.format(text = text, mood = mood, tense = tense))
                else:
                    if (tense not in set(italian_allowed_mood_tense_combinations[mood])):
                        results["conform"] = False
                        results["verbs_conform"] = False

                        results["error_messages"].append(italian_verbs_mood_tense_error_message.format(text = text, mood = mood, tense = tense))

    # --- syntax
    if check_syntax:
        # add syntax key to report
        results["syntax_conform"] = True

        for sentence in input["syntactical_analysis"]["sentences"]:
            sentence_text = sentence["content"]
            sentence_type = sentence["type"].lower()
            sentence_clauses = sentence["clauses"]

            # 1 - Main clause outside of allowed clause functions
            main_clause = sentence_clauses["main_clause"]
            main_clause_text = main_clause["content"]
            main_clause_function = main_clause["function"].lower()

            if (main_clause_function not in italian_allowed_main_clauses):
                results["conform"] = False
                results["syntax_conform"] = False

                results["error_messages"].append(italian_main_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, main_clause_text=main_clause_text, main_clause_function=main_clause_function))

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

                    results["error_messages"].append(italian_main_clause_volitive_error_message.format(type=sentence_type, sentence_text=sentence_text, main_clause_text=main_clause_text, main_clause_function=main_clause_function))

            # 2 - Coordinate clauses outside of allowed types
            for coordinate_clause in sentence_clauses["coordinate_clauses"]:
                coordinate_clause_text = coordinate_clause["content"]
                coordinate_clause_type = coordinate_clause["type"].lower()

                if (coordinate_clause_type not in italian_allowed_coordinate_clauses):
                    results["conform"] = False
                    results["syntax_conform"] = False

                    results["error_messages"].append(italian_coordinate_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, coordinate_clause_text=coordinate_clause_text, coordinate_clause_type=coordinate_clause_type))  

            # 3 - Subordinate clauses outside of allowed functions
            for subordinate_clause in sentence_clauses["subordinate_clauses"]:
                subordinate_clause_text = subordinate_clause["content"]
                subordinate_clause_function = subordinate_clause["function"].lower()

                if (subordinate_clause_function not in set(italian_allowed_subordinate_clauses)):
                    results["conform"] = False
                    results["syntax_conform"] = False

                    results["error_messages"].append(italian_subordinate_clause_error_message.format(type=sentence_type, sentence_text=sentence_text, subordinate_clause_text=subordinate_clause_text, subordinate_clause_function=subordinate_clause_function))

                # 3A - Conditinal subordinate clauses additional check
                if (subordinate_clause_function == "condizionale"):
                    content = subordinate_clause_text.lower()

                    if(not content.startswith("se")):
                        results["conform"] = False
                        results["syntax_conform"] = False

                        results["error_messages"].append(italian_subordinate_clause_conditional_error_message.format(type=sentence_type, sentence_text=sentence_text, subordinate_clause_text=subordinate_clause_text, subordinate_clause_function=subordinate_clause_function))

    return results

# --- english

# Eval template
english_eval_template = {
    "conform": True,
    "nouns_conform": True,
    "pronouns_conform": True,
    "adjectives_conform": True,
    "verbs_conform": True,
    "error_messages": []
}

english_allowed_pronouns = [ "personal", "possessive", "interrogative", "demonstrative" ]
english_allowed_interrogative_pronouns = [ "who", "what", "which" ]
english_allowed_adjectives = [ "descriptive", "interrogative", "possessive"]
english_allowed_modals = [ "can", "will" ]

# here we use the mood as key to simplify checks
english_allowed_finite_conj = {
    "indicative": [('present', 'simple'), ('present', 'perfect'), ('present', 'continous'), ('past', 'simple'), ('past', 'continous')],
    "imperative": []
}

english_allowed_passive_voice_conj = {
    "indicative": [('present', 'simple'), ('past', 'simple')]
}

english_noun_irregular_error_message = "The noun '{text}' has an irregular plural form, which is not allowed according to the A1 inventory noun specs."
english_pronoun_category_error = "The pronoun '{text}' belongs to the '{kind}' category. This pronoun category does not belong to the A1 inventory."
english_pronoun_interrogative_error = "The pronoun '{text}' is an interrogative pronoun, however only 'who', 'what' and 'which' are allowed according to the A1 inventory pronoun specs."
english_adjective_irregular_error = "The adjective '{text}', with 'degree' = '{degree}', is an irregular adjective. This is not allowed according to the A1 inventory adjective specs."
english_adjective_category_error = "The adjective '{text}' has a function outside of the A1 inventory allowed set ('descriptive', 'interrogative', 'possessive')."
english_finite_conj_error = "The verb '{text}' is conjugated in a mood x tense x aspect combination outside of the A1 verbs specs."
english_finite_voice_error = "The verb '{text}' is in 'voice' = '{voice}', however its mood x tense x aspect combination is not allowed in passive voice, according to the A1 inventory."
english_modal_verb_error = "The verb '{text}', includes the modal '{auxiliary}'. This is not one of the allowed A1 inventory modal verbs."

def parse_english_analysis(input: dict, check_syntax: bool = False) -> dict:
    results = copy.deepcopy(english_eval_template)
    """Given a text analysis report, performs a
    rule-based evaluation to check if the english A1
    invetory constraints are satisfied."""

    # --- grammar
    # check nouns
    for noun in input["nouns"]:
        text = noun["text"].lower()
        number = noun["number"].lower()
        possessive = noun["possessive"]
        regular = noun["regular"]

        # 1 - check if noun is plural + irregular
        if (number == "plural" and (not regular)):
            results["conform"] = False
            results["nouns_conform"] = False

            results["error_messages"].append(english_noun_irregular_error_message.format(text = text))

    # check pronouns
    for pronoun in input["pronouns"]:
        text = pronoun["text"].lower()
        kind = pronoun["kind"].lower()

        # 1 - check if pronoun category is allowed
        if (kind not in english_allowed_pronouns):
            results["conform"] = False
            results["pronouns_conform"] = False

            results["error_messages"].append(english_pronoun_category_error.format(text = text, kind = kind))

        # 2 - check if interrogative pronoun is within allowed list
        if (kind == "interrogative" and (text not in english_allowed_interrogative_pronouns)):
            results["conform"] = False
            results["pronouns_conform"] = False

            results["error_messages"].append(english_pronoun_interrogative_error.format(text = text))
    
    # check adjectives
    for adjective in input["adjectives"]:
        text = adjective["text"].lower()
        function = adjective["function"].lower()

        # 1 - check if function is within allowed categories
        if (function not in english_allowed_adjectives):
            results["conform"] = False
            results["adjectives_conform"] = False

            results["error_messages"].append(english_adjective_category_error.format(text = text))
        
        # 2 - if function is descriptive, also check degree and regularity
        if (function == "descriptive"):

            degree = adjective["degree"].lower()
            regular = adjective["regular"]

            if (not regular and (degree != "positive")):
                results["conform"] = False
                results["adjectives_conform"] = False

                results["error_messages"].append(english_adjective_irregular_error.format(text = text, degree = degree))


    # check verbs
    for verb in input["verbs"]:
        text = verb["text"].lower()
        lemma = verb["lemma"].lower()
        modal = verb["modal"]
        finite = verb["finite"]

        # 1 - Check modal verbs
        if (modal):

            auxiliary = verb.get("auxiliary")
            auxiliary = lemma if auxiliary is None else auxiliary.lower()

            if (auxiliary not in english_allowed_modals):
                results["conform"] = False
                results["verbs_conform"] = False

                results["error_messages"].append(english_modal_verb_error.format(text = text, auxiliary=auxiliary))
        
        # 2 - finite verbs forms
        if (finite):

            voice = verb["voice"].lower()
            mood = verb["mood"].lower()
            tense = verb.get("tense")
            aspect = verb.get("aspect")

            # 2A - Conj
            if (mood in english_allowed_finite_conj.keys()):
                if(not mood == "imperative"):
                    if(not ((tense, aspect) in set(english_allowed_finite_conj[mood]))):
                        results["conform"] = False
                        results["verbs_conform"] = False

                        results["error_messages"].append(english_finite_conj_error.format(text = text))
            else:
                results["conform"] = False
                results["verbs_conform"] = False

                results["error_messages"].append(english_finite_conj_error.format(text = text))


            # 2B - Voice
            if (voice == "passive"):
                if (mood in english_allowed_passive_voice_conj.keys()):
                    if (not((tense, aspect) in set(english_allowed_passive_voice_conj[mood]))):
                        results["conform"] = False
                        results["verbs_conform"] = False

                        results["error_messages"].append(english_finite_voice_error.format(text = text, voice=voice))
                
                else:
                    results["conform"] = False
                    results["verbs_conform"] = False

                    results["error_messages"].append(english_finite_voice_error.format(text = text, voice=voice))

    # --- syntax
    if (check_syntax):
        pass

    return results