import copy, re
from functools import partial
from langchain_core.messages import AIMessage
from pos_tagger import POSTagger, Language, TAGMethod

# Eval template
italian_eval_report = {
    "conform": True,
    "pronouns_conform": True,
    "numbers_conform": True,
    "verbs_conform": True,
    "syntax_conform": True,
    "error_messages": []
}

# Mega list of Italian irregular verbs
# Source - Wikipedia
irregular_verbs = [
    "accendere", "incendere", "raccendere", "riaccendere",
    "accludere", "concludere", "escludere", "includere", "intercludere", "occludere", "precludere", "recludere", "sconcludere",
    "accorgersi", "raccorgersi", "scorgere",
    "addurre", "abdurre", "circondurre", "condurre", "coprodurre", "dedurre", "edurre", "indurre", "introdurre", "manodurre", "perdurre", "prededurre", "produrre", "raddurre", "reintrodurre", "ricondurre", "ridurre", "riprodurre", "ritradurre", "sedurre", "soddurre", "tradurre", "trasdurre",
    "adempiere", "compire",
    "affliggere", "infliggere", "confliggere",
    "algere",
    "alludere", "colludere", "deludere", "disilludere", "eludere", "illudere", "interludere", "preludere", "proludere",
    "ancidere", "circoncidere", "coincidere", "decidere", "escidere", "incidere", "intercidere", "precidere", "recidere", "reincidere", "succidere", "uccidere",
    "andare", "oltrandare", "riandare", "trasandare",
    "annettere", "connettere", "disconnettere", "interconnettere", "riannettere", "riconnettere", "sconnettere",
    "apparire", "comparire", "disapparire", "disparire", "rapparire", "ricomparire", "riapparire", "trasparire", "scomparire",
    "appendere", "dipendere", "dispendere", "impendere", "propendere", "riappendere", "sopraspendere", "sospendere", "spendere", "vilipendere",
    "aprire", "riaprire", "semiaprire",
    "ardere", "riardere",
    "arrogere",
    "ascondere", "disascondere", "nascondere",
    "assidere",
    "assistere", "coesistere", "consistere", "desistere", "esistere", "inesistere", "insistere", "preesistere", "persistere", "resistere", "servoassistere", "sussistere",
    "assolvere", "asciolvere", "dissolvere", "risolvere",
    "assurgere", "consurgere",
    "avellere", "convellere",
    "avere", "riavere",
    "avertere", "controvertere", "estrovertere", "introvertere",
    "bere", "ribere", "strabere", "trabere",
    "cadere", "accadere", "decadere", "discadere", "ricadere", "scadere",
    "calere",
    "cernere", "decernere", "discernere", "ricernere", "scernere", "secernere",
    "chiedere", "dischiedere", "inchiedere", "richiedere",
    "chiudere", "acchiudere", "conchiudere", "dischiudere", "inchiudere", "racchiudere", "richiudere", "rinchiudere", "schiudere", "socchiudere",
    "cingere", "accingere", "discingere", "incingere", "precingere", "recingere", "ricingere", "scingere", "succingere",
    "cogliere", "accogliere", "incogliere", "raccogliere", "ricogliere",
    "comburere",
    "comprimere", "decomprimere", "deprimere", "dereprimere", "esprimere", "imprimere", "opprimere", "precomprimere", "reimprimere", "reprimere", "ricomprimere", "rimprimere", "sopprimere",
    "concedere", "succedere", "retrocedere",
    "conoscere", "anticonoscere", "disconoscere", "misconoscere", "preconoscere", "riconoscere", "sconoscere",
    "conquidere",
    "contessere", "intessere",
    "contundere", "ottundere",
    "convergere", "divergere",
    "convertire", "invertire",
    "coprire", "discoprire", "ricoprire", "riscoprire", "scoprire",
    "correre", "accorrere", "concorrere", "cooccorrere", "decorrere", "discorrere", "incorrere", "intercorrere", "occorrere", "percorrere", "precorrere", "ricorrere", "rincorrere", "ripercorrere", "scorrere", "soccorrere", "trascorrere",
    "crescere", "accrescere", "concrescere", "decrescere", "discrescere", "increscere", "ricrescere", "rincrescere", "screscere", "sopraccrescere",
    "cucire", "discucire", "ricucire", "scucire", "sdrucire",
    "cuocere", "concuocere", "decuocere", "incuocere", "ricuocere", "scuocere", "stracuocere",
    "dare", "disdare", "ridare", "sdare",
    "delinquere",
    "devolvere", "evolvere", "involvere",
    "detrudere", "estrudere", "intrudere", "protrudere",
    "difendere", "offendere",
    "diligere", "prediligere", "negligere",
    "dipingere", "dispingere", "ridipingere", "sdipingere",
    "dire", "addire", "benedire", "contraddire", "disdire", "indire", "interdire", "maledire", "predire", "ridire", "sdire", "sopraddire", "stradire",
    "dirigere", "condirigere", "erigere", "indirigere", "ridirigere",
    "discutere", "incutere", "escutere",
    "distinguere", "contraddistinguere", "estinguere", "suddistinguere",
    "dividere", "condividere", "ridividere", "suddividere",
    "dolere", "condolere", "sdolere",
    "dovere", "ridovere",
    "eccellere", "sovreccellere",
    "elidere", "allidere", "collidere",
    "empire", "riempire", "sovrempire",
    "ergere", "adergere",
    "esigere", "transigere",
    "esimere",
    "espellere", "impellere", "propellere", "repellere",
    "essere", "riessere",
    "evadere", "invadere", "pervadere",
    "fare", "affarsi", "artefare", "assuefare", "benfare", "confarsi", "consuefare", "contraffare", "disfare", "dissuefare", "forfare", "liquefare", "malfare", "mansuefare", "misfare", "prefare", "putrefare", "rarefare", "rifare", "satisfare", "sfare", "soddisfare", "sopraffare", "strafare", "stupefare", "tepefare", "torrefare", "tumefare",
    "fedire",
    "figgere", "affiggere", "configgere", "crocifiggere", "defiggere", "disconfiggere", "infiggere", "prefiggere", "rifiggere", "scalfiggere", "sconfiggere", "scrocifiggere", "suffiggere", "trafiggere",
    "fingere", "confingere", "diffingere", "effingere", "infingere",
    "flettere", "circonflettere", "deflettere", "estroflettere", "inflettere", "introflettere", "riflettere",
    "fondere", "circonfondere", "confondere", "diffondere", "effondere", "infondere", "perfondere", "profondere", "radiodiffondere", "reinfondere", "rifondere", "sconfondere", "soffondere", "trasfondere", "telediffondere",
    "frangere", "affrangere", "diffrangere", "infrangere", "rifrangere", "rinfrangere", "sfrangere",
    "friggere", "rifriggere", "sfriggere", "soffriggere",
    "fulgere", "circonfulgere", "rifulgere",
    "fungere", "defungere",
    "giacere", "soggiacere",
    "giungere", "aggiungere", "congiungere", "disgiungere", "ingiungere", "raggiungere", "ricongiungere", "scongiungere", "soggiungere", "sopraggiungere", "sorgiungere",
    "godere", "sgodere", "stragodere",
    "indulgere",
    "inferire", "profferire",
    "intridere",
    "leggere", "eleggere", "intraleggere", "preeleggere", "rieleggere", "rileggere",
    "mettere", "ammettere", "commettere", "compromettere", "dimettere", "discommettere", "dismettere", "dispromettere", "fedecommettere", "emettere", "estromettere", "frammettere", "immettere", "impromettere", "inframmettere", "intermettere", "intramettere", "intromettere", "malmettere", "manomettere", "omettere", "permettere", "premettere", "pretermettere", "promettere", "radiostrasmettere", "reimmettere", "ricetrasmettere", "riammettere", "ricommettere", "rimettere", "riemettere", "ripromettere", "scommettere", "smettere", "sommettere", "soprammettere", "sottomettere", "spromettere", "teletrasmettere", "tramettere", "trasmettere", "videotrasmettere",
    "mergere", "emergere", "immergere", "reimmergere", "riemergere", "rimmergere", "sommergere",
    "mingere",
    "mordere", "demordere", "rimordere",
    "morire", "premorire", "rimorire", "smorire",
    "muovere", "commuovere", "dismuovere", "permuovere", "promuovere", "rimuovere", "scommuovere", "smuovere", "sommuovere",
    "nascere", "prenascere", "rinascere",
    "nuocere",
    "offrire", "controffrire", "soffrire",
    "parere",
    "percuotere", "ripercuotere", "riscuotere", "scuotere",
    "perdere", "disperdere", "sperdere",
    "piacere", "compiacere", "dispiacere", "scompiacere", "spiacere",
    "piangere", "compiangere", "rimpiangere",
    "piovere", "ripiovere", "spiovere",
    "polluire",
    "porgere", "sporgere",
    "porre", "anteporre", "apporre", "bendisporre", "comporre", "contrapporre", "controproporre", "decomporre", "deporre", "discomporre", "disimporre", "disporre", "esporre", "fotocomporre", "frapporre", "giustapporre", "imporre", "indisporre", "infrapporre", "interporre", "opporre", "ovodeporre", "posporre", "predisporre", "preporre", "presupporre", "proporre", "reimporre", "ricomporre", "riporre", "riproporre", "scomporre", "sottoesporre", "sottoporre", "sovrapporre", "sovresporre", "sporre", "sovrimporre", "supporre", "traporre", "trasporre",
    "potere",
    "prendere", "apprendere", "comprendere", "disapprendere", "imprendere", "intraprendere", "rapprendere", "riprendere", "sorprendere",
    "proteggere", "sproteggere",
    "pungere", "compungere", "espungere", "interpungere", "trapungere",
    "radere", "abradere", "erodere",
    "redigere",
    "redimere",
    "relinquere",
    "reggere", "correggere", "sorreggere",
    "rendere", "arrendere",
    "ridere", "arridere", "deridere", "irridere", "sorridere",
    "rimanere", "permanere",
    "rispondere", "corrispondere",
    "rodere", "corrodere", "erodere",
    "rompere", "corrompere", "dirompere", "erompere", "interrompere", "irrompere", "prorompere",
    "salire", "assalire", "risalire", "soprassalire",
    "sapere", "consapere", "risapere", "strasapere",
    "scegliere", "prescegliere", "trascegliere",
    "scendere", "accondiscendere", "ascendere", "condiscendere", "conscendere", "discendere", "disconscendere", "ridiscendere", "saliscendere", "scoscendere", "trascendere",
    "scindere", "discindere", "piroscindere", "prescindere", "rescindere",
    "sciogliere", "disciogliere", "prosciogliere", "risciogliere",
    "scrivere", "ascrivere", "circoscrivere", "coscrivere", "dattiloscrivere", "descrivere", "inscrivere", "iscrivere", "manoscrivere", "poscrivere", "preiscrivere", "prescrivere", "proscrivere", "reinscrivere", "riscrivere", "soprascrivere", "sottoscrivere", "soscrivere", "trascrivere", "videoscrivere",
    "sedere", "compossedere", "possedere", "presedere", "risedere", "soprassedere", "spossedere",
    "seppellire", "disseppellire",
    "solere",
    "sentire", "acconsentire", "assentire", "consentire", "disconsentire", "dissentire", "intrasentire", "presentire", "riconsentire", "risentire", "sconsentire", "soprasentire", "trasentire",
    "solvere", "dissolvere",
    "sorgere", "assorgere", "insorgere", "reinsorgere", "risorgere",
    "spergere", "aspergere", "cospergere", "dispergere",
    "spandere", "espandere",
    "spargere", "dispargere", "cospargere", "espargere",
    "sparire", "risparire",
    "spegnere", "dispegnere",
    "spingere", "respingere", "retrospingere", "risospingere", "rispingere", "sospingere",
    "stare", "antistare", "ristare", "soprastare", "sottostare",
    "stringere", "astringere", "costringere", "distringere", "restringere", "ristringere",
    "struggere", "distruggere",
    "suadere", "dissuadere", "persuadere",
    "sumere", "assumere", "consumere", "desumere", "presumere", "rassumere", "riassumere", "sussumere",
    "tacere", "sottacere",
    "tendere", "attendere", "contendere", "disattendere", "disintendere", "distendere", "estendere", "fraintendere", "intendere", "malintendere", "ostendere", "pretendere", "protendere", "prostendere", "riattendere", "soprintendere", "sottendere", "sottintendere", "stendere",
    "tenere", "appartenere", "astenere", "attenere", "contenere", "detenere", "distenere", "intertenere", "intrattenere", "mantenere", "manutenere", "ottenere", "pertenere", "rattenere", "riottenere", "ritenere", "soprattenere", "sostenere", "trattenere",
    "tergere", "astergere", "detergere",
    "tingere", "attingere", "contingere", "intingere", "sovratingere", "stingere",
    "togliere", "distogliere", "ritogliere", "stogliere",
    "torcere", "attorcere", "contorcere", "detorcere", "distorcere", "estorcere", "intorcere", "rattorcere", "ritorcere", "scontorcere", "storcere",
    "trarre", "astrarre", "attrarre", "contrarre", "decontrarre", "detrare", "distrarre", "estrarre", "protrarre", "rattrarre", "retrarre", "ricontrarre", "ritrarre", "sottrarre",
    "udire", "intraudire", "riudire", "traudire",
    "ungere", "disungere", "riungere",
    "uscire", "fuoriuscire", "riuscire",
    "valere", "avvalersi", "contravvalere", "disvalere", "equivalere", "invalere", "prevalere", "rivalersi",
    "vedere", "antivedere", "avvedersi", "disvedere", "divedere", "intravedere", "malvedere", "prevedere", "provvedere", "ravvedersi", "rivedere", "sopravvedere", "sprovvedere", "stravedere", "travedere",
    "vellere", "disvellere", "divellere", "svellere",
    "venire", "addivenire", "antivenire", "avvenire", "circonvenire", "contravvenire", "convenire", "devenire", "disavvenire", "disconvenire", "disvenire", "divenire", "intervenire", "intravvenire", "misvenire", "pervenire", "prevenire", "provenire", "riconvenire", "rinvenire", "risovvenire", "rivenire", "sconvenire", "sopravvenire", "sorvenire", "sovvenire", "svenire",
    "vincere", "avvincere", "convincere", "evincere", "rivincere", "sopravvincere", "stravincere",
    "vivere", "convivere", "rivivere", "sopravvivere",
    "volere", "benvolere", "disvolere", "malvolere", "rivolere", "stravolere", "svolere",
    "volgere", "avvolgere", "capovolgere", "circonvolgere", "coinvolgere", "convolgere", "disinvolgere", "disvolgere", "involgere", "ravvolgere", "riavvolgere", "rinvolgere", "rivolgere", "sconvolgere", "stravolgere", "svolgere", "travolgere"
]
allowed_irregular_verbs = ["essere", "esserci", "avere", "averci", "volere", "volerci", "potere", "potersi", "dovere", "doversi"]
not_allowed_verbs = list(set(irregular_verbs).difference(set(allowed_irregular_verbs)))

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
        if (lemma in set(not_allowed_verbs)):
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


def regex_message_parser(message: AIMessage, regex: str) -> str | None:
    """Given a langchain AIMessage and a
    regular expression, tries to find matches
    in the model's reponse, then if any are found
    return the first matching group"""
    message_content = message.content

    match = re.search(fr"{regex}", message_content)

    if match:
        return match.group(1)
    else:
        return None

def regex_parser(regex: str) -> partial[str]:
    """Partial regex_message_parser application.
    Can be chained with a langchain llm invoke sequence"""
    return partial(regex_message_parser, regex=regex)

def strip_string(input: str) -> str:
    """Takes a string as input. Uses regular
    expressions to remove traling and leading white
    spaces + substitutes any newline sequence with
    a (1) white space. Returns the transformed text"""
    transformed = input
    transformed = re.sub(r'^\s*', '', transformed)
    transformed = re.sub(r'\s*$', '', transformed)
    transformed = re.sub(r' +', ' ',transformed)
    transformed = re.sub(r'\n+', ' ',transformed)

    return transformed