# Native optimization and full-repair loop

This is the project's native editing layer. It is deliberately different from a detector word list: it reconstructs the article around supplied facts, a plausible author voice, and useful decisions.

## 1. Build a fact and voice ledger

Before rewriting, extract:

- non-negotiable facts, numbers, dates, names, product capabilities, and sources;
- claims that are unsupported, vague, or stronger than the evidence;
- intended reader, decision, use case, and document type;
- the author's existing preferences: directness, technicality, warmth, sentence length, terminology, and degree of qualification;
- protected regions: quotes, code, tables, front matter, legal text, and attributed third-party material.

If the source contains no author sample, do not invent a personal persona. Use a restrained editorial voice appropriate to the stated audience.

## 2. Rebuild the argument before polishing sentences

For each paragraph, identify its job: context, problem, mechanism, evidence, trade-off, example, decision, or conclusion. Remove paragraphs that only restate the headline. Add a concrete bridge when adjacent paragraphs could be swapped without changing the argument.

Prefer this progression where it fits:

`specific situation → observed problem → mechanism or choice → evidence/qualification → practical implication`

Do not force this structure onto a technical reference, legal text, or a deliberately fragmentary style.

## 3. Replace AI-like abstraction with supplied specificity

Review every broad phrase such as “improves efficiency,” “plays a vital role,” “seamless,” “empowers,” “注入活力,” or “具有重要意义.” Replace it only when the source gives enough information to name:

- who or what changes;
- which step, object, or decision changes;
- how the change happens;
- under what condition it applies;
- what trade-off or limitation remains.

When information is missing, preserve the claim cautiously and insert `[需要补充：机制/数据/来源]` rather than inventing an answer.

## 4. Rebuild rhythm without theatrical randomness

- Mix short, medium, and long sentences according to meaning, not by quota.
- Let an important fact stand alone when it deserves emphasis.
- Combine sentences that repeat one idea; split overloaded sentences at real decision points.
- Vary paragraph openings and transitions. Use “first/second/finally,” “not just…but,” and three-part lists only when the logic genuinely needs them.
- Remove assistant residue, meta-commentary, generic scene-setting, fake enthusiasm, and repetitive conclusions.
- Keep necessary technical repetition, formal caution, and domain terminology.
- Do not add typos, slang, fake personal anecdotes, or awkward fragments just to appear human.

## 5. Preserve truth and voice

- Never create a statistic, customer story, citation, product feature, test result, or personal experience.
- Do not turn a technical or academic document into casual marketing copy.
- Do not delete a limitation merely because it reduces persuasion.
- Keep brand names, API names, units, formulas, and quoted text unchanged unless the user explicitly authorizes a correction.
- In ARMOR work, apply `profiles/armor.yaml` and treat unresolved product claims as review items.

## 6. Post-repair gates

After writing the full revision, check:

1. Every original factual claim is either preserved, weakened safely, sourced, or marked for confirmation.
2. No paragraph is generic enough to be pasted into a different article unchanged.
3. The introduction earns its space and does not restate the title.
4. Each section adds information instead of repeating a conclusion.
5. Evidence strength matches wording strength.
6. Sentence and paragraph rhythm follows meaning rather than a uniform template.
7. Protected content and deliberate style choices were not “corrected” mechanically.
8. A second audit finds fewer high-confidence, high-impact issues—or clearly explains why a remaining issue is intentional.

The target is a more specific, coherent, honest article with a recognizable editorial voice. It is not a promise to bypass Turnitin, ZeroGPT, or any other detector.
