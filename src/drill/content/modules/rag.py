"""RAG with Vector Search: Chunking, indexing and retrieval, then measuring which settings actually work."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('rag', 'RAG with Vector Search', 'Chunking, indexing and retrieval, then measuring which settings actually work.')

lesson(MODULE, 'chunk_text',
    title='Chunking documents',
    learn=[
        'RAG (retrieval-augmented generation) answers questions from your documents. First you cut each document into **chunks** small enough to search and to fit in a prompt.',
        'Chunks **overlap** a little, so a sentence that crosses a boundary appears whole in at least one chunk.',
    ],
    example=example('Size 4, overlap 1', """'abcdefghij' -> 'abcd', 'defg', 'ghij'
# each new chunk starts size - overlap = 3 characters later"""),
    check=question(
        'Why do chunks overlap?',
        [
            'To make the index bigger',
            'So text cut at a boundary still appears whole in one chunk',
            'Because embeddings need it',
        ],
        answer=1,
        why='Without overlap, an answer split across two chunks may never be retrieved in one piece.',
    ),
    angle=angle(
        pattern='Sliding window',
        text='A fixed-size window moves along the text in steps, so each part of the text is read only a couple of times. Longest Substring Without Repeating Characters uses a window that grows and shrinks instead.',
        say='"I slide a fixed window forward by size minus overlap, and stop once a window reaches the end so the last chunk isn\'t repeated."',
        classic='longest_unique_substring',
    ),
    stack=stack('Databricks Vector Search: index a table of chunks', """vsc.create_delta_sync_index(
    endpoint_name="vs-endpoint", index_name="main.support.docs_index",
    source_table_name="main.support.doc_chunks", pipeline_type="TRIGGERED",
    primary_key="chunk_id", embedding_source_column="text",
    embedding_model_endpoint_name="databricks-gte-large-en",
)"""),
    exercise=exercise(
        title='Chunk a Document',
        topic='rag',
        difficulty='medium',
        fn='chunk_text',
        prompt="""Before a document goes into a search index, it's cut into overlapping pieces called chunks. Given `text`, a chunk `size` and an `overlap`, return the chunks: the first starts at character 0, and each next one starts `size - overlap` characters later. Stop once a chunk reaches the end of the text.

For `"abcdefghij"` with size 4 and overlap 1, the chunks are `"abcd"`, `"defg"`, `"ghij"`. You can assume `overlap` is smaller than `size`. Empty text gives no chunks.""",
        pattern='Move a window along the text in fixed jumps, and know exactly when to stop.',
        target='visit each part of the text a fixed number of times',
        realworld='The first step of RAG (retrieval-augmented generation). The overlap stops a sentence from being cut in half and lost.',
        starter="""def chunk_text(text, size, overlap):
    # your code here
    pass
""",
        solution="""def chunk_text(text, size, overlap):
    chunks = []
    step = size - overlap
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        if start + size >= len(text):
            break
        start += step
    return chunks
""",
        cases=[
            case('abcdefghij', 4, 1, expected=['abcd', 'defg', 'ghij'], sample=True),
            case('abcdefgh', 4, 0, expected=['abcd', 'efgh']),
            case('abc', 5, 1, expected=['abc']),
            case('', 4, 1, expected=[]),
            case('abcdefghijk', 4, 2, expected=['abcd', 'cdef', 'efgh', 'ghij', 'ijk']),
        ],
        guided="""def chunk_text(text, size, overlap):
    # Replace every ___ with real code, then run the tests.

    chunks = []
    # Step 1: how far each new chunk moves forward.
    step = ___ - ___
    start = 0

    # Step 2: keep cutting while start is still inside the text.
    while start < len(text):
        chunks.append(text[___:___])
        # Step 3: did that chunk reach the end? Then we're done.
        if ___ >= len(text):
            break
        start += ___

    return chunks
""",
        concepts=[
            [
                'while loop',
                'Repeats while a condition is true. Good when the stopping point depends on what happens inside.',
                """start = 0
while start < 10:
    start += 3""",
            ],
            [
                'break',
                'Leaves the loop immediately.',
                """for n in [1, 2, 3]:
    if n == 2:
        break""",
            ],
            [
                'Slicing past the end',
                'text[8:12] on a 10-letter text just gives the last 2 letters. No error.',
                "'abcdefghij'[8:12]   # 'ij'",
            ],
        ],
        byhand='"abcdefghij" (10 letters), size 4, overlap 1, so each jump is 3. Start at 0: "abcd". Jump to 3: "defg". Jump to 6: "ghij", which reaches letter 10, the end. Stop. Without that check you\'d also add "j" alone, a chunk that\'s already covered.',
        why='Each jump moves forward by size minus overlap, so the number of chunks grows in step with the text.',
        gotchas=[
            [
                'Overlap as big as the chunk',
                'If overlap is equal to or larger than size, the jump is 0 or backwards and the loop never ends. Real splitters check this up front and raise an error.',
            ],
            [
                'Cutting by characters',
                "Splitting in the middle of a word or sentence hurts search quality. Real tools like LangChain's RecursiveCharacterTextSplitter try paragraph breaks first, then sentences, then words.",
            ],
            [
                'Chunks measured in tokens',
                'Models count tokens (word pieces), not characters. A chunk of 1,000 characters is roughly 250 tokens in English.',
            ],
        ],
    ),
)

