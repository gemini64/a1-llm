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
# Source - Wikitionary
irregular_verbs = ["abdurre", "abradere", "accadere", "accendere", "accendersi", "acchiudere", "accidere", "accignere", "accingere", "accingersi", "accludere", "accogliere", "accogliersi", "accommettere", "accondiscendere", "acconfarsi", "acconsentire", "accorgersi", "accorre", "accorrere", "accrescere", "accrescersi", "addarsi", "addire", "addirsi", "addivenire", "addurre", "addursi", "adempiere", "adempiersi", "adempire", "adergere", "affarsi", "affiggere", "affliggere", "affliggersi", "affrangere", "aggiungere", "aggiungersi", "aggredire", "algere", "allidere", "alludere", "ammettere", "ammollire", "ancidere", "andarci", "andare", "andarne", "andarsene", "andarsi", "annettere", "annettersi", "anteporre", "anticonoscere", "antistare", "antivedere", "antivenire", "apparire", "appartenere", "appendere", "appendersi", "appercepire", "applaudere", "apporre", "apprendere", "aprire", "aprirsi", "ardere", "arrendere", "arrendersi", "arridere", "arrogere", "artefare", "ascendere", "asciolvere", "ascondere", "ascondersi", "ascrivere", "ascriversi", "aspergere", "assalire", "assentire", "asserire", "assidere", "assidersi", "assistere", "assistersi", "assolvere", "assolversi", "assorbere", "assorbire", "assorgere", "assuefare", "assuefarsi", "assumere", "assumersi", "assurgere", "astenere", "astenersi", "astergere", "astraere", "astraggere", "astrarre", "astrarsi", "astrignere", "astringere", "attendere", "attendersi", "attenere", "attenersi", "attingere", "attingersi", "attorcere", "attrarre", "attrarsi", "autoadempiersi", "autoassolversi", "autocontraddirsi", "autocontrarsi", "autoconvincersi", "autodistruggere", "autodistruggersi", "autoescludersi", "autoimporsi", "autoinfliggersi", "autoprodurre", "autopromuoversi", "autoproteggersi", "autoridurre", "autosospendersi", "autosostenere", "autosostenersi", "avellere", "avercela", "avere", "averla", "aversela", "avincere", "avvalersi", "avvedersi", "avvenire", "avvilire", "avvilirsi", "avvincere", "avvincersi", "avvolgere", "avvolgersi", "bendisporre", "benedicere", "benedire", "benefare", "bere", "bersela", "bersi", "bevere", "biscuocere", "blandire", "cadere", "calere", "capire", "capirsi", "capivolgere", "capovolgere", "capovolgersi", "cedere", "cernere", "cherere", "chiedere", "chiedersi", "chierere", "chiudere", "chiudersi", "cingere", "circoncidere", "circoncidersi", "circoncingere", "circondurre", "circonflettere", "circonfondere", "circonfulgere", "circonscrivere", "circonvenire", "circonvolgere", "circoscrivere", "circumcingere", "codecidere", "coesistere", "cogliere", "cognoscere", "coincidere", "coinvolgere", "collidere", "colludere", "comburere", "commettere", "commuovere", "commuoversi", "comparire", "compiacere", "compiacersi", "compiangere", "compiangersi", "compiere", "compiersi", "compire", "comporre", "comporsi", "comprendere", "comprendersi", "comprimere", "compromettere", "compromettersi", "compungere", "compungersi", "concedere", "concedersi", "concepire", "concepirsi", "conchiudere", "concludere", "concludersi", "concorrere", "concrescere", "concuocere", "concupire", "condescendere", "condiscendere", "condividere", "condolersi", "conducere", "condurre", "condursi", "confarsi", "configgere", "confingere", "confliggere", "confondere", "confondersi", "congiungere", "congiungersi", "connettere", "connettersi", "conoscere", "conoscersi", "consentire", "consentirsi", "consistere", "conspargere", "conspergere", "constringere", "construire", "consumere", "contendere", "contendersi", "contenere", "contenersi", "contorcere", "contorcersi", "contraddire", "contraddirsi", "contraddistinguere", "contraddistinguersi", "contradire", "contraffare", "contraffarsi", "contrapporre", "contrapporsi", "contrarre", "contrarsi", "contrastare", "contravvalere", "contravvenire", "controproporre", "controrispondere", "controvertere", "contundere", "convenire", "convenirsi", "convergere", "convertire", "convertirsi", "convincere", "convincersi", "convivere", "convolgere", "coprire", "coprirsi", "coprodurre", "correggere", "correggersi", "corrercene", "correre", "corrersi", "corrispondere", "corrispondersi", "corrodere", "corrodersi", "corrompere", "corrompersi", "coscrivere", "cospargere", "cospargersi", "cospergere", "costituire", "costituirsi", "costringere", "costringersi", "costruire", "costruirsi", "crescere", "crocefiggere", "crocifiggere", "crocifiggersi", "crucifiggere", "cucire", "cucirsi", "cuocere", "dare", "darsi", "dattiloscrivere", "decadere", "decernere", "decidere", "decidersi", "decomporre", "decomporsi", "decomprimere", "decontrarre", "decontrarsi", "decorrere", "decrescere", "decuocere", "dedurre", "dedursi", "defiggere", "deflettere", "defungere", "delinquere", "deludere", "deludersi", "demergere", "demordere", "depellere", "depingere", "deporre", "deprimere", "deprimersi", "deridere", "descrivere", "descriversi", "desistere", "destituire", "destruggere", "desumere", "detenere", "detergere", "detorcere", "detrarre", "detrudere", "devenire", "devolvere", "dicere", "difendere", "difendersi", "diffondere", "diffondersi", "diffrangere", "diffrangersi", "digerire", "digiungere", "diligere", "dimettere", "dimettersi", "dimungere", "dipendere", "dipingere", "dipingersi", "diporre", "dire", "direggere", "dirigere", "dirigersi", "dirompere", "dirsi", "disapprendere", "disascondere", "disassuefare", "disassuefarsi", "disattendere", "discadere", "discendere", "discernere", "dischiedere", "dischiudere", "discingere", "disciogliere", "disciogliersi", "discommettere", "discomporre", "disconcludere", "disconfiggere", "discongiungere", "disconnettere", "disconnettersi", "disconoscere", "disconvenire", "discoprire", "discorrere", "discoscendere", "discrescere", "discrivere", "discucire", "discutere", "disdire", "disdirsi", "disfare", "disfarsi", "disgiungere", "disilludere", "disilludersi", "disimprimere", "disintendere", "disinvolgere", "dismettere", "disobbedire", "dispargere", "disparire", "dispegnere", "dispendere", "disperdere", "disperdersi", "dispergere", "dispiacere", "dispiacersi", "dispingere", "disporre", "disporsi", "dispromettere", "disrompere", "dissentire", "disseppellire", "dissolvere", "dissolversi", "dissuadere", "distare", "distendere", "distendersi", "distinguere", "distinguersi", "distogliere", "distogliersi", "distorcere", "distorcersi", "distraggere", "distrarre", "distrarsi", "distringere", "distruggere", "distruggersi", "disubbidire", "disvalere", "disvedere", "disvellere", "disverre", "disvolere", "disvolgere", "divellere", "divenire", "divergere", "dividere", "dividersi", "divolgere", "dolere", "dolersi", "dormirci", "dormire", "dormirsela", "dovere", "ducere", "-durre", "eccellere", "educere", "edurre", "effingere", "effondere", "effondersi", "eleggere", "elidere", "elidersi", "eludere", "emergere", "emettere", "empiere", "empire", "emungere", "equidistare", "equivalere", "eradere", "ereggere", "ergere", "ergersi", "erigere", "erigersi", "erodere", "erompere", "erudire", "erudirsi", "esaudire", "esaurire", "esaurirsi", "escludere", "escludersi", "escuotere", "escutere", "esigere", "esistere", "esordire", "espandere", "espandersi", "espargere", "espellere", "esperire", "esplodere", "esporre", "esporsi", "esprimere", "esprimersi", "espungere", "esserci", "essere", "esservi", "estendere", "estendersi", "estinguere", "estinguersi", "estorcere", "estrarre", "estromettere", "estromettersi", "estrudere", "evadere", "evellere", "evincere", "evolvere", "evolversi", "farcela", "fare", "fargliela", "farla", "farsela", "farsene", "farsi", "fedecommettere", "fedire", "fendere", "fendersi", "ferire", "ferirsi", "fidecommettere", "figgere", "fingere", "fingersi", "fire", "flettere", "flettersi", "fondere", "fondersi", "fotocomporre", "fraintendere", "fraintendersi", "framettere", "frammettere", "frammettersi", "frangere", "frapporre", "frapporsi", "friggere", "fuggire", "fulgere", "fungere", "fuoriuscire", "genuflettersi", "giacere", "gire", "girsene", "giungere", "giustapporre", "giustapporsi", "godere", "godersi", "guaire", "havere", "illudere", "illudersi", "imbevere", "imbeversi", "immergere", "immergersi", "immettere", "immettersi", "impedire", "impedirsi", "impellere", "impignere", "impingere", "implodere", "imporre", "imporsi", "imprendere", "imprimere", "imprimersi", "impromettere", "incendere", "inchiedere", "inchiudere", "incidere", "incingere", "includere", "incogliere", "incorrere", "increscere", "incuocere", "incutere", "indire", "indirigere", "indisporre", "indulgere", "indurre", "indursi", "inferire", "infiggere", "infingere", "inflettere", "infliggere", "infliggersi", "infondere", "inframettere", "inframmettere", "inframmettersi", "infrangere", "infrangersi", "infrapporre", "ingerire", "ingerirsi", "ingiungere", "inscrivere", "inserire", "insistere", "insorgere", "instituire", "intendere", "intendersela", "intendersene", "intendersi", "intercedere", "intercidere", "intercludere", "interconnettere", "interconnettersi", "intercorrere", "interdire", "intermettere", "interporre", "interporsi", "interpungere", "interrompere", "interrompersi", "intertenere", "intervenire", "intessersi", "intingere", "intramettere", "intraprendere", "intrattenere", "intrattenersi", "intravedere", "intravedersi", "intravenire", "intravvedere", "intravvenire", "intridere", "introdurre", "introdursi", "introflettersi", "intromettere", "intromettersi", "introvertere", "introvertersi", "intrudere", "invadere", "invalere", "invenire", "invertire", "involgere", "ire", "irridere", "irrompere", "iscrivere", "iscriversi", "lecere", "ledere", "leggere", "leggersi", "lenire", "licere", "liquefare", "liquefarsi", "lucere", "maladire", "maledire", "maledirsi", "malfare", "malmettere", "malvedere", "manicare", "manimettere", "manomettere", "manoscrivere", "mansuefare", "mansuefarsi", "mantenere", "mantenersi", "manutenere", "marimettere", "mergere", "metterci", "mettere", "mettersi", "mingere", "misconoscere", "misfare", "misprendere", "molcere", "mordere", "mordersi", "morire", "morirsene", "morirsi", "muggire", "mungere", "munire", "munirsi", "muovere", "muoversi", "nascere", "nascondere", "nascondersi", "negligere", "nuocere", "nutrire", "nutrirsene", "nutrirsi", "obbedire", "occidere", "occludere", "occorrere", "offendere", "offendersi", "offerire", "offrire", "offrirsi", "omettere", "ommettere", "opporre", "opporsi", "opprimere", "ossedere", "ottenere", "ottundere", "ovideporre", "parere", "partenere", "partorire", "percepire", "percorrere", "percotere", "percuotere", "percuotersi", "perdere", "perdersi", "perdurre", "perfare", "permanere", "permettere", "permettersi", "perplimere", "perseguire", "persistere", "persuadere", "persuadersi", "pertenere", "pervadere", "pervenire", "pervertire", "pervertirsi", "piacere", "piacersi", "piangere", "piangersi", "pignere", "pingere", "piovere", "piroscindere", "plangere", "plaudere", "porgere", "porre", "porsi", "portendere", "posporre", "possedere", "potere", "precedere", "precidere", "precingere", "precludere", "precludersi", "precognoscere", "precomprimere", "preconoscere", "precorrere", "prediligere", "predire", "predisporre", "predisporsi", "preeleggere", "preesistere", "prefare", "prefiggere", "prefiggersi", "preintendere", "preludere", "premere", "premettere", "premorire", "premunire", "premunirsi", "prenascere", "prenderci", "prendere", "prenderle", "prendersela", "prendersi", "preporre", "prepotere", "presapere", "prescegliere", "prescindere", "prescrivere", "prescriversi", "presedere", "presentire", "presumere", "presummere", "presupporre", "pretendere", "pretermettere", "pretessere", "prevalere", "prevedere", "prevenire", "procedere", "produrre", "prodursi", "profferire", "profondere", "profondersi", "progredire", "proludere", "promettere", "promettersi", "promuovere", "propellere", "propendere", "proporre", "proporsi", "prorompere", "prosciogliere", "proscrivere", "prostendere", "prosumere", "proteggere", "proteggersi", "protendere", "protendersi", "protrarre", "protrarsi", "protrudere", "provedere", "provenire", "provvedere", "provvedersi", "pungere", "pungersi", "punire", "punirsi", "putrefare", "putrefarsi", "putrire", "raccendere", "racchiudere", "racchiudersi", "raccogliere", "raccogliersi", "raccorgersi", "raddurre", "raddursi", "radere", "radersi", "radioassistere", "radiodiffondere", "radiotrasmettere", "raggiungere", "raggiungersi", "rapire", "rapprendere", "rapprendersi", "rarefare", "rarefarsi", "rassumere", "rattenere", "rattorcere", "rattrarre", "ravvedersi", "ravvolgere", "ravvolgersi", "reassumere", "recidere", "recidersi", "recingere", "recludere", "redigere", "redimere", "redimersi", "redire", "reducere", "redurre", "reflettere", "refrangere", "refulgere", "reggere", "reggersi", "regredire", "reimmergere", "reimmergersi", "reimmettere", "reimprimere", "reincidere", "reinscrivere", "reinsorgere", "reintervenire", "reintrodurre", "reintrodursi", "relinquere", "rendere", "rendersi", "repellere", "reperire", "reporre", "reprimere", "reprimersi", "rescindere", "resistere", "resolvere", "respingere", "respingersi", "respondere", "restringere", "restringersi", "resumere", "resurgere", "retrarre", "retrocedere", "riaccadere", "riaccendere", "riaccendersi", "riaccogliere", "riaccrescere", "riaffiggere", "riammettere", "riandare", "riannettere", "riapparire", "riappendere", "riapprendere", "riaprire", "riaprirsi", "riardere", "riascendere", "riassalire", "riassidersi", "riassolvere", "riassuefare", "riassumere", "riassumersi", "riattendere", "riattingere", "riattorcere", "riattrarre", "riavere", "riaversi", "riavvincere", "riavvolgere", "riavvolgersi", "ribenedire", "ribere", "ricadere", "ricernere", "ricetrasmettere", "richerere", "richiedere", "richiudere", "richiudersi", "ricidere", "ricingere", "ricogliere", "ricommettere", "ricommuovere", "ricomparire", "ricompiere", "ricompire", "ricomporre", "ricomporsi", "ricomprendere", "ricomprimere", "ricompromettere", "riconcedere", "riconcepire", "riconcorrere", "riconducere", "ricondurre", "ricondursi", "riconfiggere", "riconfondere", "ricongiungere", "ricongiungersi", "riconnettere", "riconoscere", "riconoscersi", "riconsentire", "ricontraddire", "ricontraffare", "ricontrarre", "riconvenire", "riconvincere", "ricoprire", "ricoprirsi", "ricorreggere", "ricorrere", "ricospargere", "ricostringere", "ricovrire", "ricrescere", "ricrocifiggere", "ricucire", "ricuocere", "ridare", "ridarsi", "rideporre", "ridere", "ridersene", "ridersi", "ridescrivere", "ridifendere", "ridiffondere", "ridipingere", "ridire", "ridiscendere", "ridischiudere", "ridisciogliere", "ridiscorrere", "ridiscutere", "ridisfare", "ridisfarsi", "ridisporre", "ridistendere", "ridistinguere", "ridistogliere", "ridistruggere", "ridivenire", "ridividere", "ridolere", "ridormire", "ridovere", "riducere", "ridurre", "ridursi", "rieleggere", "riemergere", "riemettere", "riempiere", "riempire", "riempirsi", "riergere", "riescludere", "riespandere", "riespellere", "riesplodere", "riesporre", "riesprimere", "riessere", "riestendere", "riestinguere", "riestrarre", "rifare", "rifarsela", "rifarsi", "rifendere", "rifiggere", "riflettere", "riflettersi", "rifondere", "rifrangere", "rifrangersi", "rifriggere", "rifulgere", "rigiacere", "rigiungere", "rigodere", "rileggere", "rileggersi", "rilucere", "rimaledire", "rimanere", "rimanersi", "rimetterci", "rimettere", "rimettersi", "rimordere", "rimorire", "rimovere", "rimpiangere", "rimprimere", "rimuggire", "rimungere", "rimunire", "rimuovere", "rimuoversi", "rinascere", "rinascondere", "rinchiedere", "rinchiudere", "rinchiudersi", "rincingere", "rincorrere", "rincorrersi", "rincrescere", "rincrescersi", "rinfondere", "rinfrangere", "rintendere", "rintingere", "rintrodurre", "rinuocere", "rinvenire", "rinvenirsi", "rinvolgere", "rioffendere", "rioffrire", "riopporre", "riottenere", "ripercorrere", "ripercotere", "ripercuotere", "ripercuotersi", "riperdere", "ripiangere", "ripignere", "ripingere", "ripiovere", "riporgere", "riporre", "ripossedere", "ripotere", "riprendere", "riprendersi", "ripretendere", "riprodurre", "riprodursi", "ripromettere", "ripromettersi", "riproporre", "riproporsi", "riproteggere", "riprovedere", "riprovvedere", "ripungere", "rirendere", "rirompere", "risalire", "risapere", "riscegliere", "riscendere", "risciogliere", "riscommettere", "risconvolgere", "riscoprire", "riscorrere", "riscotere", "riscrivere", "riscuotere", "riscuotersi", "risdrucire", "risedere", "riseppellire", "risoggiungere", "risolvere", "risolversi", "risommergere", "risorgere", "risospendere", "risospingere", "risostenere", "risottomettere", "risovvenire", "risovvenirsi", "rispandere", "rispargere", "rispegnere", "rispendere", "rispergere", "rispingere", "rispondere", "rispondersi", "ristare", "ristendere", "ristringere", "ristringersi", "ristruggere", "risurgere", "risvenire", "risvolgere", "ritendere", "ritenere", "ritenersi", "ritergere", "ritessere", "ritingere", "ritogliere", "ritorcere", "ritorcersi", "ritradurre", "ritraggere", "ritrarre", "ritrarsi", "ritrascorrere", "ritrascrivere", "ritrasgredire", "ritrasmettere", "ritrasporre", "riudire", "riungere", "riuscire", "riuscirsene", "rivalersi", "rivedere", "rivedersi", "rivenire", "rivincere", "rivivere", "rivolere", "rivolgere", "rivolgersi", "rodere", "rodersi", "rompere", "rompersi", "saglire", "salire", "sapere", "sapersi", "satisfare", "scadere", "scalfiggere", "scegliere", "scegliersi", "scendere", "scernere", "schiudere", "schiudersi", "scignere", "scindere", "scindersi", "scingere", "sciogliere", "sciogliersi", "sciolvere", "sciorre", "scognoscere", "scommettere", "scommettersi", "scommuovere", "scomparire", "scompiacere", "scomponere", "scomporre", "scomporsi", "sconcludere", "sconfiggere", "sconfondere", "scongiungere", "sconnettere", "sconoscere", "sconsentire", "scontessere", "scontorcere", "sconvenire", "sconvolgere", "sconvolgersi", "scoprire", "scoprirsi", "scorgere", "scorreggere", "scorrere", "scoscendere", "scovrire", "screscere", "scrivere", "scriversi", "scucire", "sculpere", "scuocere", "scuotere", "scuotersi", "sdipingere", "sdire", "sdolere", "sdrucire", "sdrucirsi", "secernere", "sedere", "sedersi", "sedurre", "semicingere", "sentire", "sepellire", "seppellire", "seppellirsi", "servoassistere", "sfare", "sfarsi", "sfendere", "sfrangere", "sfrangersi", "sfriggere", "sgrillettarsi", "smettere", "smetterla", "smorire", "smovere", "smungere", "smuovere", "smuoversi", "socchiudere", "soccorrere", "soddisfare", "soddisfarsi", "sodisfare", "sofferere", "sofferire", "soffolcere", "soffolgere", "soffondere", "soffriggere", "soffrire", "soggiacere", "soggiungere", "solere", "solvere", "sommergere", "sommettere", "sommuovere", "soppellire", "soppendere", "sopporre", "sopprimere", "soprabbevere", "sopraccorrere", "sopraccrescere", "sopraffare", "sopraggiungere", "sopraintendere", "soprammettere", "soprantendere", "sopraporre", "soprapporre", "soprapprendere", "soprascrivere", "sopraspendere", "soprassapere", "soprassedere", "sopravincere", "sopravvedere", "sopravvenire", "sopravvincere", "sopravvivere", "soprintendere", "sorgere", "sorgiungere", "sorprendere", "sorprendersi", "sorradere", "sorreggere", "sorridere", "sorridersi", "sorvenire", "soscrivere", "sospendere", "sospignere", "sospingere", "sostenere", "sostenersi", "sottacere", "sottendere", "sottintendere", "sottodividere", "sottoesporre", "sottogiacere", "sottomettere", "sottomettersi", "sottoporre", "sottoporsi", "sottoridere", "sottoscrivere", "sottostare", "sottraggere", "sottrarre", "sottrarsi", "sovraesporre", "sovraggiungere", "sovraimporre", "sovraintendere", "sovrapporre", "sovrapporsi", "sovrascorrere", "sovrascrivere", "sovresporre", "sovrimporre", "sovrintendere", "sovvenire", "sovvolgere", "spandere", "spandersi", "spargere", "spargersi", "sparire", "spedire", "spedirsi", "spegnere", "spegnersi", "spendere", "spendersi", "spengere", "spengersi", "sperdere", "spergere", "spiacere", "spiacersi", "spingere", "spingersi", "spiovere", "splendere", "sporgere", "sporgersi", "sporre", "spossedere", "spromettere", "sproteggere", "sprovvedere", "stare", "starsene", "starsi", "stendere", "stendersi", "stingere", "stingersi", "stinguere", "stogliere", "storcere", "storcersi", "strabenedire", "strabere", "stracuocere", "strafare", "strafarsi", "stragodere", "stramaledire", "straperdere", "strasapere", "stravedere", "stravincere", "stravolere", "stravolgere", "strignere", "stringere", "stringersi", "struggere", "struggersi", "stupefare", "stupefarsi", "suadere", "subconcedere", "subsistere", "succedere", "succedersi", "succidere", "succingere", "suddistinguere", "suddividere", "suddividersi", "suffiggere", "suffolcere", "suffondere", "suffulcere", "suggere", "sumere", "superavvolgere", "supporre", "surgere", "sussistere", "sussumere", "svegliere", "svellere", "svenire", "svolere", "svolgere", "svolgersi", "tacere", "telediffondere", "teleradiotrasmettere", "teletrasmettere", "televedere", "tendere", "tenerci", "tenere", "tenersi", "tepefare", "tepefarsi", "tergere", "tingere", "tingersi", "togliere", "togliersi", "tondere", "torcere", "torcersi", "tornire", "torre", "torrefare", "trabere", "tradurre", "tradursi", "trafiggere", "trafiggersi", "traggere", "tralucere", "tramettere", "transandare", "transcendere", "transcorrere", "transcrivere", "transfondere", "transigere", "transporre", "transvedere", "traporre", "trapporre", "trapungere", "trarompere", "trarre", "trarsi", "trasandare", "trascegliere", "trascendere", "trascorrere", "trascrivere", "trasdurre", "trasfondere", "trasgredire", "trasmettere", "trasmettersi", "trasparire", "trasporre", "trasvedere", "trasvolgere", "trattenere", "trattenersi", "traudire", "travedere", "travolgere", "tumefare", "tumefarsi", "ubbidire", "uccidere", "uccidersi", "udire", "ugnere", "ungere", "ungersi", "uscire", "uscirne", "uscirsene", "usucapire", "valere", "valersi", "vederci", "vedere", "vedersela", "vedersi", "venire", "venirne", "venirsene", "vergere", "videoscrivere", "videotrasmettere", "vilipendere", "vincere", "vincersi", "vivere", "viversi", "volercene", "volerci", "volere", "volerne", "volersi", "volgere", "volgersi", "volvere"]
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