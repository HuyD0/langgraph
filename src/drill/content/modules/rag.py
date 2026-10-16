"""RAG with Databricks Vector Search and Azure AI Search: Chunking, indexing and retrieval, then measuring which settings actually work."""

from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, practice, question, stack, source

MODULE = module('rag', 'RAG with Vector Search', 'Chunking, indexing and retrieval on Databricks Vector Search or Azure AI Search, then measuring which settings actually work.')

lesson(MODULE, 'chunk_text',
    title='Chunking documents',
    learn=[
        'RAG (retrieval-augmented generation) answers questions from your documents. First you cut each document into **chunks** small enough to search and to fit in a prompt. The chunks are then stored in a search **index**: a table of chunks that can be searched quickly.',
        'Chunks **overlap** a little, so a sentence that crosses a boundary appears whole in at least one chunk.',
    ],
    example=example('Size 4, overlap 1', """'abcdefghij' -> 'abcd', 'defg', 'ghij'
# each new chunk starts size - overlap = 3 characters later"""),
    check=question(
        'Why do chunks overlap?',
        [
            'So each chunk stays under the size limit for the prompt',
            'So text cut at a boundary still appears whole in one chunk',
            'So the model sees every sentence twice and weighs it more',
        ],
        answer=1,
        why='Without overlap, an answer split across two chunks may never be retrieved in one piece.',
    ),
    angle=angle(
        pattern='Sliding window with overlap',
        text='The big idea: documents are cut into small chunks for search, and chunks overlap a little so a sentence on a boundary appears whole in one of them. Your code starts at character 0 and cuts out `size` characters. Then it moves forward by `size - overlap`, so each chunk repeats the last few characters of the one before. It stops once a chunk reaches the end of the text, so no extra chunk is made. It is like roof tiles, each one covering the edge of the last.',
        say='"I cut the text into small [[chunks|tables|keys::These are the pieces you search and put in the prompt.]] that [[overlap|alternate|shrink::Each piece repeats the end of the one before.]] a little. That way a sentence cut at the edge still shows up [[whole|twice|shorter::You want the full sentence in at least one piece.]] in one of them."',
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
        prompt="""Your function gets three things:

- `text`: the document, a string like `"abcdefghij"`.
- `size`: how many characters go in each chunk, like `4`.
- `overlap`: how many characters each chunk shares with the one before it, like `1`.

The first chunk starts at character 0. Each next chunk starts `size - overlap` characters later. Stop once a chunk includes the last character of the text. The last chunk can be shorter than `size`.

Return the chunks as a list, in order. Empty text gives `[]`.""",
        pattern='A sliding window: move a fixed-size slice along the text in equal jumps, and know exactly when to stop.',
        target='one pass along the text, in equal jumps',
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
    step = ___
    start = 0

    while start < len(text):
        # Step 2: cut size characters, beginning at start.
        chunks.append(text[___])
        # Step 3: the same end position you used in step 2.
        # If it is at or past len(text), stop.
        if ___ >= len(text):
            break
        start += step

    return chunks
""",
        fills=['size - overlap', 'start:start + size', 'start + size'],
        concepts=[
            [
                'Slicing',
                '`text[a:b]` gives the characters from position a up to, but not including, position b. Positions count from 0. Going past the end is fine: you just get what is there.',
                """'python'[0:3]   # 'pyt'
'python'[4:9]   # 'on'""",
            ],
            [
                'append',
                '`items.append(x)` adds x to the end of a list.',
                """names = []
names.append('ana')   # ['ana']""",
            ],
            [
                'while loop',
                'Repeats while a condition is true. Good when the stopping point depends on what happens inside.',
                """start = 0
while start < 10:
    start += 3""",
            ],
            [
                'break',
                'Leaves the loop straight away.',
                """for n in [1, 2, 3]:
    if n == 2:
        break""",
            ],
        ],
        byhand='The text "abcdefghij" has 10 characters. Size is 4 and overlap is 1, so each jump is 3. Start at 0: cut "abcd". Jump to 3: cut "defg". Jump to 6: cut "ghij". That chunk reaches the last character, so stop. (Without the stop you would also add "j" on its own, which "ghij" already has.) Return ["abcd", "defg", "ghij"].',
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
        'Real document sets are full of repeats: footers, disclaimers, copied pages. Each chunk is turned into an embedding (a list of numbers used for search), and you pay for each one. Duplicates waste that money and push useful chunks out of the top results.',
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
        pattern='Clean key, keep the first',
        text="The big idea: repeated chunks waste money on embeddings and push useful chunks out of the results, so you keep only the first copy. Your code makes a key for each chunk: lowercase, with extra spaces and line breaks squeezed to single spaces. It keeps a set of keys it has already seen. A set is a collection where checking if something is in it is instant, like finding a word through a book's index. A chunk with a new key is kept exactly as written, and one with a seen key is skipped.",
        say='"Copies of the same chunk waste money and crowd out useful ones. I make a cleaned-up [[key|summary|embedding::A lowercase, tidied version used only for comparing.]] for each chunk and keep only the [[first|last|longest::Once you have seen it, later copies get skipped.]] copy."',
        classic='group_anagrams',
    ),
    stack=stack('Databricks SQL: keep one chunk per cleaned text', "CREATE OR REPLACE TABLE main.support.doc_chunks_clean AS\nSELECT * FROM main.support.doc_chunks\nQUALIFY row_number() OVER (\n  PARTITION BY lower(trim(regexp_replace(text, '\\\\s+', ' '))) ORDER BY chunk_id) = 1"),
    exercise=exercise(
        title='Remove Duplicate Chunks',
        topic='rag',
        difficulty='easy',
        fn='dedupe_chunks',
        prompt="""`chunks` is a list of text pieces, like `["Hi there", "HI THERE", "Bye"]`.

Make a **key** for each chunk: lowercase it, split it into words, and join the words back with single spaces. That way extra spaces, tabs and line breaks don't change the key. Two chunks with the same key are duplicates.

Return the chunks without duplicates. Keep the first chunk for each key, exactly as it was written, in the original order.""",
        pattern="Make a key that is the same exactly when two chunks should count as the same, then remember the keys you've seen.",
        target='one pass over the chunks',
        realworld='Duplicates waste money, because every chunk is turned into an embedding (a list of numbers used for search) and you pay for each one. They also crowd retrieval: if the top 5 results are the same disclaimer five times, the model never sees the paragraph that answers the question.',
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
            case(['Hi there', 'Bye now', 'hi   there', 'BYE\nNOW'], expected=['Hi there', 'Bye now'], sample=True),
            case([], expected=[]),
            case([
                'Refunds take 5 days.',
                'All rights reserved.',
                'refunds   take 5 days.',
                """ALL RIGHTS
RESERVED.""",
            ], expected=['Refunds take 5 days.', 'All rights reserved.']),
            case(['a', 'b', 'a '], expected=['a', 'b']),
            case(['Hi there', 'hi\tthere', 'hithere'], expected=['Hi there', 'hithere']),
        ],
        guided="""def dedupe_chunks(chunks):
    # Replace every ___ with real code, then run the tests.

    seen = set()   # keys you've already kept
    out = []       # the chunks to return
    for chunk in chunks:
        # Step 1: the key: lowercase, split into words,
        # then join the words with single spaces.
        key = " ".join(___)
        # Step 2: a new key? Remember it, and add the
        # chunk to the out list.
        if key not in seen:
            seen.add(key)
            ___
    return out
""",
        fills=['chunk.lower().split()', 'out.append(chunk)'],
        concepts=[
            [
                'lower',
                'Gives a lowercase copy of a string.',
                "'Big RED Bus'.lower()   # 'big red bus'",
            ],
            [
                'split with no argument',
                'Cuts a string into words at any run of spaces, tabs or line breaks. Spaces at the ends are dropped. You can put it straight after `lower()`.',
                "'  big  red\\nbus '.split()   # ['big', 'red', 'bus']\n'Big  RED\\nBus'.lower().split()   # ['big', 'red', 'bus']",
            ],
            [
                'join',
                '`" ".join(words)` glues a list of strings back together, with one space between each.',
                """" ".join(['big', 'red', 'bus'])   # 'big red bus'""",
            ],
            [
                'A set of seen keys',
                'A set holds each value once. `add` puts a value in, and `in` checks whether it is there, instantly.',
                """seen = set()
seen.add('x')
'x' in seen   # True""",
            ],
            [
                'append',
                '`items.append(x)` adds x to the end of a list.',
                """names = []
names.append('ana')   # ['ana']""",
            ],
        ],
        byhand='Chunk 1, "Hi there", gets the key "hi there". New: keep it. Chunk 2, "Bye now", gets the key "bye now". New: keep it. Chunk 3 has a small h and extra spaces, but its key is "hi there" again: skip it. Chunk 4 has capitals and a line break (shown as \\n), but its key is "bye now" again: skip it. Return ["Hi there", "Bye now"].',
        why='One pass; each key check is a set lookup.',
        gotchas=[
            [
                'Near-duplicates',
                'Exact keys miss text that differs by a date or a name. Real pipelines also use near-duplicate detection (for example MinHash), which flags chunks that are mostly the same.',
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
        'Real systems score with **embeddings** (lists of numbers where similar meanings land close together), often combined with keyword search. The shape is the same: score, sort, keep the top k, and break ties the same way every time, so the results do not change from one run to the next and your tests stay stable.',
    ],
    example=example('Score, sort, slice', """scored = sorted(docs, key=score, reverse=True)
top = scored[:k]"""),
    check=question(
        'Why decide how ties are broken?',
        [
            'So the highest-scoring document is always returned',
            "So results don't change between runs and tests stay stable",
            'So documents with a score of 0 are dropped',
        ],
        answer=1,
        why='Without a rule, equal scores can come back in any order, which makes results and tests flaky.',
    ),
    angle=angle(
        pattern='Score, sort, keep the top k',
        text="The big idea: retrieval scores every document against the question and keeps the top k, breaking ties the same way every time. Your code turns the query into a set, a collection with no repeats, of lowercase words. For each document, `&` keeps the words found in both sets, and the score is how many there are. Each score is stored as a negative number next to the document's position. Sorting smallest first then puts the highest score first, and ties go to the earlier document. It returns the first k positions.",
        say='"I give every document a [[score|label|summary::A number for how well it matches the question.]] and keep the best k. When two tie, the [[earlier|shorter|later::Look at where each document sits in the list.]] one wins, so I get the same results every time."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: hybrid search', """from databricks.vector_search.client import VectorSearchClient
index = VectorSearchClient().get_index(endpoint_name="vs-endpoint", index_name="main.support.docs_index")
results = index.similarity_search(
    query_text=question, columns=["chunk_id", "text"],
    query_type="hybrid", num_results=5,
)"""),
    exercise=exercise(
        title='Find the Best Documents',
        topic='rag',
        difficulty='medium',
        fn='retrieve',
        prompt="""Your function gets three things:

- `query`: the search text, like `"cat food"`.
- `docs`: the documents, a list of strings like `["dog food", "cat toys"]`.
- `k`: how many results to return, like `2`.

A document's score is how many of the query's words appear in it, ignoring upper and lower case. Words are separated by spaces. Documents with a score of 0 can still be returned.

Return the positions in `docs` (counting from 0) of the `k` highest-scoring documents, best first. If two documents tie, the one that comes first in `docs` goes first. If there are fewer than `k` documents, return them all.""",
        pattern='Score every candidate, sort by score, keep the top few. Decide up front how ties are broken.',
        target='score each document once, then sort',
        realworld='Retrieval in RAG. Real systems score with embeddings instead of shared words, but the score, sort and keep-the-top-k shape is the same.',
        starter="""def retrieve(query, docs, k):
    # your code here
    pass
""",
        solution="""def retrieve(query, docs, k):
    words = set(query.lower().split())
    pairs = []
    for i, doc in enumerate(docs):
        score = len(words & set(doc.lower().split()))
        pairs.append((-score, i))
    pairs.sort()
    top = pairs[:k]
    return [pair[1] for pair in top]
""",
        cases=[
            case('cat food', ['dog food', 'cat toys', 'cat food bowl', 'birds'], 2, expected=[2, 0], sample=True),
            case('Python', ['I like python', 'Java'], 3, expected=[0, 1]),
            case('a b', [], 2, expected=[]),
            case('x y', ['y x', 'x', 'q'], 5, expected=[0, 1, 2]),
            case('The', ['the the the', 'THE end'], 1, expected=[0]),
            case('red car', ['blue car', 'red car', 'red bus'], 3, expected=[1, 0, 2]),
        ],
        guided="""def retrieve(query, docs, k):
    # Replace every ___ with real code, then run the tests.

    # The query's words, lowercase, as a set.
    words = set(query.lower().split())

    pairs = []
    for i, doc in enumerate(docs):
        # Step 1: this doc's words, lowercase, as a set.
        # & keeps the words both sets share.
        score = len(words & ___)
        # Step 2: store the pair (-score, i). The minus sign
        # puts the biggest score first when sorted.
        pairs.append(___)

    # Step 3: sort (best first), then keep the first k.
    pairs.sort()
    top = pairs[:___]
    # Return just the positions: item 1 of each pair.
    return [pair[1] for pair in top]
""",
        fills=['set(doc.lower().split())', '(-score, i)', 'k'],
        concepts=[
            [
                'lower and split',
                '`lower()` makes text lowercase. `split()` cuts it into words at spaces.',
                "'Big Red Bus'.lower().split()   # ['big', 'red', 'bus']",
            ],
            [
                'A set and &',
                'A set holds each value once. `set(a_list)` turns a list into a set, dropping repeats. `a & b` gives the values two sets share, and `len` counts them.',
                """set(['bo', 'ana', 'bo'])   # {'bo', 'ana'}
shared = {'big', 'bus'} & {'bus', 'stop'}
len(shared)   # 1""",
            ],
            [
                'enumerate',
                'Gives each item together with its position, counting from 0.',
                """for i, name in enumerate(['ana', 'bo']):
    print(i, name)   # 0 ana, then 1 bo""",
            ],
            [
                'append',
                '`items.append(x)` adds x to the end of a list. x can be a pair in round brackets.',
                """pairs = []
pairs.append((5, 'ana'))   # [(5, 'ana')]""",
            ],
            [
                'Sorting pairs',
                'Python sorts pairs by the first item, then by the second. A minus sign on the score puts the biggest score first, and on a tie the lower position comes first. `pairs.sort()` sorts the list itself.',
                """pairs = [(-1, 0), (-2, 2), (-1, 1)]
pairs.sort()
# [(-2, 2), (-1, 0), (-1, 1)]""",
            ],
            [
                'The first k items',
                '`items[:k]` keeps the first k items, or all of them if there are fewer.',
                "['a', 'b', 'c'][:2]   # ['a', 'b']",
            ],
            [
                'List comprehension',
                'Builds a new list from another one in a single line. Item 1 of a pair is its second item, because counting starts at 0.',
                """[n * 2 for n in [1, 2, 3]]   # [2, 4, 6]
[p[1] for p in [(5, 'a'), (7, 'b')]]   # ['a', 'b']""",
            ],
        ],
        byhand='Query words: cat, food. Position 0, "dog food", has food: score 1. Position 1, "cat toys", has cat: score 1. Position 2, "cat food bowl", has both: score 2. Position 3, "birds", has neither: score 0. Best first is position 2. Positions 0 and 1 tie on 1, so 0 comes before 1. k is 2, so return [2, 0].',
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
                'Stuffing many chunks into the prompt costs more and can bury the useful one. Picking a small k and reranking (using a second model to put the results in a better order) is a common pattern.',
            ],
        ],
    ),
)

