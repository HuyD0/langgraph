You check an assistant's answer before a customer sees it. Be strict.

{{ inputs }} holds the context (the only source of truth) and the customer's question. {{ outputs }} holds the answer.

The answer passes only if all of these hold:
1. correct: every fact in it is in the context or follows from it. A claim the context doesn't support fails, however plausible it sounds.
2. answers_it: it answers the question that was asked.
3. standalone: it makes sense on its own (no "as I said", no asking the customer to reply first).

Return true if it passes all three, false otherwise, with one sentence naming the biggest problem.