lesson(MODULE, 'dedupe_chunks',
    title='Cleaning the index',
    learn=[
        'Real document sets are full of repeats: footers, disclaimers, copied pages. Duplicates waste embedding money and push useful chunks out of the top results.',
        'Normalise text (case, whitespace) into a **key**, and keep only the first chunk for each key.',
    ],
    example=example('Same text, same key', "' '.join('ALL RIGHTS\\nRESERVED.'.lower().split())\n# 'all rights reserved.'"),
    check=question(
        "Your top 5 retrieved chunks are the same disclaimer from 5 pages. What's the best fix?",
        ['Retrieve 50 chunks instead', 'Remove duplicate chunks before indexing', 'Use a bigger model'],
        answer=1,
        why='Fix the index. Retrieving more just pays for more copies of the same text.',
    ),
    angle=angle(
        pattern='Design a key',
        text="Turn each item into a key that comes out the same exactly when two items should count as the same, and keep a set of keys you've seen. One walk through the chunks. Group Anagrams is the same trick, with sorted letters as the key.",
        say='"I turn each chunk into a cleaned-up key and keep a set of keys I\'ve seen, so the first copy survives and the rest are dropped in one pass."',
        classic='group_anagrams',
    ),
    stack=stack('Databricks SQL: keep one chunk per cleaned text', "CREATE OR REPLACE TABLE main.support.doc_chunks_clean AS\nSELECT * FROM main.support.doc_chunks\nQUALIFY row_number() OVER (\n  PARTITION BY lower(regexp_replace(text, '\\\\s+', ' ')) ORDER BY chunk_id) = 1"),
    exercise=exercise(
        title='Remove Duplicate Chunks',
        topic='rag',
        difficulty='easy',
        fn='dedupe_chunks',
        prompt="""The same text shows up many times in a document collection: footers, disclaimers, copied paragraphs. Given a list of `chunks`, remove duplicates, where two chunks count as the same if they match after lowercasing and squeezing all runs of whitespace (spaces, newlines, tabs) to single spaces, with the ends trimmed.

Keep the first copy of each, unchanged, in the original order.""",
        pattern="Design a key that is equal exactly when two things should count as the same, then remember the keys you've seen.",
        target='one pass over the chunks',
        realworld='Duplicates waste embedding money and crowd retrieval: if the top 5 results are the same disclaimer five times, the model never sees the paragraph that answers the question.',
        starter="""def dedupe_chunks(chunks):
    # your code here
    pass
""",
        solution="""def dedupe_chunks(chunks):
    seen = set()
    out = []
    for chunk in chunks:
        key = " ".join(chunk.lower().split())
        if key not in seen:
            seen.add(key)
            out.append(chunk)
    return out
""",
        cases=[
            case([
                'Refunds take 5 days.',
                'All rights reserved.',
                'refunds   take 5 days.',
                """ALL RIGHTS
RESERVED.""",
            ], expected=['Refunds take 5 days.', 'All rights reserved.'], sample=True),
            case([], expected=[]),
            case(['a', 'b', 'a '], expected=['a', 'b']),
            case(['Hi there', 'hi\tthere', 'hithere'], expected=['Hi there', 'hithere']),
        ],
        guided="""def dedupe_chunks(chunks):
    # Replace every ___ with real code, then run the tests.

    seen = set()   # keys you've already kept
    out = []
    for chunk in chunks:
        # Step 1: the key: lowercase, then split() and join with single spaces.
        key = " ".join(___)
        # Step 2: first time you see this key? Keep the chunk.
        if key not in seen:
            seen.add(key)
            ___
    return out
""",
        fills=['chunk.lower().split()', 'out.append(chunk)'],
        concepts=[
            [
                'split with no argument',
                'Splits on any run of whitespace, including newlines and tabs, and drops empty pieces.',
                "'a  b\\nc'.split()   # ['a', 'b', 'c']",
            ],
            [
                'A set of seen keys',
                'Add each key after you use it; check before adding.',
                """seen = set()
seen.add('x')
'x' in seen   # True""",
            ],
        ],
        byhand='"Refunds take 5 days." becomes the key "refunds take 5 days.". Keep it. "refunds   take 5 days." gives the same key: skip. The two disclaimers both become "all rights reserved.": keep the first only.',
        why='One pass; each key check is a set lookup.',
        gotchas=[
            [
                'Near-duplicates',
                'Exact keys miss text that differs by a date or a name. Real pipelines also use hashing tricks such as MinHash to catch near-duplicates.',
            ],
            [
                'Dedupe before you embed',
                'Embedding costs money per token. Removing duplicates first is the cheapest optimisation in most RAG pipelines.',
            ],
        ],
    ),
)