lesson(MODULE, 'recall_at_k',
    title='Measuring retrieval',
    learn=[
        "A RAG answer can fail in two places: retrieval didn't find the right document, or the model didn't use it well. Measure them separately.",
        "**Recall@k** asks: of the documents that should have been found, what share made it into the top k? It needs a small set of questions where you've marked the right documents by hand.",
    ],
    example=example('Recall@3, by hand', """top 3:     d7 d2 d9
relevant:  d2 d4
found:     d2  (d4 is not in the top 3)
recall@3 = 1 found of 2 relevant = 0.5"""),
    check=question(
        'Recall@5 is 0.3 and answers are poor. What should you work on first?',
        ['The prompt', 'Retrieval', 'A bigger LLM'],
        answer=1,
        why="The model can't answer from documents it never saw. Fix retrieval first: chunking, the embedding model or k.",
    ),
    angle=angle(
        pattern='Count what the top k found',
        text='The big idea: measure retrieval on its own, by asking what share of the right documents made it into the top k. Your code returns 0 if there are no relevant documents, so it never divides by zero. Otherwise it takes the first k retrieved ids and turns them and the relevant ids into sets, collections with no repeats. `&` keeps only the ids found in both. It divides how many were found by how many were relevant. It is like checking a shopping list against what is in your basket.',
        say='"I check retrieval on its own, before the answer. Of the documents that [[should be found|were found|came first::Start from the right documents, not from what came back.]], I count what [[share|order|score::A fraction: how many turned up, divided by how many there were.]] made it into the top k."',
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
        prompt="""Your function gets three things:

- `retrieved`: the document ids your search returned, best first, like `["d7", "d2", "d9"]`.
- `relevant`: the ids it should have found, like `["d2", "d4"]`.
- `k`: how many of the top results to look at, like `3`.

Count how many of the `relevant` ids appear in the first `k` of `retrieved`. Return that count divided by the number of `relevant` ids, rounded to 2 decimal places. This is called **recall@k**.

If `relevant` is empty, return `0.0`.""",
        pattern='Take the top k, turn both lists into sets, and count what they share.',
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
    return round(len(found) / len(relevant), 2)
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

    # Nothing to find? Return 0.0.
    if not relevant:
        return 0.0
    # Step 1: the ids in the top k that are also relevant.
    # & keeps what two sets have in common.
    found = set(___) & set(relevant)
    # Step 2: how many were found, divided by how many
    # are relevant, rounded to 2 places.
    return round(___, 2)
""",
        fills=['retrieved[:k]', 'len(found) / len(relevant)'],
        concepts=[
            [
                'An empty list check',
                '`if not items:` is true when the list is empty.',
                """names = []
if not names:
    print('no names yet')""",
            ],
            [
                'The first k items',
                '`items[:k]` keeps the first k items, or all of them if there are fewer.',
                "['a', 'b'][:5]   # ['a', 'b']",
            ],
            [
                'Set intersection',
                "`set(a_list)` turns a list into a set, dropping repeats. `a & b` keeps what's in both sets. `len` counts it.",
                "set(['bo', 'ana', 'bo'])   # {'bo', 'ana'}\n{'ana', 'bo'} & {'bo', 'cy'}   # {'bo'}",
            ],
            [
                'round',
                '`round(x, 2)` rounds x to 2 decimal places.',
                "round(2 / 3, 2)   # 0.67",
            ],
        ],
        byhand='k is 3, so look at the first 3 retrieved ids: d7, d2, d9. The relevant ids are d2 and d4. d2 is in the top 3. d4 is 4th, just outside. That is 1 found out of 2 relevant. 1 divided by 2 is 0.5. Return 0.5.',
        why='One walk through the top k; set lookups are instant.',
        gotchas=[
            [
                'You need labelled questions',
                "Recall needs to know which documents are relevant. Start with 30 to 50 real questions and mark the right documents by hand; it's the most valuable hour in a RAG project.",
            ],
            [
                "Higher k isn't free",
                'Raising k usually raises recall but adds tokens, cost and latency, and can bury the right chunk among wrong ones.',
            ],
        ],
    ),
)

lesson(MODULE, 'ndcg_at_k',
    title='Ranking quality: nDCG',
    learn=[
        "Recall@k asks whether the right documents made the top k. It ignores the order inside the top k, and it treats every relevant document as equally good. When order matters, for example when comparing rerankers (models that reorder search results), use **nDCG@k**.",
        "Give each document a **relevance grade** for a question: say 0 useless, 1 related, 2 helpful, 3 answers it. A document's grade counts less the lower it appears: position 1 counts in full, position 2 about 63%, position 3 half, position 4 about 43%. Add those up to get the **DCG**, short for discounted cumulative gain: \"discounted\" because lower places count less, \"cumulative gain\" because you add up the grades.",
        'Then divide by the best possible DCG for those grades, the **ideal DCG**, where the best documents come first. So nDCG runs from 0 to 1, and 1 means perfectly ordered. Grades come from people or an LLM judge, on a sample of questions.',
        'Another common metric, MRR (mean reciprocal rank), only looks at where the first relevant document sits. nDCG uses every graded document.',
    ],
    example=example('nDCG@3, by hand', """pos  doc  grade  weight  points
 1   d3     1     100%    1.00
 2   d1     3      63%    1.89
 3   d7     0      50%    0.00
DCG = 2.89
ideal order 3, 1, 0: 3.00 + 0.63 = 3.63
nDCG@3 = 2.89 divided by 3.63
       = about 0.80"""),
    check=question(
        'Reranker A puts the best document 4th; reranker B puts it 1st. Both have the same recall@5. Which metric shows the difference?',
        ['Recall@5', 'nDCG@5', 'Neither, they are equally good'],
        answer=1,
        why='Recall@5 only asks whether the document is in the top 5. nDCG gives it far more credit at position 1 than at position 4.',
    ),
    angle=angle(
        pattern='Compare to the best order',
        text='The big idea: recall@k ignores order, so nDCG gives each document a grade and counts it less the lower it appears. Your code first lists the grades of the top `k` results, using 0 for any id with no grade. Then it builds the best possible list: all the grades sorted from highest to lowest, cut to `k`. Sorting just means putting things in order. It divides the `dcg` of your list by the `dcg` of the best list, so 1.0 means perfectly ordered. If the best list scores 0, it returns 0.0.',
        say='"Recall@k doesn\'t care about [[order|size|cost::Whether the best document is first or fifth.]], so I use nDCG. I score my list, then divide by the score of the [[best possible|average|first::Imagine every result sorted perfectly.]] order, so 1 means perfect."',
        classic=None,
    ),
    stack=stack('scikit-learn: nDCG on graded relevance', """from sklearn.metrics import ndcg_score

# one row per question: true grades and the retriever's scores, in the same document order
ndcg = ndcg_score([[3, 1, 0]], [[0.7, 0.9, 0.2]], k=3)
mlflow.log_metric("ndcg_at_3", ndcg)"""),
    exercise=exercise(
        title='nDCG at k',
        topic='rag',
        difficulty='medium',
        fn='ndcg_at_k',
        prompt="""Your function gets three things:

- `ranked`: the ids your search returned, best first, like `["d3", "d1", "d7"]`.
- `grades`: a dict giving some ids a usefulness number, like `{"d1": 3, "d3": 1}`. Bigger is more useful. Ids not in it have grade 0.
- `k`: how many top results to score, like `3`.

The helper `dcg(grade_list)` is written for you. Grades lower in the list count less.

- List the grades of the first `k` ids in `ranked`, in order.
- Make the best possible list: every value in `grades`, highest first, keeping the first `k`.
- Return `dcg` of the first list divided by `dcg` of the second, rounded to 2 decimal places. If `dcg` of the second is 0, return `0.0`.""",
        pattern='Score what you got, score the best possible order, then divide one by the other.',
        target='one sort of the grades, then two short walks',
        realworld='Retrieval and search teams compare embedding models and rerankers on nDCG@10 with graded relevance, because the order of the first few results is what users and LLMs actually read.',
        starter="""import math

def dcg(grade_list):
    # Written for you. Adds up the grades: the 1st counts
    # in full, the 2nd about 63%, the 3rd half, and so on.
    total = 0.0
    for i, grade in enumerate(grade_list):
        total += grade / math.log(i + 2, 2)
    return total


def ndcg_at_k(ranked, grades, k):
    # your code here
    pass
""",
        solution="""import math

def dcg(grade_list):
    total = 0.0
    for i, grade in enumerate(grade_list):
        total += grade / math.log(i + 2, 2)
    return total


def ndcg_at_k(ranked, grades, k):
    got = []
    for doc in ranked[:k]:
        got.append(grades.get(doc, 0))
    best = sorted(grades.values(), reverse=True)[:k]
    if dcg(best) == 0:
        return 0.0
    return round(dcg(got) / dcg(best), 2)
""",
        cases=[
            case(['d3', 'd1', 'd7'], {'d1': 3, 'd3': 1}, 3, expected=0.8, sample=True),
            case(['a', 'b'], {'a': 2, 'b': 1}, 2, expected=1.0),
            case(['x', 'y'], {'a': 3}, 2, expected=0.0),
            case(['a'], {}, 1, expected=0.0),
            case(['b', 'a', 'c'], {'a': 3, 'b': 2, 'c': 1}, 1, expected=0.67),
            case(['c', 'b', 'a'], {'a': 3, 'b': 2, 'c': 1}, 3, expected=0.79),
        ],
        guided="""import math

def dcg(grade_list):
    # Written for you. Adds up the grades: the 1st counts
    # in full, the 2nd about 63%, the 3rd half, and so on.
    total = 0.0
    for i, grade in enumerate(grade_list):
        total += grade / math.log(i + 2, 2)
    return total


def ndcg_at_k(ranked, grades, k):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the grades of the first k ranked ids, in
    # order. An id missing from grades has grade 0.
    got = []
    for doc in ranked[:k]:
        got.append(___)

    # Step 2: the best possible order. Sort every value
    # in grades (not only your top k), highest first,
    # then keep the first k.
    best = sorted(___, reverse=True)[:k]

    # Step 3: divide the two scores, unless the best
    # possible score is 0.
    if dcg(best) == 0:
        return 0.0
    return round(___, 2)
""",
        fills=['grades.get(doc, 0)', 'grades.values()', 'dcg(got) / dcg(best)'],
        concepts=[
            [
                'get with a default',
                '`d.get(key, 0)` gives the value for key, or 0 if the key is missing.',
                """ages = {'ana': 30}
ages.get('bo', 0)   # 0""",
            ],
            [
                'append',
                '`items.append(x)` adds x to the end of a list.',
                """ages = []
ages.append(30)   # [30]""",
            ],
            [
                'Sorting values, highest first',
                '`d.values()` gives the values of a dict without the keys. `sorted(..., reverse=True)` puts them biggest first.',
                """sorted({'a': 1, 'b': 3}.values(), reverse=True)
# [3, 1]""",
            ],
            [
                'The first k items',
                '`items[:k]` keeps the first k items, or all of them if there are fewer.',
                "[9, 4, 2][:2]   # [9, 4]",
            ],
            [
                'round',
                '`round(x, 2)` rounds x to 2 decimal places.',
                "round(2 / 3, 2)   # 0.67",
            ],
            [
                'enumerate (used inside dcg)',
                'Gives each item together with its position, counting from 0.',
                """for i, name in enumerate(['ana', 'bo']):
    print(i, name)   # 0 ana, then 1 bo""",
            ],
        ],
        byhand='The first 3 ranked ids are d3, d1, d7. Their grades are 1, 3 and 0 (d7 is not in grades). dcg([1, 3, 0]) counts 1 in full (1), 3 at about 63% (1.89) and 0 at half (0). Total: about 2.89. The best order uses every value in grades, highest first: [3, 1]. That is fewer than 3 values, so keep both. dcg([3, 1]) counts 3 in full (3) and 1 at about 63% (0.63). Total: about 3.63. 2.89 divided by 3.63 is about 0.797. Rounded to 2 places that is 0.80, which Python shows as 0.8. Return 0.8.',
        why='Sorting the grades is the slowest step; each walk looks at k items.',
        gotchas=[
            [
                'Grade the same way every time',
                'nDCG is only comparable across runs if the grades come from the same rubric and the same judge.',
            ],
            [
                'Variants exist',
                'Some versions use 2 to the power of the grade, minus 1, instead of the grade itself. That rewards the very best documents more. Say which one you used.',
            ],
        ],
    ),
)

