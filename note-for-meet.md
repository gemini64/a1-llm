# Estimating viable length

**Options:**
1. Using learning material for a1 learners
- No specific data on CEFR Documents (the only info is: short text)
- **IT:** Use sites as http://parliamoitaliano.altervista.org/ to extract average length data
- **IT/EN:** Check if any exams or books can be used to extract some statistical data about average **readings** length

2. Check how long are text used in similar studies
- **[TinyStories](https://arxiv.org/pdf/2305.07759):** 2-3 paragraphs that follow a simple plot and a consistent theme. No detailed statistics about the average word count, token count, or other specific length metrics for the stories. Can extrapolate data from HF. Note that there is also no real justification other than "texts suitable for a 3-4 y.o. reader".
- **[TinyTolkien](https://drive.google.com/drive/u/1/folders/1FuVHhpRqtmiRN38m8Cq27XqmSlCpZhXw):** 3-5 paraphraphs based on the **summaries** of the TinyStories dataset. Note that in this case the task is leveled on multiple CEFR levels.

3. On pre-existing datasets -> Use in-dateset stats
- **Wikipedia/S-W(EN):** Average summary length
- **CEFR Leveled Texts:** Average on portion tagged as A1

# Options for data sourcing (specifically on italian)
1. Go back to the original idea of using Wikipedia and focus only on "Pagine in vetrina" to have at least some idea of page quality.
2. Use articles from Vikidia and estimate quality using metadata (page length, how many times edited, how many quotations it includes, how many pages refer to it, if it is part of a very populated sub-category...)
3. Other options:
- **[Cleaned HC Corpora](https://www.kaggle.com/datasets/alvations/old-newspapers)**: Text from the internet, splitted into single line entries. Available also for Italian (with subset of blogs, articles, and tweets). No linguistic quality data.
- **[PAISÀ Corpus](https://www.corpusitaliano.it/):** Also text from the web, only in IT, minimum length is 100 words. Sources are various but only with CC usare rights. Also no linguistic quality data.