lesson(MODULE, 'retrieve',
    title='Retrieval: finding the right chunks',
    learn=[
        'Retrieval scores every chunk against the question and keeps the top **k** to put in the prompt.',
        'Real systems score with **embeddings** (vectors where similar meanings are close), often combined with keyword search. The shape is the same: score, sort, keep the top k, break ties consistently.',
    ],
    example=example('Score, sort, slice', """scored = sorted(docs, key=score, reverse=True)
top = scored[:k]"""),
    check=question(
        'Why decide how ties are broken?',
        [
            'It makes the code faster',
            "So results don't change between runs and tests stay stable",
            'Embeddings require it',
        ],
        answer=1,
        why='Without a rule, equal scores can come back in any order, which makes results and tests flaky.',
    ),
    angle=angle(
        pattern='Top k',
        text='Score every document once, then sort. When there are millions of documents and you only want the top few, a heap (`heapq.nlargest`) keeps just those few as it goes, which is much faster than sorting everything.',
        say='"Sorting everything works. A heap that keeps only the best k as I go is much faster when there are millions of documents."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: hybrid search', """from databricks.vector_search.client import VectorSearchClient
index = VectorSearchClient().get_index(endpoint_name="vs-endpoint", index_name="main.support.docs_index")
results = index.similarity_search(
    query_text=question, columns=["chunk_id", "text"],
    query_type="HYBRID", num_results=5,
)"""),
    exercise=exercise(
        title='Find the Best Documents',
        topic='rag',
        difficulty='medium',
        fn='retrieve',
        prompt="""Given a search `query`, a list of `docs` (strings) and a number `k`, return the positions of the `k` best documents, best first. A document's score is how many different query words appear in it, ignoring upper and lower case. Words are separated by spaces.

If two documents have the same score, the one that comes first in `docs` wins. Leave out documents that score 0. Return fewer than `k` if there aren't enough.""",
        pattern='Score every candidate, sort by score, keep the top few. Decide up front how ties are broken.',
        target='score each document once, then sort',
        realworld='Retrieval in RAG. Real systems score with embeddings instead of shared words, but the score, sort and keep-the-top-k shape is the same.',
        starter="""def retrieve(query, docs, k):
    # your code here
    pass
""",
        solution="""def retrieve(query, docs, k):
    words = set(query.lower().split())
    scored = []
    for i, doc in enumerate(docs):
        score = len(words & set(doc.lower().split()))
        if score > 0:
            scored.append((-score, i))
    scored.sort()
    return [i for _, i in scored[:k]]
""",
        cases=[
            case('cat food', ['dog food', 'cat toys', 'cat food bowl', 'birds'], 2, expected=[2, 0], sample=True),
            case('Python', ['I like python', 'Java'], 3, expected=[0]),
            case('a b', [], 2, expected=[]),
            case('x y', ['y x', 'x', 'q'], 5, expected=[0, 1]),
            case('The', ['the the the', 'THE end'], 1, expected=[0]),
        ],
        guided="""def retrieve(query, docs, k):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the query's words, lowercase, as a set.
    words = set(query.___().split())

    scored = []
    for i, doc in enumerate(docs):
        # Step 2: how many query words are in this doc?
        score = len(words & set(___))
        if score > 0:
            # Step 3: store (-score, i) so sorting puts best first, ties by position.
            scored.append((___, ___))

    scored.sort()
    # Step 4: keep the first k positions.
    return [i for _, i in scored[:___]]
""",
        concepts=[
            [
                'set',
                'A collection with no duplicates. a & b gives what two sets have in common.',
                "{'cat', 'food'} & {'cat', 'toys'}   # {'cat'}",
            ],
            [
                'Sorting pairs',
                'Python sorts tuples by the first item, then the second. Make the score negative to get biggest first while keeping lower positions first on ties.',
                """sorted([(-1, 0), (-2, 2), (-1, 1)])
# [(-2, 2), (-1, 0), (-1, 1)]""",
            ],
            [
                'lower and split',
                'lower() makes text lowercase. split() cuts it into words at spaces.',
                "'Cat Food'.lower().split()   # ['cat', 'food']",
            ],
        ],
        byhand='Query "cat food". "dog food" shares food (1). "cat toys" shares cat (1). "cat food bowl" shares both (2). "birds" shares nothing, so drop it. Best first: position 2 (score 2), then the ties at positions 0 and 1, and the first one wins. With k = 2 the answer is [2, 0].',
        why='You look at each document once to score it, then sort. Sorting is a little slower than one pass, but fine.',
        gotchas=[
            [
                'Ties in random order',
                "If you don't decide how ties break, results can change from run to run and your tests become flaky.",
            ],
            [
                'Real retrieval uses embeddings',
                'An embedding turns text into a list of numbers so that similar meanings land close together. "car" then matches "automobile", which word matching misses. Good systems often combine both, called hybrid search.',
            ],
            [
                "More context isn't always better",
                'Stuffing many chunks into the prompt costs more and can bury the useful one. Picking a small k and reranking is a common pattern.',
            ],
        ],
    ),
)

