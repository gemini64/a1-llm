upos_to_simple = {
    "NOUN": "n",
    "PROPN": "propn",
    "VERB": "v",
    "AUX": "v",
    "ADJ": "a",
    "ADV": "r",
    "ADP": "p",
    "DET": "d",
    "CCONJ": "c",
    "SCONJ": "c",
    "PRON": "pron",
    "NUM": "num",
    "INTJ": "i",
    "PUNCT": "punct",
    "SYM": "sym",
    "X": "x",
    "PART": "part"
}

oxford_to_simple = {
    "adj.": "a", # adjective -> a
    "adv.": "r", # adverb -> r
    "auxiliary v.": "v", # auxiliary verb -> v
    "conj.": "c", # conjunction -> c
    "definite article": "d", # definite article -> d (determiner)
    "det.": "d", # determiner -> d
    "exclam.": "i", # exclamation -> i (interjection)
    "indefinite article": "d", # indefinite article -> d (determiner)
    "infinitive marker": "part", # infinitive marker -> part (particle)
    "modal v.": "v", # modal verb -> v
    "n.": "n", # noun -> n
    "number": "num", # number -> num
    "prep.": "p", # preposition -> p
    "pron.": "pron", # pronoun -> pron
    "v.": "v" # verb -> v
}

perugia_to_simple = {
    "agg.": "a", # aggettivo -> a (adjective)
    "art.": "d", # articolo -> d (determiner)
    "avv.": "r", # avverbio -> r (adverb)
    "cong.": "c", # congiunzione -> c (conjunction)
    "inter.": "i", # interiezione -> i (interjection)
    "locuz.": "x", # locuzione -> x (other/miscellaneous)
    "part.pron.": "pron", # particella pronominale -> pron (pronoun)
    "part.pron.luogo": "r", # particella pronominale di luogo -> r (adverb)
    "prep.": "p", # preposizione -> p (preposition)
    "pron.": "pron", # pronome -> pron (pronoun)
    "s.f.": "n", # sostantivo femminile -> n (noun)
    "s.m.": "n", # sostantivo maschile -> n (noun)
    "s.m.pl.": "n", # sostantivo maschile plurale -> n (noun)
    "v.int.": "v", # verbo intransitivo -> v (verb)
    "v.int.pron.": "v", # verbo intransitivo pronominale -> v (verb)
    "v.rifl.": "v", # verbo riflessivo -> v (verb)
    "v.rifl.recip.": "v", # verbo riflessivo reciproco -> v (verb)
    "v.t.": "v", # verbo transitivo -> v (verb)
    "v.t.pron.": "v" # verbo transitivo pronominale -> v (verb)
}