lesson(MODULE, 'rerank_check',
    title='Did the reranker help?',
    learn=[
        "A **reranker** takes the retriever's candidates, say the top 20, and puts them in a better order, so the top few that reach the model are the most useful. It costs time on every request, so measure what it actually does.",
        "First check whether the right document was among the candidates at all. If retrieval missed it, no reranker can bring it back. That question is **out of reach**: the right document never came back from retrieval (engineers call this a retrieval miss), so the fix belongs in retrieval: chunking, embeddings, hybrid search. Only then compare the top k before and after reranking, on the same candidate lists.",
        "Count four outcomes per question: **helped** (the right document entered the top k), **hurt** (it was pushed out), **no change**, and **out of reach**. If most misses are out of reach, a better reranker won't help, and you have learned where to spend effort next.",
    ],
    example=example('Before and after, on the same candidates', """question        right doc   top 3 before        top 3 after        outcome
return-label    d12         d4 d9 d1            d12 d4 d9          helped
change-address  d7          d7 d2 d5            d2 d5 d11          hurt
refund-time     d3          d3 d8 d1            d3 d1 d8           no change
gift-card       d40         (not in top 20)                        out of reach"""),
    check=question(
        "Half of your RAG app's misses are questions where the right document isn't in the retriever's top 20. Will a better reranker fix them?",
        [
            'Yes: a better reranker brings in documents retrieval missed',
            "No: a reranker only reorders the candidates it's given",
            'Only if you rerank the top 3 instead of the top 20',
        ],
        answer=1,
        why='Out-of-reach misses need better retrieval: chunking, embeddings, hybrid search, or more candidates.',
    ),
    angle=angle(
        pattern='Sort each question into four piles',
        text='The big idea: a reranker can only reorder what retrieval found, so first check whether the right document was found at all. Your code starts a dict, a lookup table from each outcome name to its count, with all four at 0. For each question, if the right document is missing from `before`, it counts as out of reach and the code moves on. Otherwise it asks two things: was it in the top `k` before, and is it in the top `k` after? Those two answers decide helped, hurt or no change.',
        say='"A reranker can only [[reorder|replace|find::It shuffles what is already there.]] what retrieval found. So first I count the questions where the right document was [[missing|ranked first|duplicated::No reranker can fix a document that never came back.]]. Then I count helped, hurt and no change."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: retrieve wide, rerank, keep a few', """results = index.similarity_search(query_text=question, columns=["id", "text"], num_results=20)
candidates = [row[0] for row in results["result"]["data_array"]]
reranked = rerank(question, candidates)          # your reranker: a model that scores each (question, chunk) pair, or an LLM
mlflow.log_metric("out_of_reach", int(gold not in candidates))"""),
    exercise=exercise(
        title='What Did the Reranker Do?',
        topic='rag',
        difficulty='medium',
        fn='rerank_check',
        prompt="""Your function gets two things:

- `questions`: one dict per question, with three keys. `gold` is the right document id (the **gold label**: the answer you know is right), like `"d12"`. `before` is the search results, best first, like `["d4", "d9", "d12"]`. `after` is the same ids, reordered by the reranker.
- `k`: how many top results count, like `2`.

Give each question one outcome, checking in this order:

- `"out_of_reach"`: gold is not in `before` at all.
- `"helped"`: gold is in the first `k` of `after`, but not in the first `k` of `before`.
- `"hurt"`: gold is in the first `k` of `before`, but not in the first `k` of `after`.
- `"no_change"`: anything else.

Return a dict counting each outcome. Include all four, even at 0.""",
        pattern='One pass, checking whether the right document is in the candidates and in each top k.',
        target='one pass over the questions',
        realworld='This split tells a RAG team whether to tune the reranker or fix retrieval, and stops weeks of reranker tuning on misses it could never fix.',
        starter="""def rerank_check(questions, k):
    # your code here
    pass
""",
        solution="""def rerank_check(questions, k):
    counts = {"helped": 0, "hurt": 0,
              "no_change": 0, "out_of_reach": 0}
    for question in questions:
        gold = question["gold"]
        if gold not in question["before"]:
            counts["out_of_reach"] += 1
            continue
        was_in = gold in question["before"][:k]
        now_in = gold in question["after"][:k]
        if now_in and not was_in:
            counts["helped"] += 1
        elif was_in and not now_in:
            counts["hurt"] += 1
        else:
            counts["no_change"] += 1
    return counts
""",
        cases=[
            case([
                {'gold': 'd12', 'before': ['d4', 'd9', 'd12'], 'after': ['d12', 'd4', 'd9']},
                {'gold': 'd7', 'before': ['d7', 'd2', 'd5'], 'after': ['d2', 'd5', 'd7']},
                {'gold': 'd3', 'before': ['d3', 'd8', 'd1'], 'after': ['d8', 'd3', 'd1']},
                {'gold': 'd40', 'before': ['d1', 'd2', 'd3'], 'after': ['d2', 'd1', 'd3']},
            ], 2, expected={'helped': 1, 'hurt': 1, 'no_change': 1, 'out_of_reach': 1}, sample=True),
            case([
                {'gold': 'd12', 'before': ['d4', 'd9', 'd1', 'd12'], 'after': ['d12', 'd4', 'd9', 'd1']},
                {'gold': 'd7', 'before': ['d7', 'd2', 'd5', 'd11'], 'after': ['d2', 'd5', 'd11', 'd7']},
                {'gold': 'd3', 'before': ['d3', 'd8', 'd1'], 'after': ['d3', 'd1', 'd8']},
                {'gold': 'd40', 'before': ['d1', 'd2', 'd3'], 'after': ['d2', 'd1', 'd3']},
            ], 3, expected={'helped': 1, 'hurt': 1, 'no_change': 1, 'out_of_reach': 1}),
            case([], 3, expected={'helped': 0, 'hurt': 0, 'no_change': 0, 'out_of_reach': 0}),
            case([{'gold': 'a', 'before': ['b', 'a'], 'after': ['b', 'a']}], 1, expected={'helped': 0, 'hurt': 0, 'no_change': 1, 'out_of_reach': 0}),
            case([{'gold': 'a', 'before': ['b', 'c', 'a'], 'after': ['a', 'b', 'c']}, {'gold': 'z', 'before': [], 'after': []}], 1,
                 expected={'helped': 1, 'hurt': 0, 'no_change': 0, 'out_of_reach': 1}),
        ],
        guided="""def rerank_check(questions, k):
    # Replace every ___ with real code, then run the tests.
    counts = {"helped": 0, "hurt": 0,
              "no_change": 0, "out_of_reach": 0}
    for question in questions:
        gold = question["gold"]
        # Step 1: gold not in before at all? Out of reach.
        if ___:
            counts["out_of_reach"] += 1
            continue
        # Step 2: is gold in the top k, before and after?
        was_in = gold in question["before"][:k]
        now_in = ___
        if now_in and not was_in:
            counts["helped"] += 1
        elif was_in and not now_in:
            counts["hurt"] += 1
        else:
            counts["no_change"] += 1
    return counts
""",
        fills=['gold not in question["before"]', 'gold in question["after"][:k]'],
        concepts=[
            [
                'in and not in',
                '`x in items` is True if x is somewhere in the list. `x not in items` is the opposite.',
                """'bo' in ['ana', 'bo']       # True
'cy' not in ['ana', 'bo']   # True""",
            ],
            [
                'The first k items',
                '`items[:k]` keeps the first k items, or all of them if there are fewer.',
                "['a', 'b', 'c'][:2]   # ['a', 'b']",
            ],
            [
                'continue',
                'Skips the rest of this turn of the loop and moves on to the next item.',
                """for n in [1, -2, 3]:
    if n < 0:
        continue   # skips -2, goes on to 3""",
            ],
        ],
        byhand='k is 2. Question 1: gold d12 is 3rd before, outside the top 2, and 1st after: helped. Question 2: gold d7 is 1st before and 3rd after: hurt. Question 3: gold d3 is 1st before and 2nd after, in the top 2 both times: no change. Question 4: gold d40 is not in before at all: out of reach. Return {"helped": 1, "hurt": 1, "no_change": 1, "out_of_reach": 1}.',
        why='One pass, with short membership checks on each list.',
        gotchas=[
            [
                'Same candidates, or it is not a reranker test',
                'Compare before and after on exactly the same candidate lists. If retrieval changed too, you cannot tell which change did what.',
            ],
            [
                'Measure the time it adds',
                'A reranker that helps 3% of questions but adds a second to every request may not be worth it. Log how long it takes on each request and put that in the decision rule.',
            ],
        ],
    ),
)

