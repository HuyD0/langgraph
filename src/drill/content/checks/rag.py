"""More Check questions for RAG with Vector Search (modules/rag.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "chunk_text": [
        ask("You cut a manual into chunks with no overlap. A question about the warranty fails, and the "
            "warranty sentence is split across two chunks. What change helps?",
            ["Retrieve fewer chunks each time", "Let chunks overlap a little", "Use a different answering model"],
            answer=1,
            clue="The sentence needs to appear whole somewhere.",
            why="With a little overlap, each chunk repeats the end of the one before, so a sentence cut "
                "at the edge shows up whole in one of them."),
        ask("Someone wants to skip chunking and store each 200-page manual in the index as one piece. "
            "What's the problem?",
            ["Too big to search well or fit a prompt", "The index only accepts short text", "Search would only match its title"],
            answer=0,
            clue="Think about what you do with each piece once search finds it.",
            why="Chunks need to be small enough to search and to fit in a prompt. A whole 200-page "
                "manual is neither."),
    ],
    "dedupe_chunks": [
        ask("Your dedupe compares chunks exactly as written. Two chunks are the same footer, but one "
            "has capital letters and extra spaces. What happens?",
            ["The second copy is dropped", "Both copies are dropped", "Both are kept, so a copy slips in"],
            answer=2,
            clue="Does the raw text match letter for letter?",
            why="The raw text differs, so an exact compare misses the copy. Normalise it into a key "
                "first: lowercase, single spaces."),
        ask("Your 10,000 chunks include the same legal footer from every page. What do all those copies "
            "cost you?",
            ["Money for embeddings and room in results", "Nothing, search skips repeated text", "Only a little extra disk space"],
            answer=0,
            clue="Every chunk is turned into an embedding. And what fills the top results?",
            why="You pay for every embedding, and repeated footers crowd useful chunks out of the top results."),
    ],
    "retrieve": [
        ask("Your retriever scores every chunk but forgets to sort before taking the first 3. "
            "What do you get?",
            ["The best 3, just more slowly", "The first 3 in the list, not the best", "An error, because k needs sorting"],
            answer=1,
            clue="Without sorting, which three come first?",
            why="Keeping the top k only works after sorting by score. Without it you get whatever "
                "happened to come first in the list."),
        ask("A user asks \"how do I get my money back?\" The right chunk says \"refund policy\". "
            "Keyword search finds nothing. Why do real systems also use embeddings?",
            ["They match exact words faster", "They always return more chunks", "Similar meanings land close together"],
            answer=2,
            clue="The question and the chunk share no words, but they mean the same thing.",
            why="Embeddings put similar meanings close together, so \"money back\" can match \"refund\" "
                "even with no words in common."),
    ],
    "recall_at_k": [
        ask("Answers are poor, but recall@5 is high: the right documents nearly always reach the top 5. "
            "Where do you look next?",
            ["The chunk size and the k", "The embedding model", "How the model uses the chunks"],
            answer=2,
            clue="Retrieval is finding the right documents. Which half is left?",
            why="A RAG answer can fail in retrieval or in the answer. High recall means retrieval is doing "
                "its job, so look at the prompt and how the model uses what it gets."),
        ask("You want to measure recall@5, but nobody has marked which documents are right for each "
            "question. What do you need first?",
            ["Questions with their right docs marked", "A bigger k, like 50 instead of 5", "An LLM judge to grade the answers"],
            answer=0,
            clue="Recall counts how many of the right documents were found. How do you know which are right?",
            why="Recall@k needs a small set of questions where someone has marked the right documents by hand."),
    ],
    "pick_vector_size": [
        ask("Your index holds 5 million chunks at 1,536 numbers each. A teammate wants to switch to a model "
            "that gives 768, \"just for the new documents\". What happens?",
            ["Every chunk must be embedded again", "It works: search handles mixed sizes", "Only the new chunks need a bigger k"],
            answer=0,
            clue="Can a vector from one model be compared with a vector from another?",
            why="Vectors from two models can't be compared, and an index has one size, so a new model means new "
                "embeddings for every chunk and a rebuilt index. Plan it as a one-off as big as the first indexing."),
        ask("A 3,072-number model tops a public leaderboard. On your own eval set, recall@5 is 0.86 with it "
            "and 0.86 with your 768-number model. Which do you keep?",
            ["The 768 model: same recall, less cost", "The 3,072 model: bigger finds more", "The 3,072 model: the leaderboard says so"],
            answer=0,
            clue="Which test used your questions and your documents?",
            why="Bigger is not always better on your own documents. The honest check is retrieval quality on "
                "your own eval set, and there the smaller model does just as well, with fewer units and "
                "faster search."),
    ],
    "ndcg_at_k": [
        ask("You want to compare two rerankers with nDCG@5, but your test questions have no relevance "
            "grades yet. What do you do?",
            ["Use recall@5 in place of grades", "Have people or an LLM judge grade a sample", "Give every document a grade of 3"],
            answer=1,
            clue="nDCG needs to know how good each document is. Someone has to say so.",
            why="nDCG needs a relevance grade for each document. Grades come from people or an LLM judge, "
                "on a sample of questions."),
        ask("Your users read the whole top 5, not just the first hit. Which metric fits better, MRR or nDCG?",
            ["MRR, as it looks at the first hit", "Either, they measure the same thing", "nDCG, as it counts every graded doc"],
            answer=2,
            clue="One of them only cares where the first relevant document sits.",
            why="MRR only looks at the first relevant document. nDCG adds up every graded document, "
                "counting lower places less."),
    ],
    "rerank_check": [
        ask("Before reranking, the right document was 3rd. After, it's 8th, and k is 5. Which outcome does "
            "this question get?",
            ["Helped", "Hurt", "Out of reach"],
            answer=1,
            clue="It was in the top 5 before. Is it still there after?",
            why="It was in the top 5 before and got pushed out after, so the reranker hurt this one."),
        ask("A teammate compares the top 5 before and after reranking, but uses a different candidate "
            "list for each. What's wrong?",
            ["It no longer shows what the reranker did", "The reranker needs at least 50 candidates", "Nothing, as long as k stays at 5"],
            answer=0,
            clue="To see what one change did, what should stay the same?",
            why="Compare on the same candidate lists, so the only difference is the order the reranker chose."),
    ],
    "abstention_rates": [
        ask("A payroll bot's documents cover pay and payslips, but not pensions. You're writing "
            "unanswerable questions for its eval set. Which one tests it best?",
            ["\"How do I change my pension?\"", "\"What's the weather on Mars?\"", "\"Where do I see my payslip?\""],
            answer=0,
            clue="Look for a question the documents don't answer, but the bot might be tempted to.",
            why="Good unanswerable questions sit on nearby topics the documents don't cover. Mars is too "
                "easy to decline, and payslips are covered."),
        ask("You tune your help-desk app so it declines more often, and missed refusals drop. "
            "What should you watch next?",
            ["Over-refusals, which tend to go up", "Nothing: the risky rate is fixed now", "Recall@5 of the retriever"],
            answer=0,
            clue="The two rates pull against each other.",
            why="Pushing one rate down usually pushes the other up. Declining more often means it may "
                "turn away questions it could answer."),
    ],
    "claim_gate": [
        ask("The gate checks 4 claims: 3 supported, 1 unsupported, none contradicted. What does the gate do?",
            ["Release all 4 claims", "Abstain from answering", "Revise: drop the unsupported one"],
            answer=2,
            clue="Not every claim is backed, but some are, and nothing says the opposite of its source.",
            why="Some supported and none contradicted means revise: keep the 3 supported claims and "
                "drop the other one."),
        ask("One claim says refunds take 5 days, but its cited passage says 30 days. The other claims "
            "are supported. What should a safe gate do?",
            ["Abstain, since one claim is contradicted", "Revise and drop just that claim", "Release, since most are supported"],
            answer=0,
            clue="This claim doesn't just lack support. It says the opposite of its source.",
            why="A contradiction means the answer says the opposite of its source, so a safe policy "
                "abstains instead of trusting the rest."),
    ],
    "pick_config": [
        ask("In one run you change both the chunk size and the embedding model, and quality goes up. "
            "What can't you tell?",
            ["Whether quality went up at all", "Which of the two changes helped", "How long the run took"],
            answer=1,
            clue="Two things changed at once.",
            why="Change one setting at a time, or try every combination of the two (a grid search), so "
                "you can see what each one did."),
        ask("Between two runs, a teammate also swapped in a new judge. Run B scores higher than run A. "
            "Can you trust the comparison?",
            ["Yes, a newer judge is fairer", "No, the judge must stay fixed", "Yes, if the eval set is the same"],
            answer=1,
            clue="If the thing doing the scoring changed, what is the score really measuring?",
            why="Hold the eval set, the judge and the answering model fixed. Otherwise a higher score "
                "might come from the new judge, not the new settings."),
    ],
    "rrf": [
        ask("Keyword search gives one document a score of 12. Vector search gives another 0.83. "
            "Why not just sort them all by score?",
            ["The two kinds of score can't be compared", "Sorting that many scores takes too long", "Vector scores are always more accurate"],
            answer=0,
            clue="Is 12 really better than 0.83, or are they measured in different ways?",
            why="Keyword and vector scores aren't comparable, so hybrid search merges by each "
                "document's place in each list instead."),
        ask("Doc A is 1st in keyword search and 2nd in vector search. Doc B is 1st in vector search and "
            "missing from keyword search. With rank fusion, which comes first?",
            ["Doc B, because 1st place wins", "Doc A, as both lists give it points", "They tie, as both reach 1st place"],
            answer=1,
            clue="Every list a document appears in gives it points.",
            why="Rank fusion adds up points from every list. Doc A collects points twice, so it beats "
                "Doc B, which is found only once."),
    ],
    "vector_index_setup": [
        ask("Your help-desk documents change a few times a day, and answers can be a day behind. "
            "Which sync mode fits?",
            ["Triggered, synced once a day", "Continuous, always streaming", "Either, they cost the same"],
            answer=0,
            clue="Answers can be a day old. Do you need a job running all the time?",
            why="Triggered updates only when you call sync, so it costs least. Continuous runs a "
                "streaming job all the time and is worth it only when minutes matter."),
        ask("Ana has USE CATALOG, USE SCHEMA and SELECT on the index, but her search is still refused. "
            "What is she missing?",
            ["Change Data Feed on the table", "A Storage-optimized endpoint", "Her permission on the endpoint"],
            answer=2,
            clue="Access has two locks: one in Unity Catalog, and one somewhere else.",
            why="Unity Catalog grants cover the index, but the endpoint has its own permission, "
                "CAN_USE or CAN_MANAGE."),
    ],
    "pick_search_service": [
        ask("The files sit in Azure Blob Storage, and you don't want to write your own chunking and "
            "embedding code. What helps most?",
            ["Azure AI Search indexers", "A Delta Sync index", "The semantic ranker"],
            answer=0,
            clue="Look for the part that pulls files in on a schedule and prepares them for search.",
            why="Azure AI Search indexers pull the files in on a schedule, cut them into chunks and make "
                "the embeddings for you."),
        ask("Your team runs both: product tables in Databricks Vector Search, SharePoint files in Azure "
            "AI Search. How do you compare them fairly?",
            ["Ask users which one they like", "Use one eval set for both", "Compare their monthly bills"],
            answer=1,
            clue="To compare two things fairly, give them the same test.",
            why="Keep one evaluation set, so both are judged on the same questions."),
    ],
}