lesson(MODULE, 'recall_at_k',
    title='Measuring retrieval',
    learn=[
        "A RAG answer can fail in two places: retrieval didn't find the right document, or the model didn't use it well. Measure them separately.",
        "**Recall@k** asks: of the documents that should have been found, how many were in the top k? It needs a small set of questions where you've marked the right documents by hand.",
    ],
    example=example('A recall@5 scorer for mlflow.genai.evaluate', """from mlflow.genai.scorers import scorer

@scorer
def recall_at_5(outputs, expectations):
    found = set(outputs["doc_ids"][:5])
    wanted = set(expectations["relevant_ids"])
    return len(found & wanted) / len(wanted) if wanted else 0.0"""),
    check=question(
        'Recall@5 is 0.3 and answers are poor. What should you work on first?',
        ['The prompt', 'Retrieval: chunking, the embedding model or k', 'A bigger LLM'],
        answer=1,
        why="The model can't answer from documents it never saw. Fix retrieval first.",
    ),
    angle=angle(
        pattern='Set overlap',
        text='Take the top k, turn both lists into sets and count what they share. The same "is it in here?" lookup as Two Sum.',
        say='"I intersect the top-k ids with the relevant set and divide by the number of relevant ids, guarding the empty case."',
        classic='two_sum',
    ),
    stack=stack('MLflow: a recall@5 scorer', """from mlflow.genai.scorers import scorer

@scorer
def recall_at_5(outputs, expectations):
    found = set(outputs["doc_ids"][:5])
    wanted = set(expectations["relevant_ids"])
    return len(found & wanted) / len(wanted) if wanted else 0.0"""),
    exercise=exercise(
        title='Measure Retrieval',
        topic='rag',
        difficulty='easy',
        fn='recall_at_k',
        prompt="""For one test question you know which documents are relevant. `retrieved` is the list of document ids your retriever returned, best first, and `relevant` is the list of ids that should be found.

Return the share of relevant ids that appear in the first `k` retrieved, rounded to 2 places. If `relevant` is empty, return `0.0`.""",
        pattern='Take the top k, turn both into sets, count the overlap.',
        target='one walk through the top k',
        realworld='Measure retrieval separately from the final answer. If recall@5 is low, no prompt change will fix the answers: the model never saw the right document.',
        starter="""def recall_at_k(retrieved, relevant, k):
    # your code here
    pass
""",
        solution="""def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0
    found = set(retrieved[:k]) & set(relevant)
    return round(len(found) / len(set(relevant)), 2)
""",
        cases=[
            case(['d7', 'd2', 'd9', 'd4'], ['d2', 'd4'], 3, expected=0.5, sample=True),
            case(['a'], [], 1, expected=0.0),
            case(['a', 'b'], ['a', 'b'], 2, expected=1.0),
            case(['x', 'y', 'z'], ['q'], 3, expected=0.0),
            case(['a', 'b', 'c'], ['c', 'b', 'e'], 5, expected=0.67),
        ],
        guided="""def recall_at_k(retrieved, relevant, k):
    # Replace every ___ with real code, then run the tests.

    if not relevant:
        return 0.0
    # Step 1: the ids in the top k that are also relevant. & is set intersection.
    found = set(___) & set(relevant)
    # Step 2: what share of the relevant ids were found?
    return round(___, 2)
""",
        fills=['retrieved[:k]', 'len(found) / len(set(relevant))'],
        concepts=[
            ['Set intersection', "`a & b` keeps what's in both sets.", "{'d2', 'd7'} & {'d2', 'd4'}   # {'d2'}"],
            [
                'Slicing past the end',
                '`items[:5]` on a 3-item list just gives all 3.',
                "['a', 'b'][:5]   # ['a', 'b']",
            ],
        ],
        byhand='Top 3: d7, d2, d9. Relevant: d2 and d4. Found d2 only, so 1 of 2: 0.5.',
        why='One walk through the top k; set lookups are instant.',
        gotchas=[
            [
                'You need labelled questions',
                "Recall needs to know which documents are relevant. Start with 30–50 real questions and mark the right documents by hand; it's the most valuable hour in a RAG project.",
            ],
            [
                "Higher k isn't free",
                'Raising k usually raises recall but adds tokens, cost and latency, and can bury the right chunk among wrong ones.',
            ],
        ],
    ),
)