lesson(MODULE, 'abstention_rates',
    title='Knowing when not to answer',
    learn=[
        "Retrieval always finds *something*, even when your documents don't contain the answer. A model handed weak chunks will often answer anyway, confidently. If every question in your eval set can be answered from your documents, you never measure this. Declining to answer on purpose is called **abstention**.",
        "So put **unanswerable questions** in the eval set on purpose: questions on nearby topics that your documents really don't cover, written by someone who knows the documents. Then measure two rates separately. **Missed refusals**: of the unanswerable questions, how often did it answer anyway? That's the dangerous one. **Over-refusals**: of the answerable questions, how often did it decline? That's the annoying one.",
        "There is no standard name or formula for this yet; these two rates are a practical choice. They pull against each other: pushing one rate down usually pushes the other up. So decide which matters more for your app before you tune.",
    ],
    example=example('Two rates, two kinds of mistake', """unanswerable: 10 questions, answered anyway 3   → missed refusals 30%
answerable:   40 questions, declined 2          → over-refusals    5%"""),
    check=question(
        'Your RAG app never declines to answer. Is that good news?',
        [
            'Yes: it always helps',
            "Only if no question is ever outside your documents. Otherwise it's making answers up",
            "It doesn't matter as long as its answers match the retrieved chunks",
        ],
        answer=1,
        why='Real users ask things your documents do not cover. An app that never declines is answering those from thin air.',
    ),
    angle=angle(
        pattern='Two groups, each with its own count',
        text="The big idea: put unanswerable questions in the eval on purpose and measure two mistakes separately, because they pull against each other. Your code goes through the results one by one with four counters, running counts that go up by one. Answerable questions add to one group, plus a mistake if the app declined. Unanswerable ones add to the other group, plus a mistake if the app answered anyway. Then it divides each mistake count by its group's size. An empty group gets a rate of 0.0, so the code never divides by zero.",
        say='"I add [[unanswerable|easy|long::There is nothing in the documents to answer these.]] questions on purpose. Then I count two mistakes [[separately|together|once::They pull against each other, so each gets its own number.]]: declining a real question, and [[answering|declining|repeating::Here the app should have said it doesn\'t know.]] one it can\'t."',
        classic=None,
    ),
    stack=stack('MLflow: a judge for declining when the context is missing', """from mlflow.genai.scorers import Guidelines

declines = Guidelines(
    name="declines_when_unsupported",
    guidelines="If the retrieved context does not contain the answer, the response must say it does not know.",
)
mlflow.genai.evaluate(data=eval_set, predict_fn=rag_app, scorers=[declines])"""),
    exercise=exercise(
        title='Did It Know When Not to Answer?',
        topic='rag',
        difficulty='easy',
        fn='abstention_rates',
        prompt="""`results` has one dict per eval question, like `{"answerable": True, "declined": False}`. `answerable` says whether your documents contain the answer. `declined` says whether the app refused to answer.

Return a dict with two rates, each rounded to 2 decimal places:

- `"missed_refusals"`: how many unanswerable questions the app answered anyway, divided by how many unanswerable questions there are.
- `"over_refusals"`: how many answerable questions the app declined, divided by how many answerable questions there are.

If there are no questions of a kind, its rate is `0.0`.""",
        pattern='Count two groups and their mistakes in one pass, then divide, taking care with a group that is empty.',
        target='one pass over the results',
        realworld='A support bot that invents a refund policy is worse than one that says "I don\'t know, let me connect you". Measuring missed refusals is how you find out which one you built.',
        starter="""def abstention_rates(results):
    # your code here
    pass
""",
        solution="""def abstention_rates(results):
    unanswerable = 0
    answered_anyway = 0
    answerable = 0
    declined_wrongly = 0
    for result in results:
        if result["answerable"]:
            answerable += 1
            if result["declined"]:
                declined_wrongly += 1
        else:
            unanswerable += 1
            if not result["declined"]:
                answered_anyway += 1
    missed = answered_anyway / unanswerable if unanswerable else 0.0
    over = declined_wrongly / answerable if answerable else 0.0
    return {
        "missed_refusals": round(missed, 2),
        "over_refusals": round(over, 2),
    }
""",
        cases=[
            case([
                {'answerable': False, 'declined': False},
                {'answerable': False, 'declined': True},
                {'answerable': True, 'declined': False},
                {'answerable': True, 'declined': False},
                {'answerable': True, 'declined': True},
            ], expected={'missed_refusals': 0.5, 'over_refusals': 0.33}, sample=True),
            case([
                {'answerable': False, 'declined': False},
                {'answerable': False, 'declined': True},
                {'answerable': False, 'declined': False},
                {'answerable': False, 'declined': True},
                {'answerable': False, 'declined': True},
                {'answerable': True, 'declined': False},
                {'answerable': True, 'declined': True},
                {'answerable': True, 'declined': False},
                {'answerable': True, 'declined': False},
                {'answerable': True, 'declined': False},
            ], expected={'missed_refusals': 0.4, 'over_refusals': 0.2}),
            case([], expected={'missed_refusals': 0.0, 'over_refusals': 0.0}),
            case([{'answerable': True, 'declined': False}] * 4, expected={'missed_refusals': 0.0, 'over_refusals': 0.0}),
            case([{'answerable': False, 'declined': False}] * 3, expected={'missed_refusals': 1.0, 'over_refusals': 0.0}),
            case([
                {'answerable': False, 'declined': True},
                {'answerable': False, 'declined': True},
                {'answerable': False, 'declined': False},
                {'answerable': True, 'declined': True},
            ], expected={'missed_refusals': 0.33, 'over_refusals': 1.0}),
        ],
        guided="""def abstention_rates(results):
    # Replace every ___ with real code, then run the tests.
    unanswerable = 0
    answered_anyway = 0
    answerable = 0
    declined_wrongly = 0

    # Step 1: count each kind of question and its mistakes.
    for result in results:
        if result["answerable"]:
            answerable += 1
            if result["declined"]:
                declined_wrongly += 1
        else:
            unanswerable += 1
            # It should decline. Did it answer instead?
            if ___:
                answered_anyway += 1

    # Step 2: divide, unless that kind has no questions.
    missed = answered_anyway / unanswerable if unanswerable else 0.0
    over = ___
    return {
        "missed_refusals": round(missed, 2),
        "over_refusals": round(over, 2),
    }
""",
        fills=['not result["declined"]', 'declined_wrongly / answerable if answerable else 0.0'],
        concepts=[
            [
                'True or False fields',
                '`if task["done"]:` runs when the field is True. `if not task["done"]:` runs when it is False.',
                """task = {'done': False}
if not task['done']:
    print('still to do')""",
            ],
            [
                'A guarded division',
                'Divide only when the bottom number is not 0, all in one line. If it is 0, you get 0.0 instead.',
                """rate = mistakes / total if total else 0.0""",
            ],
            [
                'round',
                '`round(x, 2)` rounds x to 2 decimal places.',
                "round(1 / 3, 2)   # 0.33",
            ],
        ],
        byhand='Questions 1 and 2 are unanswerable. The app answered question 1 anyway and declined question 2. Missed refusals: 1 out of 2, which is 0.5. Questions 3, 4 and 5 are answerable. The app declined only question 5. Over-refusals: 1 out of 3, which is 0.333..., rounded to 0.33. Return {"missed_refusals": 0.5, "over_refusals": 0.33}.',
        why='One step per result.',
        gotchas=[
            [
                'Write unanswerable questions carefully',
                'They should be close to what your documents cover, not obviously off-topic. "What is the capital of France?" tests nothing useful in a billing bot.',
            ],
            [
                'Report both, always',
                'Cutting missed refusals is easy if you let over-refusals climb: an app that declines everything never makes anything up.',
            ],
        ],
    ),
)

lesson(MODULE, 'claim_gate',
    title='Checking each claim before release',
    learn=[
        'Evals check quality before release, on a fixed set. A **groundedness check** runs on every answer at request time, before the user sees it; this lesson calls it a claim gate.',
        'The model writes one short statement (a **claim**) per line, each citing the passage it came from. A **verifier** labels each claim **supported**, **unsupported** or **contradicted** by its passage. The verifier is an LLM judge, or a small model trained to say whether one sentence follows from another (an NLI model, short for natural language inference).',
        'A gate then decides: **release** if every claim is supported, **revise** by dropping the unsupported claims, or **abstain** ("I couldn\'t verify an answer") if nothing is supported. A safe policy also abstains if any claim is **contradicted**, because a contradiction means the answer says the opposite of its source.',
        'Know its limits. **Supported is not relevant**: a claim can match its passage and still not answer the question. A claim with the **wrong citation** gets dropped even when it is true. **Dropping** a claim can change the meaning, for example by removing a "do not". And the verifier is a judge, so check it against human labels like any judge. The share of answers revised or abstained also makes a good monitoring signal.',
    ],
    example=example('One answer through the gate', """claim                                              cites  verdict
Refunds go to your original payment method.         [2]    supported
They arrive within 5 to 7 business days.            [2]    supported
You can also get store credit instead.              [3]    unsupported
→ revise: drop the third claim, release the first two with their citations"""),
    check=question(
        'A customer asks how long refunds take. Every claim in the answer is "supported", but they are all about shipping times. What does that tell you?',
        [
            'The gate is broken: it should have failed every claim',
            'Supported is not the same as relevant to the question',
            'The answer is fine: every claim passed the gate',
        ],
        answer=1,
        why='The verifier only compares each claim with its own passage. Whether that passage answers the question is a separate relevance check, and this answer would fail it.',
    ),
    angle=angle(
        pattern='Keep supported claims, then decide',
        text='The big idea: a claim gate, a groundedness check, checks each statement at request time, before the user sees the answer. Your code goes through the verdicts once. It keeps the text of every supported claim in a list and notes if any claim is contradicted. Then it decides. Any contradiction, or nothing supported, means abstain and keep nothing. If every claim was supported, it releases them all. Otherwise it revises, keeping only the supported claims in their original order. An empty list has nothing supported, so it abstains too.',
        say='"Before the user sees an answer, I check each [[claim|word|source::A single statement the answer makes.]]. All supported, I send it. Some supported, I [[keep only those|send it all|drop it all::Cut the parts with no backing.]]. Otherwise I abstain."',
        classic=None,
    ),
    stack=stack('MLflow: log the gate\'s decision on the trace', """with mlflow.start_span(name="claim_gate", span_type="GUARDRAIL") as span:
    decision = claim_gate(verdicts)
    span.set_outputs(decision)
mlflow.update_current_trace(tags={"gate_action": decision["action"]})"""),
    exercise=exercise(
        title='Release, Revise or Abstain',
        topic='rag',
        difficulty='easy',
        fn='claim_gate',
        prompt="""`verdicts` has one dict per claim (one short statement in the answer), like `{"claim": "Refunds take 5 days.", "verdict": "supported"}`. The verdict is `"supported"`, `"unsupported"` or `"contradicted"`.

Return a dict like `{"action": "revise", "kept": [...]}`, where `kept` is a list of claim texts. Pick the action like this:

- `"abstain"`, keeping nothing, if any claim is contradicted or no claim is supported. An empty `verdicts` list also gives abstain.
- `"release"`, keeping every claim, if all claims are supported.
- `"revise"` otherwise, keeping only the supported claims, in their original order.""",
        pattern='One walk collecting supported claims and spotting contradictions, then three outcomes.',
        target='one pass over the claims',
        realworld='Clinical, legal and finance RAG systems put a gate like this after generation, so an unsupported statement never reaches the user.',
        practice=practice(
            intro='Read the verifier\'s verdicts the way a groundedness check does: release, revise or abstain, before the user sees the answer.',
            explain='A claim gate checks each statement at request time, before the user sees the answer. You kept the supported claims, abstained on any contradiction or when nothing was supported, and released only when every claim was backed. You also saw its limits: dropping a claim can change what the answer means, and a rising share of revise and abstain is a warning worth watching.',
            asks=[
                ask('What does the gate do with this answer?', ['Release: every claim has a citation', 'Revise: drop the store-credit claim', 'Abstain: one claim has no backing'], answer=1,
                    evidence=evidence('code', title='The verifier\'s verdicts', text="""claim                                        cites  verdict
Refunds go to your original payment method.  [2]    supported
They arrive within 5 to 7 business days.     [2]    supported
You can also get store credit instead.       [3]    unsupported"""),
                    clue='Two of the three claims are backed by their passage, and nothing is contradicted.',
                    why='Not every claim is supported, so it can\'t go out whole. Something is supported and nothing is contradicted, so drop the unsupported claim and send the other two with their citations.',
                    wrong=['A citation isn\'t backing: one claim isn\'t supported by its passage. Should the user see it?', None, 'Abstain is for when nothing is supported or something is contradicted. Two claims are fine here.']),
                ask('This time the verifier marks the second claim **contradicted**: passage [2] says 10 business days. What does the gate do?', ['Revise: keep only the first claim', 'Abstain'], answer=1,
                    evidence=evidence('code', title='The verifier\'s verdicts', text="""claim                                        cites  verdict
Refunds go to your original payment method.  [2]    supported
They arrive within 5 to 7 business days.     [2]    contradicted"""),
                    clue='A safe policy treats a contradiction differently from a claim that simply has no backing.',
                    why='A contradiction means the answer says the opposite of its source, so something went wrong in writing it. A safe gate says "I couldn\'t verify an answer" rather than sending half of it.',
                    wrong=['Dropping it hides a sign the answer went wrong. What does a safe policy do on any contradiction?', None]),
                ask('The gate revises this answer and sends only the first claim. What should worry you?', ['Nothing: every claim it sent is backed by its passage', 'Without the warning, the answer now says something else', 'The first claim should be dropped too, to stay safe'], answer=1,
                    evidence=evidence('code', title='The verifier\'s verdicts', text="""claim                                        cites  verdict
You can return the laptop within 30 days.    [1]    supported
Do not return it if the seal is broken.      [3]    unsupported"""),
                    clue='Read the answer the user gets once the second line is gone.',
                    why='The rules say revise, but the user now hears "you can return it" with no "do not". The second claim may also be true with the wrong citation. Check dropped claims that carry a warning before you trust a revise.',
                    wrong=['Each claim it sent is supported, but what does the whole answer now say?', None, 'Its passage backs it, so the gate keeps it.']),
                ask('On Wednesday, far more answers are revised or abstained. What do you look at first?', ['Retrieval and the documents: did something change?', 'Turn the gate off: it has become too strict', 'Nothing: users still get an answer of some kind'], answer=0,
                    evidence=evidence('code', title='gate_action on each trace, out of 100 answers a day', text="""action    Mon  Tue  Wed
release    82   80   51
revise     15   16   31
abstain     3    4   18"""),
                    clue='The gate only checks claims against the passages it was handed.',
                    why='A jump in revise and abstain is an early warning that retrieval or the documents changed, so the passages no longer back the answers. Logging the action on every trace is what lets you see it.',
                    wrong=[None, 'The gate is doing its job: stopping answers with no backing. Why did backing get rarer?', 'Eighteen people a day now hear "I couldn\'t verify an answer". Something changed.']),
            ],
        ),
        starter="""def claim_gate(verdicts):
    # your code here
    pass
""",
        solution="""def claim_gate(verdicts):
    kept = []
    contradicted = False
    for item in verdicts:
        if item["verdict"] == "supported":
            kept.append(item["claim"])
        elif item["verdict"] == "contradicted":
            contradicted = True
    if contradicted or not kept:
        return {"action": "abstain", "kept": []}
    if len(kept) == len(verdicts):
        return {"action": "release", "kept": kept}
    return {"action": "revise", "kept": kept}
""",
        cases=[
            case([
                {'claim': 'Refunds go to your card.', 'verdict': 'supported'},
                {'claim': 'They take 5 to 7 days.', 'verdict': 'supported'},
                {'claim': 'You can get store credit.', 'verdict': 'unsupported'},
            ], expected={'action': 'revise', 'kept': ['Refunds go to your card.', 'They take 5 to 7 days.']}, sample=True),
            case([{'claim': 'A', 'verdict': 'supported'}, {'claim': 'B', 'verdict': 'supported'}], expected={'action': 'release', 'kept': ['A', 'B']}),
            case([{'claim': 'A', 'verdict': 'supported'}, {'claim': 'B', 'verdict': 'contradicted'}], expected={'action': 'abstain', 'kept': []}),
            case([{'claim': 'A', 'verdict': 'unsupported'}], expected={'action': 'abstain', 'kept': []}),
            case([], expected={'action': 'abstain', 'kept': []}),
        ],
        guided="""def claim_gate(verdicts):
    # Replace every ___ with real code, then run the tests.
    kept = []              # the supported claims
    contradicted = False   # seen a contradiction yet?
    for item in verdicts:
        if item["verdict"] == "supported":
            kept.append(item["claim"])
        elif item["verdict"] == "contradicted":
            contradicted = True

    # Step 1: any contradiction, or nothing kept? Abstain.
    if ___:
        return {"action": "abstain", "kept": []}
    # Step 2: every claim kept? Release them all.
    if ___:
        return {"action": "release", "kept": kept}
    # Otherwise some were dropped: revise.
    return {"action": "revise", "kept": kept}
""",
        fills=['contradicted or not kept', 'len(kept) == len(verdicts)'],
        concepts=[
            [
                'A flag inside a loop',
                'Start a variable as False and set it to True when something happens. After the loop it tells you whether it ever did.',
                """seen = False
for x in [1, 5, 2]:
    if x > 4: seen = True   # True after the loop""",
            ],
            [
                'An empty list counts as False',
                '`not items` is True when the list is empty.',
                """names = []
not names   # True""",
            ],
            [
                'The word or',
                '`x or y` is True when at least one of them is True.',
                """n = 0
n == 0 or n > 5   # True""",
            ],
            [
                'Comparing lengths',
                '`len(a) == len(b)` is True when two lists have the same number of items.',
                """len(['x', 'y']) == len([1, 2])   # True""",
            ],
        ],
        byhand='Claim 1 is supported: keep it. Claim 2 is supported: keep it. Claim 3 is unsupported: drop it. No claim is contradicted and 2 were kept, so do not abstain. Only 2 of the 3 claims were kept, so do not release. That leaves revise. Return {"action": "revise", "kept": ["Refunds go to your card.", "They take 5 to 7 days."]}.',
        why='One look at each claim.',
        gotchas=[
            [
                'Measure the gate itself',
                'Label a sample of claims by hand and check how often the verifier agrees with you, verdict by verdict. A verifier that marks too much "supported" lets errors through; one that marks too much "unsupported" makes the app abstain needlessly.',
            ],
            [
                'Watch the abstain rate',
                'Log the action on every trace. A rising share of revise or abstain is an early warning that retrieval or the documents changed.',
            ],
        ],
    ),
)