lesson(MODULE, 'pick_config',
    title='Designing a RAG experiment',
    learn=[
        'The settings that matter most in RAG: **chunk size** and **overlap**, **k** (how many chunks go into the prompt), the **embedding model**, and whether you **rerank**. Vary two at a time.',
        'Hold the eval set, the judge and the answering model fixed. Log retrieval quality, answer quality, p95 latency and cost for every run. Then pick using the rule you wrote down: best answer quality within the latency budget.',
    ],
    example=example('One evaluated run per config', """from mlflow.genai.scorers import RelevanceToQuery, RetrievalGroundedness

for chunk_size, k in [(256, 3), (512, 5), (1024, 10)]:
    with mlflow.start_run(run_name=f"cs{chunk_size}-k{k}"):
        mlflow.log_params({"chunk_size": chunk_size, "k": k})
        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(chunk_size, k),
                              scorers=[RetrievalGroundedness(), RelevanceToQuery()])"""),
    check=question(
        'Your best-quality config has a p95 of 2.6 seconds; the product needs under 1.5. What do you ship?',
        ['The best-quality config anyway', 'The best config within 1.5 seconds', 'The fastest config'],
        answer=1,
        why="A config the product can't use has no return. Maximise quality inside the budget.",
    ),
    angle=angle(
        pattern='Constraint, then best, then tie-break',
        text='Skip what breaks the budget, keep the best of the rest, and break ties on cost. One walk through the results.',
        say='"I filter by the latency budget, then take the highest quality, with cost as the tie-break."',
        classic=None,
    ),
    stack=stack('MLflow: one evaluated run per config', """for chunk_size, k in [(256, 3), (512, 5), (1024, 10)]:
    with mlflow.start_run(run_name=f"cs{chunk_size}-k{k}"):
        mlflow.log_params({"chunk_size": chunk_size, "k": k})
        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(chunk_size, k),
                              scorers=[RetrievalGroundedness(), RelevanceToQuery()])"""),
    exercise=exercise(
        title='Choose Chunk Size and k',
        topic='rag',
        difficulty='medium',
        fn='pick_config',
        prompt="""You ran a RAG experiment over chunk sizes and k. Each row of `results` looks like `{"chunk_size": 512, "k": 5, "quality": 0.82, "p95_ms": 1400, "cost": 2.1}`.

Return `[chunk_size, k]` for the row with the highest `quality` whose `p95_ms` is at most `max_ms`. If several tie on quality, pick the cheapest. If none is fast enough, return `None`.""",
        pattern='Constraint first, then best by the main metric, then a tie-break on cost.',
        target='one walk through the results',
        realworld="Teams often pick the highest-quality config and discover it's too slow for the product. Deciding the latency budget up front, then maximising quality inside it, is how you get a config you can actually ship.",
        starter="""def pick_config(results, max_ms):
    # your code here
    pass
""",
        solution="""def pick_config(results, max_ms):
    best = None
    for r in results:
        if r["p95_ms"] > max_ms:
            continue
        if best is None or r["quality"] > best["quality"] or (r["quality"] == best["quality"] and r["cost"] < best["cost"]):
            best = r
    return [best["chunk_size"], best["k"]] if best else None
""",
        cases=[
            case([
                {'chunk_size': 256, 'k': 3, 'quality': 0.71, 'p95_ms': 900, 'cost': 1.2},
                {'chunk_size': 512, 'k': 5, 'quality': 0.82, 'p95_ms': 1400, 'cost': 2.1},
                {'chunk_size': 1024, 'k': 10, 'quality': 0.85, 'p95_ms': 2600, 'cost': 3.9},
            ], 1500, expected=[512, 5], sample=True),
            case([], 1000, expected=None),
            case([{'chunk_size': 512, 'k': 5, 'quality': 0.8, 'p95_ms': 2000, 'cost': 2.0}], 1000, expected=None),
            case([
                {'chunk_size': 256, 'k': 5, 'quality': 0.8, 'p95_ms': 800, 'cost': 1.5},
                {'chunk_size': 512, 'k': 3, 'quality': 0.8, 'p95_ms': 700, 'cost': 1.1},
            ], 1000, expected=[512, 3]),
        ],
        guided="""def pick_config(results, max_ms):
    # Replace every ___ with real code, then run the tests.

    best = None
    for r in results:
        # Step 1: too slow? skip it.
        if ___:
            continue
        # Step 2: higher quality wins; on a tie, cheaper wins.
        if best is None or r["quality"] > best["quality"] or (r["quality"] == best["quality"] and r["cost"] < best["cost"]):
            best = r
    # Step 3: return the two settings, or None.
    return ___ if best else None
""",
        fills=['r["p95_ms"] > max_ms', '[best["chunk_size"], best["k"]]'],
        concepts=[['A one-line if', '`a if condition else b`.', 'answer = [512, 5] if best else None']],
        byhand='Budget 1,500 ms. 256/3 takes 900 ms, quality 0.71. 512/5 takes 1,400 ms, quality 0.82: better. 1024/10 takes 2,600 ms: too slow. Answer [512, 5].',
        why='One walk through the results.',
        gotchas=[
            [
                'Change one thing at a time when debugging',
                "If quality drops after changing chunk size, k and the embedding model together, you won't know which one did it.",
            ],
            [
                'Measure retrieval and answers separately',
                'Log recall@k and answer quality as separate metrics. A config can retrieve well and still answer badly, and the fixes are different.',
            ],
        ],
    ),
)