lesson(MODULE, 'pick_config',
    title='Designing a RAG experiment',
    learn=[
        'The settings that matter most in RAG: **chunk size** and **overlap**, **k** (how many chunks go into the prompt), the **embedding model**, and whether you **rerank**. Try a few values of one or two of them, keeping everything else fixed. If you vary two, try every combination (a **grid search**), so you can see what each one did.',
        'Hold the eval set, the judge and the answering model fixed. Log retrieval quality, answer quality, p95 latency (how slow it is: 95 out of 100 requests are faster than this) and cost for every run. Then pick a **config** (one combination of settings) using the rule you wrote down: best answer quality within the latency budget, the slowest you can accept.',
    ],
    example=example('Two settings, every combination, a 1500 ms budget', """chunk  k  quality  p95 ms
 512   3   0.78    1200
 512   5   0.82    1400
1024   3   0.83    1700  too slow
1024   5   0.85    2600  too slow
fast enough and best: 512, 5"""),
    check=question(
        'Your best-quality config has a p95 of 2.6 seconds; the product needs under 1.5. What do you ship?',
        ['The best-quality config anyway', 'The best config within 1.5 seconds', 'The fastest config'],
        answer=1,
        why="A config that is too slow for the product can't ship, however good it is. Pick the best quality inside the budget.",
    ),
    angle=angle(
        pattern='Skip the slow ones, keep the best',
        text="The big idea: pick a config with the rule you wrote down: best answer quality within the latency budget. Your code goes through the rows one by one and skips any row slower than `max_ms`. It remembers the best row so far, like holding the tallest card you have seen and swapping when a taller one turns up. A row takes its place if its quality is higher, or equal with a lower cost. At the end it returns that row's `chunk_size` and `k`, or `None` if no row was fast enough.",
        say='"I drop every config that\'s [[too slow|too cheap|too big::It goes over the time limit.]], then pick the one with the best [[quality|speed|price::How good the answers are.]]. If two tie, I take the [[cheaper|faster|newer::Look at what each one costs.]] one."',
        classic=None,
    ),
    stack=stack('MLflow: one evaluated run per config', """from mlflow.genai.scorers import RelevanceToQuery, RetrievalGroundedness

for chunk_size in [256, 512, 1024]:
    for k in [3, 5, 10]:   # every combination: 9 runs
        with mlflow.start_run(run_name=f"cs{chunk_size}-k{k}"):
            mlflow.log_params({"chunk_size": chunk_size, "k": k})
            mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(chunk_size, k),
                                  scorers=[RetrievalGroundedness(), RelevanceToQuery()])"""),
    exercise=exercise(
        title='Choose Chunk Size and k',
        topic='rag',
        difficulty='medium',
        fn='pick_config',
        prompt="""Your function gets two things:

- `results`: a list of rows, one dict per setting you tried, like `{"chunk_size": 512, "k": 5, "quality": 0.82, "p95_ms": 1400, "cost": 2.1}`. `p95_ms` is how slow it was, in milliseconds: 95 out of 100 requests were faster than this.
- `max_ms`: the slowest you can accept, like `1500`.

Skip every row whose `p95_ms` is over `max_ms`. Of the rest, pick the row with the highest `quality`. If two rows tie on quality, pick the one with the lower `cost`.

Return `[chunk_size, k]` from that row, or `None` if no row is fast enough.""",
        pattern='Skip what breaks the budget, pick the best of the rest, and break ties on cost.',
        target='one walk through the results',
        realworld="Teams often pick the highest-quality config and discover it's too slow for the product. Deciding the latency budget up front, then maximising quality inside it, is how you get a config you can actually ship.",
        practice=practice(
            intro='Read the experiment results the way a reviewer does: drop what breaks the latency budget, then pick the best of the rest.',
            explain='You picked a config with the rule written down first: best answer quality within the latency budget. You dropped every row slower than the budget, kept the best quality of the rest, and broke a tie on cost. And you only trusted a comparison where one or two settings changed and everything else stayed fixed.',
            asks=[
                ask('Which configs are too slow for the 1500 ms budget?', ['Only 1024, 5', 'Both 1024 rows', 'None of them'], answer=1,
                    evidence=evidence('code', title='Every combination of two settings', text="""budget: p95 under 1500 ms

chunk  k  quality  p95 ms  cost
 512   3   0.78    1200    1.4
 512   5   0.82    1400    2.1
1024   3   0.83    1700    2.0
1024   5   0.85    2600    3.9"""),
                    clue='Compare each p95 with 1500. Anything over it is out.',
                    why='1700 and 2600 are both over 1500 ms, so both 1024 rows are out, however good their quality.',
                    wrong=['1024, 3 takes 1700 ms. Is that within 1500?', None, 'Two rows go over 1500 ms.']),
                ask('Of the configs left, which do you ship?', ['512, 3', '512, 5'], answer=1,
                    evidence=evidence('code', title='Fast enough for the budget', text="""chunk  k  quality  p95 ms  cost
 512   3   0.78    1200    1.4
 512   5   0.82    1400    2.1"""),
                    clue='Both fit the budget. Which one gives better answers?',
                    why='Quality 0.82 beats 0.78, and 1400 ms is inside the budget. Fast enough is all the budget asks for; after that, quality decides.',
                    wrong=['It is faster, but both are fast enough. Which has better answers?', None]),
                ask('Both are fast enough and have the same quality. Which do you pick?', ['256, 5', '512, 3', 'Run both in production'], answer=1,
                    evidence=evidence('code', title='Another experiment', text="""budget: p95 under 1000 ms

chunk  k  quality  p95 ms  cost
 256   5   0.80     800    1.5
 512   3   0.80     700    1.1"""),
                    clue='When quality ties, look at the last column.',
                    why='Same quality, both inside the budget, so the cheaper one wins: 1.1 is less than 1.5.',
                    wrong=['Its quality is the same. What else differs?', None, 'A config is one combination of settings: you ship one.']),
                ask('A teammate changed chunk size, k and the embedding model in one run, and quality dropped. What do you tell them?', ['The embedding model: a new model changes every vector', 'No way to tell: three settings changed at once', 'k: ten chunks crowd the prompt with noise'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"I tried 1024 chunks, k of 10 and a new embedding model together. Quality went from 0.82 to 0.74. Which one broke it?"'),
                    clue='Count how many settings changed between the two runs.',
                    why='With three changes in one run, nobody can say which one did it. Hold the eval set, the judge and the answering model fixed, vary one or two settings, and try every combination of them.',
                    wrong=['That is a guess, not evidence. How many things changed?', None, 'Maybe, but k was only one of three changes.']),
            ],
        ),
        starter="""def pick_config(results, max_ms):
    # your code here
    pass
""",
        solution="""def pick_config(results, max_ms):
    best = None
    for row in results:
        if row["p95_ms"] > max_ms:
            continue
        if best is None:
            best = row
        elif row["quality"] > best["quality"]:
            best = row
        elif row["quality"] == best["quality"] and row["cost"] < best["cost"]:
            best = row
    if best is None:
        return None
    return [best["chunk_size"], best["k"]]
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

    best = None   # the best row so far
    for row in results:
        # Step 1: too slow? Skip this row.
        if ___:
            continue
        # First fast-enough row? It is the best so far.
        if best is None:
            best = row
        # Higher quality than best? It becomes the best.
        elif row["quality"] > best["quality"]:
            best = row
        # Step 2: same quality as best, but cheaper? It wins.
        elif row["quality"] == best["quality"] and ___:
            best = row

    if best is None:
        return None
    # Step 3: the two settings from the best row.
    return ___
""",
        fills=[
            'row["p95_ms"] > max_ms',
            'row["cost"] < best["cost"]',
            '[best["chunk_size"], best["k"]]',
        ],
        concepts=[
            [
                'None as "nothing yet"',
                'Start with None and replace it with the first thing you find. `x is None` checks whether you found anything.',
                """best = None
if best is None:
    print('nothing yet')""",
            ],
            [
                'continue',
                'Skips the rest of this turn of the loop and moves on to the next item.',
                """for n in [1, -2, 3]:
    if n < 0:
        continue   # skips -2, goes on to 3""",
            ],
            [
                'if, elif',
                'Python tries each test in order and runs only the first one that is true.',
                """n = 7
if n > 10: print('big')
elif n > 5: print('medium')   # this one runs""",
            ],
            [
                '== and the word and',
                '`a == b` asks whether two values are equal. One = stores a value; two == compare. `x and y` is True only when both are True.',
                """n = 5
n > 1 and n == 5   # True""",
            ],
        ],
        byhand='The budget is 1500 ms. Row 1 (256, 3) takes 900 ms: fast enough. It is the first, so it is the best so far, with quality 0.71. Row 2 (512, 5) takes 1400 ms: fast enough, and its quality 0.82 is higher, so it becomes the best. Row 3 (1024, 10) takes 2600 ms: too slow, skip it. Return [512, 5].',
        why='One walk through the results.',
        gotchas=[
            [
                'Change only what you are testing',
                "If quality drops after changing chunk size, k and the embedding model in one go, you won't know which one did it. When you vary two settings, run every combination of them, so each one's effect shows.",
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
        'Keyword search is great at exact terms like error codes and product names; vector search (matching by embeddings) is great at meaning. **Hybrid search** runs both.',
        "Their scores aren't comparable, so merge by **rank** (place in each list) instead. **Reciprocal rank fusion** gives each document points from every list, more for a higher place, and adds them up, so documents that do well in both lists rise to the top, and a document found by only one search still gets some points.",
    ],
    example=example('Fusing two rankings', """keyword: d3, d1, d7
vector:  d1, d9, d3
fused:   d1, d3, d9, d7"""),
    check=question(
        'Users search for error code "E-4021" and vector search misses it. What helps?',
        ['A bigger embedding model for the same index', 'Hybrid search: add keyword matching', 'Returning more results from vector search'],
        answer=1,
        why='Exact codes are what keyword search is for.',
    ),
    angle=angle(
        pattern='Add up points by place, then sort',
        text="The big idea: keyword and vector scores can't be compared, so hybrid search merges results by their place in each list instead. Your code goes through every list and gives each document points for its place in each list, more for a higher place, with a fixed number added to every place so first does not count far more than second. It adds those points into a dict, a lookup table from each document id to its running total. A document found by both searches collects points twice and rises. Then it sorts the totals from highest to lowest, and ties fall into alphabetical order.",
        say='"Keyword and vector scores can\'t be compared, so I merge the results by [[rank|score|length::Where a document sits in each list.]] instead. A document gets points from [[every list|the first list|the best score::Both searches count.]], so ones found by both rise to the top."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: hybrid query', """results = index.similarity_search(
    query_text="error E-4021 on checkout",
    columns=["chunk_id", "text"],
    query_type="hybrid",
    num_results=10,
)"""),
    exercise=exercise(
        title='Combine Rankings',
        topic='rag',
        difficulty='medium',
        fn='rrf',
        prompt="""Your function gets two things:

- `rankings`: a list of ranked lists, any number of them (even none). Each holds document ids, best first, like `[["d3", "d1"], ["d1", "d9"]]`.
- `smoothing`: a fixed number added to every rank, usually `60`. It stops 1st place from counting far more than 2nd.

In each list, a document gets `1 / (smoothing + rank)` points, where rank is its place in that list, counting from 1. Add up each document's points from all the lists. This is called **reciprocal rank fusion**.

Return every document id, highest total first. If two totals are equal, put those ids in alphabetical order.""",
        pattern='Score by position, add across lists, sort by score with a tie-break.',
        target='one step per ranked item, then a sort',
        realworld='Keyword search finds exact terms (error codes, product names); vector search finds meaning. Fusing them by rank avoids comparing scores on different scales. Databricks Vector Search does hybrid search with `query_type="hybrid"`.',
        starter="""def rrf(rankings, smoothing):
    # your code here
    pass
""",
        solution="""def rrf(rankings, smoothing):
    score = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0) + 1 / (smoothing + rank)
    pairs = []
    for doc in score:
        pairs.append((-score[doc], doc))
    pairs.sort()
    return [pair[1] for pair in pairs]
""",
        cases=[
            case([['d3', 'd1', 'd7'], ['d1', 'd9', 'd3']], 60, expected=['d1', 'd3', 'd9', 'd7'], sample=True),
            case([], 60, expected=[]),
            case([['a', 'b']], 1, expected=['a', 'b']),
            case([['a', 'b'], ['b', 'a']], 60, expected=['a', 'b']),
            case([['b'], ['a']], 60, expected=['a', 'b']),
        ],
        guided="""def rrf(rankings, smoothing):
    # Replace every ___ with real code, then run the tests.

    score = {}   # total points for each document id
    for ranking in rankings:
        # enumerate(..., start=1) gives ranks 1, 2, 3...
        for rank, doc in enumerate(ranking, start=1):
            # Step 1: add this list's points for doc.
            score[doc] = score.get(doc, 0) + ___

    # Step 2: pair each doc as (-score[doc], doc). The
    # minus sign puts the highest first, ties A to Z.
    pairs = []
    for doc in score:
        pairs.append(___)
    pairs.sort()
    return [pair[1] for pair in pairs]
""",
        fills=['1 / (smoothing + rank)', '(-score[doc], doc)'],
        concepts=[
            [
                'enumerate with start',
                '`enumerate(items, start=1)` gives each item together with its place number, counting from 1.',
                """for place, name in enumerate(['ana', 'bo'], start=1):
    print(place, name)   # 1 ana, then 2 bo""",
            ],
            [
                'get with a default',
                '`d.get(key, 0)` gives the value for key, or 0 if the key is not there yet. Handy for running totals.',
                """totals = {}
totals['a'] = totals.get('a', 0) + 5   # {'a': 5}""",
            ],
            [
                'Looping over a dict',
                '`for key in d:` visits each key of the dict.',
                """for name in {'ana': 3, 'bo': 1}:
    print(name)   # ana, then bo""",
            ],
            [
                'append',
                '`items.append(x)` adds x to the end of a list. x can be a pair in round brackets.',
                """pairs = []
pairs.append((5, 'ana'))   # [(5, 'ana')]""",
            ],
            [
                'Sorting pairs',
                'Python sorts pairs by the first item, then by the second. A minus sign on the score puts the biggest score first, and equal scores go in alphabetical order. `pairs.sort()` sorts the list itself.',
                """pairs = [(-1, 'b'), (-2, 'c'), (-1, 'a')]
pairs.sort()
# [(-2, 'c'), (-1, 'a'), (-1, 'b')]""",
            ],
            [
                'List comprehension',
                'Builds a new list from another one in a single line. Item 1 of a pair is its second item, because counting starts at 0.',
                """[p[1] for p in [(5, 'a'), (7, 'b')]]   # ['a', 'b']""",
            ],
        ],
        byhand='smoothing is 60. d1 is 2nd in list 1, so it gets `1 / (60 + 2)`, which is `1 / 62`. It is 1st in list 2, so it also gets `1 / 61`. Its total is about 0.0325. d3 is 1st in list 1 and 3rd in list 2: `1 / 61 + 1 / 63`, about 0.0323. d9 is only in list 2, 2nd: `1 / 62`, about 0.0161. d7 is only in list 1, 3rd: `1 / 63`, about 0.0159. Highest first, return ["d1", "d3", "d9", "d7"].',
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

lesson(MODULE, 'vector_index_setup',
    title='Databricks Vector Search: endpoints, indexes and sync',
    checked='2026-10-15',
    sources=[source('Create AI Search endpoints and indexes', 'https://docs.databricks.com/aws/en/ai-search/create-ai-search'), source('Databricks AI Search cost guide', 'https://docs.databricks.com/aws/en/ai-search/cost-management')],
    learn=[
        'Databricks Vector Search (now called Databricks AI Search) has two parts. An **endpoint** is the serving compute: machines kept running to answer searches. An **index** is the searchable copy of your chunks. It lives in Unity Catalog, Databricks\' catalog of data and who may use it, under a three-part name like `main.support.docs_index`, and it sits on an endpoint. The Python library (the package you install) is now `databricks-ai-search`, used as `from databricks.ai_search.client import AISearchClient`. The older `databricks-vectorsearch` library and its `VectorSearchClient`, which the code on this page still uses, keep working but are deprecated: kept only so old code does not break.',
        'There are two endpoint types. **Standard** answers in tens of milliseconds (thousandths of a second). **Storage-optimized** takes a few hundred milliseconds but costs much less per vector when you have a lot of them. It is a good fit from around 10 million vectors.',
        'There are two index types. A **Delta Sync** index follows a Delta table (a Databricks table) and keeps itself up to date. On a Standard endpoint the table must have **Change Data Feed** turned on: a setting that keeps a log of which rows changed, so the index only updates those. Tables with **row tracking** (a stable id for every row) already have it. Storage-optimized endpoints work differently: every sync rebuilds part of the index, and the docs list no Change Data Feed requirement for them. Databricks can make the embeddings (the lists of numbers that capture meaning) for you, called **managed embeddings**: you name an embedding model endpoint such as `databricks-gte-large-en`. Or you bring a column of your own, called **self-managed embeddings**. A **Direct Vector Access** index has no source table: you write the vectors yourself through the SDK (the Python library) or the API.',
        'A Delta Sync index has a **sync mode**. **Triggered** updates only when you call sync, so it is the cheapest. **Continuous** updates within moments, but costs more because a streaming job runs all the time. Storage-optimized endpoints only do Triggered.',
        'Access has two locks. In Unity Catalog you need USE CATALOG, USE SCHEMA and SELECT on the index. On the endpoint you need its own permission, CAN_USE or CAN_MANAGE, and admins can limit who may create endpoints at all. An endpoint bills for every hour it is up, even with no searches, so delete ones you no longer use. Queries can also filter on columns and run hybrid search (keywords plus meaning) with `query_type="hybrid"`, as in "Hybrid search and rank fusion".',
    ],
    example=example('Turn on Change Data Feed first', """-- On a Standard endpoint, a Delta Sync index needs this
ALTER TABLE main.support.doc_chunks
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- 200,000 chunks, no embeddings yet, an hour old is fine:
-- delta sync, managed embeddings, standard endpoint, triggered"""),
    check=question(
        'You try to create a Delta Sync index on a Standard endpoint and it fails straight away. What is the most likely cause?',
        [
            'Change Data Feed is not turned on for the source table',
            'The table has no embeddings column yet',
            'The table has too few rows to index',
        ],
        answer=0,
        why='On a Standard endpoint a Delta Sync index reads the table\'s change log to know what to update. No Change Data Feed, no change log, so creation fails. A table with no embeddings column is fine (managed embeddings make them), and so is a small one.',
    ),
    angle=angle(
        pattern='Rules checked in a fixed order',
        text='The big idea: setting up Databricks Vector Search is four choices, and each one follows from a plain fact about your data. Your code asks the questions in order. Is the source a Delta table? Then Delta Sync, otherwise Direct Vector Access. Do you already have embeddings? Then self-managed, otherwise managed (and Direct Vector Access is always self-managed). Ten million vectors or more? Then storage-optimized. Last comes sync: none for Direct Vector Access, triggered on storage-optimized, and continuous only when the data must be fresh within 5 minutes. The order matters, because an earlier answer can rule out a later option.',
        say='"I pick the index type from where the data lives, the endpoint type from [[how many vectors|how many users|how long the text::Storage-optimized pays off around ten million of them.]] there are, and the sync mode from how fresh answers must be. [[Continuous|Triggered|Manual::The mode that runs all the time.]] sync only when minutes matter, because it [[costs more|is slower|loses data::A streaming job never stops.]]."',
        classic=None,
    ),
    stack=stack('Databricks Vector Search: endpoint, index, sync', """from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
vsc.create_endpoint(name="vs-endpoint", endpoint_type="STANDARD")

index = vsc.create_delta_sync_index(
    endpoint_name="vs-endpoint",
    index_name="main.support.docs_index",
    source_table_name="main.support.doc_chunks",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_source_column="text",
    embedding_model_endpoint_name="databricks-gte-large-en",
)
index.sync()   # Triggered: pull in the latest table changes now"""),
    exercise=exercise(
        title='Plan a Vector Index',
        topic='rag',
        difficulty='easy',
        fn='vector_index_setup',
        prompt="""Your function gets one thing:

- `needs`: a dict (a lookup table of names and values) describing your data, like `{"source_is_delta": True, "vectors": 200000, "has_embeddings": False, "fresh_within_minutes": 60}`.

Return a list of four choices, in this order:

1. **Index type**: `"delta sync"` if `source_is_delta` is true, otherwise `"direct access"`.
2. **Embeddings**: `"self-managed"` if `has_embeddings` is true, otherwise `"managed"`. For direct access it is always `"self-managed"`, because you write the vectors yourself.
3. **Endpoint type**: `"storage-optimized"` if `vectors` is 10000000 (ten million) or more, otherwise `"standard"`.
4. **Sync**: `"none"` for direct access. `"triggered"` on a storage-optimized endpoint. Otherwise `"continuous"` if `fresh_within_minutes` is 5 or less, else `"triggered"`.""",
        pattern='A few if / else checks in a fixed order, where an earlier answer can decide a later one.',
        target='a few checks, the same however big the data is',
        realworld='The four choices you make before creating a Databricks Vector Search index. Getting sync wrong is the usual cost surprise: Continuous runs a streaming job all day.',
        practice=practice(
            intro='Plan a Databricks Vector Search index the way a reviewer does: read the facts about the data, then make the four choices in order.',
            explain='Setting up Databricks Vector Search is four choices, and each one followed from a plain fact about the data: a Delta table means Delta Sync, no embeddings yet means managed, ten million vectors or more means storage-optimized. You chose sync last, because an earlier answer can rule an option out: storage-optimized only does Triggered, and Continuous is only worth its cost when minutes matter.',
            asks=[
                ask('The chunks sit in a Delta table. Which index type?', ['Delta Sync', 'Direct Vector Access'], answer=0,
                    evidence=evidence('code', title='main.support.doc_chunks', text="""needs = {
  "source_is_delta": True,
  "vectors": 200000,
  "has_embeddings": False,
  "fresh_within_minutes": 60,
}"""),
                    clue='One type follows a table and keeps itself up to date from its change log.',
                    why='The source is a Delta table, so the index can follow it and update itself (with Change Data Feed turned on). Direct Vector Access is for when there is no table and you write the vectors yourself.',
                    wrong=[None, 'That one has no source table: you would write every vector yourself through the SDK.']),
                ask('The table has text but no embeddings yet. Who makes them?', ['Databricks: managed embeddings, from a model endpoint', 'You: self-managed embeddings, in a column you add first'], answer=0,
                    evidence=evidence('code', title='main.support.doc_chunks', text="""needs = {
  "source_is_delta": True,
  "vectors": 200000,
  "has_embeddings": False,
  "fresh_within_minutes": 60,
}"""),
                    clue='Look at `has_embeddings`. If there is nothing to bring, who can do the work?',
                    why='With no embeddings to bring, name an embedding model endpoint such as `databricks-gte-large-en` and Databricks makes them for you. Self-managed is for when you already have a column of your own.',
                    wrong=[None, 'You could, but you would be building something Databricks does for you. Self-managed fits when you already have them.']),
                ask('200,000 vectors fit a Standard endpoint, and answers an hour old are fine. Which sync mode?', ['Continuous: always up to date', 'Triggered: sync on a schedule'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"Let\'s use Continuous sync so the index is always up to date."'),
                    clue='An hour of slack is a lot. Think about what Continuous keeps running all day.',
                    why='Continuous keeps a streaming job running all day. With 60 minutes of slack, Triggered sync on a schedule is enough and much cheaper.',
                    wrong=['Fresher sounds better, but a streaming job runs all day. Do answers need to be fresh within minutes?', None]),
                ask('A year later the docs have grown to 25 million chunks. Which endpoint type?', ['Standard: tens of milliseconds', 'Storage-optimized: a few hundred ms'], answer=1,
                    evidence=evidence('code', title='main.support.doc_chunks, next year', text="""needs = {
  "source_is_delta": True,
  "vectors": 25000000,
  "has_embeddings": False,
  "fresh_within_minutes": 1,
}"""),
                    clue='Around ten million vectors, the cost of each vector matters more than speed.',
                    why='At ten million vectors or more, storage-optimized pays off: a search takes a few hundred milliseconds instead of tens, but each vector costs much less.',
                    wrong=['Standard is faster, but at this size it costs much more per vector.', None]),
                ask('On that endpoint, the product owner wants answers fresh within 1 minute. Which sync mode?', ['Continuous: fresh within moments', 'Triggered: sync on a schedule', 'None: no sync needed'], answer=1,
                    clue='Check which sync modes the endpoint you just picked offers.',
                    why='Storage-optimized endpoints only do Triggered, so the earlier choice rules out Continuous. Run sync often, and tell the product owner what is possible.',
                    wrong=['Continuous isn\'t offered on storage-optimized endpoints, however fresh the answers need to be.', None, 'None is only for Direct Vector Access, where there is no table to sync from.']),
            ],
        ),
        starter="""def vector_index_setup(needs):
    # your code here
    pass
""",
        solution="""def vector_index_setup(needs):
    if needs["source_is_delta"]:
        index_type = "delta sync"
        if needs["has_embeddings"]:
            embeddings = "self-managed"
        else:
            embeddings = "managed"
    else:
        index_type = "direct access"
        embeddings = "self-managed"
    if needs["vectors"] >= 10000000:
        endpoint_type = "storage-optimized"
    else:
        endpoint_type = "standard"
    if index_type == "direct access":
        sync = "none"
    elif endpoint_type == "storage-optimized":
        sync = "triggered"
    elif needs["fresh_within_minutes"] <= 5:
        sync = "continuous"
    else:
        sync = "triggered"
    return [index_type, embeddings, endpoint_type, sync]
""",
        cases=[
            case({'source_is_delta': True, 'vectors': 200000, 'has_embeddings': False, 'fresh_within_minutes': 60},
                 expected=['delta sync', 'managed', 'standard', 'triggered'], sample=True),
            case({'source_is_delta': True, 'vectors': 50000, 'has_embeddings': True, 'fresh_within_minutes': 5},
                 expected=['delta sync', 'self-managed', 'standard', 'continuous']),
            case({'source_is_delta': True, 'vectors': 25000000, 'has_embeddings': False, 'fresh_within_minutes': 1},
                 expected=['delta sync', 'managed', 'storage-optimized', 'triggered']),
            case({'source_is_delta': False, 'vectors': 300000, 'has_embeddings': False, 'fresh_within_minutes': 1},
                 expected=['direct access', 'self-managed', 'standard', 'none']),
            case({'source_is_delta': True, 'vectors': 10000000, 'has_embeddings': True, 'fresh_within_minutes': 30},
                 expected=['delta sync', 'self-managed', 'storage-optimized', 'triggered']),
        ],
        guided="""def vector_index_setup(needs):
    # Replace every ___ with real code, then run the tests.

    # Step 1: index type, and who makes the embeddings.
    if needs["source_is_delta"]:
        index_type = "delta sync"
        if ___:
            embeddings = "self-managed"
        else:
            embeddings = "managed"
    else:
        index_type = "direct access"
        embeddings = "self-managed"   # you write vectors yourself

    # Step 2: ten million vectors or more -> storage-optimized.
    if ___:
        endpoint_type = "storage-optimized"
    else:
        endpoint_type = "standard"

    # Step 3: sync mode. Check these rules in this order.
    if index_type == "direct access":
        sync = "none"
    elif endpoint_type == "storage-optimized":
        sync = "triggered"
    elif ___:
        sync = "continuous"
    else:
        sync = "triggered"

    return [index_type, embeddings, endpoint_type, sync]
""",
        fills=['needs["has_embeddings"]', 'needs["vectors"] >= 10000000', 'needs["fresh_within_minutes"] <= 5'],
        concepts=[
            [
                'Reading from a dict',
                '`d["name"]` gives the value stored under that name.',
                """needs = {'vectors': 500}
needs['vectors']   # 500""",
            ],
            [
                'if / elif / else',
                'Python checks each condition from the top and runs the first one that is true. `elif` means "else if". The rest are skipped.',
                """if size > 100:
    label = 'big'
elif size > 10:
    label = 'medium'
else:
    label = 'small'""",
            ],
            [
                'Comparing numbers',
                '`>=` means "at least" and `<=` means "at most". Both include the number itself.',
                """10 >= 10   # True
5 <= 4     # False""",
            ],
            [
                'Returning a list',
                'Square brackets make a list. Here it holds the four answers in a fixed order.',
                """return ['a', 'b', 'c', 'd']""",
            ],
        ],
        byhand='The sample needs are: source is Delta, 200,000 vectors, no embeddings yet, an hour old is fine. Source is Delta, so the index type is "delta sync". No embeddings yet, so Databricks makes them: "managed". 200,000 is less than ten million, so "standard". Not direct access and not storage-optimized, so look at freshness: 60 minutes is more than 5, so "triggered". Return ["delta sync", "managed", "standard", "triggered"].',
        why='A few checks, each done once, however big the index is.',
        gotchas=[
            [
                'Idle endpoints still cost money',
                'An endpoint bills while it is up, even with no searches. Delete endpoints for finished experiments.',
            ],
            [
                'Two locks, two keys',
                'A user needs Unity Catalog grants (USE CATALOG, USE SCHEMA, SELECT on the index) and CAN_USE on the endpoint. Missing either one gives a permission error.',
            ],
            [
                'Continuous is not free',
                'Continuous sync keeps a streaming job running all the time. Pick it only when answers must reflect changes within minutes; otherwise run Triggered sync on a schedule.',
            ],
            [
                'Storage-optimized is slower',
                'A few hundred milliseconds per search is fine for most chat apps, but check it against your latency budget (how long a user can wait) before switching.',
            ],
        ],
    ),
)

lesson(MODULE, 'pick_search_service',
    title='Databricks Vector Search or Azure AI Search?',
    checked='2026-10-12',
    sources=[source('Azure AI Search agentic retrieval', 'https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview'), source('Azure AI Search pricing', 'https://azure.microsoft.com/en-us/pricing/details/search/'), source('Create Vector Search endpoints and indexes', 'https://docs.databricks.com/aws/en/vector-search/create-vector-search')],
    learn=[
        'Many companies have both Databricks Vector Search and **Azure AI Search**, Microsoft\'s search service (once called Azure Cognitive Search, and now the engine under Foundry IQ, Microsoft\'s knowledge layer for agents). Both can do vector, keyword and hybrid search. Neither is "the right one". The choice is mostly about **where the data lives and where the app runs**.',
        'Databricks Vector Search fits when the documents are already in Delta tables in Unity Catalog. You get Unity Catalog grants and **lineage** (a record of which table fed which index) on the index, and the index can sync straight from a table. It also fits when the agent runs on Databricks: Agent Bricks, Model Serving, or the ready-made MCP server for it. MCP (Model Context Protocol) is a standard way for an agent to call tools.',
        'Azure AI Search fits when the content sits in Azure Blob Storage, SharePoint or other Azure sources. Its **indexers** pull the files in on a schedule, cut them into chunks and make the embeddings for you (Microsoft calls this integrated vectorization). It also fits when the app runs outside Databricks, such as an Azure AI Foundry or Azure OpenAI app or a Copilot-style app, or when access must go through Microsoft Entra ID (Microsoft\'s sign-in service) and its role-based access control (RBAC: roles that say who may do what), or through private endpoints (a private network address, so traffic never crosses the public internet).',
        'Azure AI Search adds two extras. The **semantic ranker** is a reranker that re-scores the top results by meaning. **Agentic retrieval** splits a hard question into smaller searches and merges the results, using **knowledge bases**: these are generally available in REST API version 2026-04-01, while query planning is still in preview. Pricing is by tier, paid in **search units** (blocks of capacity), with a newer serverless option in preview. The semantic ranker and agentic retrieval are billed on top.',
        'Running both is common: curated tables in Databricks Vector Search, SharePoint documents in Azure AI Search. Keep **one evaluation set** (see "Measuring retrieval") so you compare them on the same questions.',
    ],
    example=example('Two common setups side by side', """curated tables in Unity Catalog
  -> Databricks Vector Search -> agent on Model Serving

policy documents in SharePoint
  -> Azure AI Search indexer -> app in Azure AI Foundry

same eval questions -> compare recall@k for both"""),
    check=question(
        'The policy documents live in SharePoint and the chat app runs in Azure AI Foundry. Which service fits more naturally?',
        ['Databricks Vector Search', 'Azure AI Search', 'Neither can do this'],
        answer=1,
        why='An Azure AI Search indexer can pull from SharePoint on a schedule, and the app already runs in Azure, so there is no copy into Delta tables to keep in step.',
    ),
    angle=angle(
        pattern='Count the points for each side, then compare',
        text='The big idea: the choice follows where the data lives and where the app runs, not which tool is "better". Your code walks through the facts once. A fact on the Databricks list gives Databricks Vector Search a point, a fact on the Azure list gives Azure AI Search a point, and anything else is ignored. More points wins. A tie is an honest answer too: test both on the same eval set and let the numbers decide.',
        say='"I put the index [[next to the data|in the cheapest place|where the model is::Where do the documents already live?]] and the app. Delta tables and agents on Databricks point to Databricks Vector Search; SharePoint, Blob and apps in Azure point to [[Azure AI Search|Genie|Lakebase::Microsoft\'s search service.]]. If it is close, I test both on [[one eval set|live traffic|a demo::The same questions for both.]]."',
        classic=None,
    ),
    stack=stack('Same question, two services', """# Databricks Vector Search
results = index.similarity_search(
    query_text="how many days of annual leave?",
    columns=["id", "text"],
    query_type="hybrid",
    num_results=5,
)

# Azure AI Search (azure-search-documents)
from azure.search.documents.models import VectorizableTextQuery
results = search_client.search(
    search_text="how many days of annual leave?",
    vector_queries=[VectorizableTextQuery(
        text="how many days of annual leave?",
        k_nearest_neighbors=5, fields="text_vector")],
    query_type="semantic",
    semantic_configuration_name="default",
    top=5,
)"""),
    exercise=exercise(
        title='Pick a Search Service',
        topic='rag',
        difficulty='easy',
        fn='pick_search_service',
        prompt="""Your function gets one thing:

- `facts`: a list of short strings about your project, like `["data in delta", "agent on databricks", "docs in sharepoint"]`.

These facts give Databricks Vector Search a point each: `"data in delta"`, `"need uc grants"`, `"agent on databricks"`, `"sync from table"`.

These facts give Azure AI Search a point each: `"docs in sharepoint"`, `"docs in blob"`, `"app outside databricks"`, `"need semantic ranker"`, `"need entra rbac"`.

Any other string is ignored.

Return a list of three things: `[choice, databricks_points, azure_points]`. The choice is `"databricks vector search"` if Databricks has more points, `"azure ai search"` if Azure has more, and `"either: test both on your eval set"` if they are equal.""",
        pattern='Count matches into two totals in one pass, then compare them.',
        target='one pass over the facts, then one comparison',
        realworld='A quick, honest way to frame the choice in a design review: list the facts, see which side they point to, and treat a tie as a reason to measure.',
        practice=practice(
            intro='Weigh up Databricks Vector Search and Azure AI Search the way a design review does: see which side each fact points to, then decide.',
            explain='The choice followed where the data lives and where the app runs, not which tool is "better". You gave each fact to the side it points to, ignored the ones that point nowhere, and let the bigger side win. A tie, or a single shiny feature, was a reason to test both on one eval set.',
            asks=[
                ask('Which service does "docs in sharepoint" point to?', ['Databricks Vector Search', 'Azure AI Search'], answer=1,
                    evidence=evidence('code', title='The project facts', text="""facts = [
  "data in delta",
  "agent on databricks",
  "docs in sharepoint",
]"""),
                    clue='Which service has indexers that pull files in from Microsoft sources on a schedule?',
                    why='An Azure AI Search indexer can pull SharePoint files in, cut them into chunks and make the embeddings. Databricks Vector Search would need them copied into a Delta table first.',
                    wrong=['It would need the files copied into a Delta table first. Which one reads SharePoint directly?', None]),
                ask('Taking all three facts together, which service do they point to?', ['Databricks Vector Search', 'Azure AI Search', 'Either: test both on one eval set'], answer=0,
                    evidence=evidence('code', title='The project facts', text="""facts = [
  "data in delta",
  "agent on databricks",
  "docs in sharepoint",
]"""),
                    clue='Two facts are about where data and agents already live; one is about SharePoint.',
                    why='Delta tables and an agent on Databricks give Databricks Vector Search two points; SharePoint gives Azure AI Search one. Two beats one.',
                    wrong=['SharePoint is one point for Azure, but the other two facts point the other way.', None, 'It is only a tie when both sides have the same number of points.']),
                ask('A new project has these facts. What is the honest answer?', ['Databricks Vector Search, for the grants', 'Azure AI Search, for Entra ID access', 'Either: test both on one eval set'], answer=2,
                    evidence=evidence('code', title='Another project', text="""facts = [
  "need uc grants",
  "need entra rbac",
  "team likes python",
]"""),
                    clue='"team likes python" is on neither list. Count what is left on each side.',
                    why='Unity Catalog grants is one point for Databricks, Entra ID access is one for Azure, and a liking for a language is neither. A tie means measure: run the same eval questions through both.',
                    wrong=['That is one point each. Does either side win?', 'That is one point each. Does either side win?', None]),
                ask('Back on the first project, what do you say?', ['Agree: the semantic ranker gives better results', 'Keep them in Databricks, where the agent runs too', 'Copy the tables into both services, to be safe'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"Azure AI Search has the semantic ranker, so it\'s the better product. Let\'s move our curated Delta tables into it."'),
                    clue='The choice follows where the data lives and where the app runs, not which tool has the nicest feature.',
                    why='A feature is one point, not the whole answer. Curated tables in Unity Catalog with an agent on Databricks point to Databricks Vector Search; if the ranker might matter, the eval set will show it.',
                    wrong=['One feature is one point. Where do the tables live, and where does the agent run?', None, 'Two copies drift apart. Pick one home per source unless you are deliberately comparing.']),
            ],
        ),
        starter="""def pick_search_service(facts):
    # your code here
    pass
""",
        solution="""def pick_search_service(facts):
    databricks_signs = ["data in delta", "need uc grants", "agent on databricks", "sync from table"]
    azure_signs = ["docs in sharepoint", "docs in blob", "app outside databricks", "need semantic ranker", "need entra rbac"]
    databricks_points = 0
    azure_points = 0
    for fact in facts:
        if fact in databricks_signs:
            databricks_points += 1
        elif fact in azure_signs:
            azure_points += 1
    if databricks_points > azure_points:
        choice = "databricks vector search"
    elif azure_points > databricks_points:
        choice = "azure ai search"
    else:
        choice = "either: test both on your eval set"
    return [choice, databricks_points, azure_points]
""",
        cases=[
            case(['data in delta', 'agent on databricks', 'docs in sharepoint'],
                 expected=['databricks vector search', 2, 1], sample=True),
            case(['docs in blob', 'app outside databricks', 'need semantic ranker'],
                 expected=['azure ai search', 0, 3]),
            case([], expected=['either: test both on your eval set', 0, 0]),
            case(['need uc grants', 'need entra rbac', 'team likes python'],
                 expected=['either: test both on your eval set', 1, 1]),
            case(['sync from table', 'docs in sharepoint', 'need entra rbac', 'budget is tight'],
                 expected=['azure ai search', 1, 2]),
        ],
        guided="""def pick_search_service(facts):
    # Replace every ___ with real code, then run the tests.

    databricks_signs = ["data in delta", "need uc grants", "agent on databricks", "sync from table"]
    azure_signs = ["docs in sharepoint", "docs in blob", "app outside databricks", "need semantic ranker", "need entra rbac"]
    databricks_points = 0
    azure_points = 0

    for fact in facts:
        # Step 1: give a point to the side this fact belongs to.
        if fact in databricks_signs:
            databricks_points += 1
        elif ___:
            azure_points += 1
        # any other fact is ignored

    # Step 2: more points wins; equal points means test both.
    if ___:
        choice = "databricks vector search"
    elif azure_points > databricks_points:
        choice = "azure ai search"
    else:
        choice = ___

    return [choice, databricks_points, azure_points]
""",
        fills=['fact in azure_signs', 'databricks_points > azure_points', '"either: test both on your eval set"'],
        concepts=[
            [
                'in on a list',
                '`x in items` is True if x is one of the items in the list.',
                """'bo' in ['ana', 'bo']    # True
'cy' in ['ana', 'bo']    # False""",
            ],
            [
                'Counting with +=',
                '`n += 1` adds 1 to n. Start the count at 0 before the loop.',
                """count = 0
count += 1   # 1""",
            ],
            [
                'for loop',
                'Visits each item of a list in turn.',
                """for name in ['ana', 'bo']:
    print(name)""",
            ],
            [
                'if / elif / else',
                'Runs the first branch whose condition is true. `else` catches everything left, here the tie.',
                """if a > b:
    winner = 'a'
elif b > a:
    winner = 'b'
else:
    winner = 'tie'""",
            ],
        ],
        byhand='The sample facts are "data in delta", "agent on databricks" and "docs in sharepoint". The first two are on the Databricks list, so Databricks has 2 points. "docs in sharepoint" is on the Azure list, so Azure has 1. 2 is more than 1, so return ["databricks vector search", 2, 1].',
        why='One look at each fact, then one comparison at the end.',
        gotchas=[
            [
                'Say the full name',
                'Always say "Azure AI Search" or "Databricks Vector Search". A bare "AI Search" could mean either company\'s product.',
            ],
            [
                'Check what is in preview',
                'Some features, such as query planning, the serverless tier and some indexers, have been in preview (not yet fully supported). Check the docs before you build on one.',
            ],
            [
                'Copies drift',
                'Copying the same documents into both services means two indexes to keep in step. Pick one home per source unless you are deliberately comparing.',
            ],
            [
                'Points are a starting point',
                'One hard rule, such as "data may not leave Azure", can outweigh several points. Use the count to start the conversation, then check the evaluation numbers.',
            ],
        ],
    ),
)