lesson(MODULE, 'rrf',
    title='Hybrid search and rank fusion',
    learn=[
        'Keyword search is great at exact terms like error codes and product names; vector search is great at meaning. **Hybrid search** runs both.',
        "Their scores aren't comparable, so merge by **rank** instead: reciprocal rank fusion rewards documents that rank well in either list.",
    ],
    example=example('Fusing two rankings', """keyword: d3, d1, d7
vector:  d1, d9, d3
fused:   d1, d3, d9, d7"""),
    check=question(
        'Users search for error code "E-4021" and vector search misses it. What helps?',
        ['A bigger embedding model', 'Hybrid search that includes keyword matching', 'Raising k'],
        answer=1,
        why='Exact codes are what keyword search is for.',
    ),
    angle=angle(
        pattern='Score by rank, sort',
        text='One step per ranked item, then one sort.',
        say='"I fuse rankings with reciprocal rank fusion, so I don\'t compare raw scores on different scales."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: hybrid query', """results = index.similarity_search(
    query_text="error E-4021 on checkout",
    columns=["chunk_id", "text"],
    query_type="HYBRID",
    num_results=10,
)"""),
    exercise=exercise(
        title='Combine Two Rankings',
        topic='rag',
        difficulty='medium',
        fn='rrf',
        prompt="""Hybrid search runs a keyword search and a vector search, then merges their rankings. **Reciprocal rank fusion** gives each document `1 / (k + rank)` from each list it appears in (rank counts from 1), and adds them up.

`rankings` is a list of ranked lists of document ids. Return all the ids, highest total score first; break ties alphabetically.""",
        pattern='Score by position, add across lists, sort by score with a tie-break.',
        target='one step per ranked item, then a sort',
        realworld='Keyword search finds exact terms (error codes, product names); vector search finds meaning. Fusing them by rank avoids comparing scores on different scales. Databricks Vector Search does hybrid search with `query_type="HYBRID"`.',
        starter="""def rrf(rankings, k):
    # your code here
    pass
""",
        solution="""def rrf(rankings, k):
    score = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0) + 1 / (k + rank)
    return sorted(score, key=lambda d: (-score[d], d))
""",
        cases=[
            case([['d3', 'd1', 'd7'], ['d1', 'd9', 'd3']], 60, expected=['d1', 'd3', 'd9', 'd7'], sample=True),
            case([], 60, expected=[]),
            case([['a', 'b']], 1, expected=['a', 'b']),
            case([['a', 'b'], ['b', 'a']], 60, expected=['a', 'b']),
        ],
        guided="""def rrf(rankings, k):
    # Replace every ___ with real code, then run the tests.

    score = {}
    for ranking in rankings:
        # Step 1: enumerate(..., start=1) gives ranks 1, 2, 3...
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0) + ___
    # Step 2: highest score first, then alphabetical.
    return sorted(score, key=lambda d: (___, d))
""",
        fills=['1 / (k + rank)', '-score[d]'],
        concepts=[
            [
                'enumerate with start',
                '`start=1` counts from 1 instead of 0.',
                "list(enumerate(['a', 'b'], start=1))   # [(1, 'a'), (2, 'b')]",
            ],
            [
                'Sorting with a key',
                '`key` says what to sort by; a minus sign puts the biggest first.',
                "sorted(['a', 'b'], key=lambda d: (-scores[d], d))",
            ],
        ],
        byhand="With k = 60: d1 is 2nd in one list and 1st in the other, so it scores highest. d3 is 1st and 3rd, next. d9 and d7 appear once each, and d9's rank is better.",
        why='One step per ranked item, then one sort.',
        gotchas=[
            [
                'Measure before and after',
                'Hybrid search usually helps on queries with exact terms. Check recall@k on your own eval set rather than assuming.',
            ],
            [
                'Rerankers come after fusion',
                'A reranker model re-scores the fused top results more carefully, at extra latency and cost.',
            ],
        ],
    ),
)
