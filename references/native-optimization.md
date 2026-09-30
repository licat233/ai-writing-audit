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

### Choose an opening with a reason to exist

Select the strongest opening supported by the source:

1. a specific observed scene or operational detail;
2. a buyer decision or mistake with a concrete consequence;
3. a tension between the obvious solution and the actual constraint;
4. a verified result, limitation, or product mechanism;
5. a direct statement of the problem when no richer material exists.

Do not open by paraphrasing the title, announcing that the topic is important, or inventing a store visit, customer reaction, trend, or date. A plain truthful opening is better than cinematic fiction.

### Make section depth asymmetric

Allocate space by information value. A difficult mechanism may need several paragraphs; a secondary point may need one sentence. Remove parallel headings that merely divide a list into equal blocks. Keep FAQ only when readers genuinely use the page as a reference or the user explicitly needs an SEO FAQ.

### Expose a real reasoning move

Move between paragraphs through one of these relationships: cause, correction, condition, trade-off, exception, evidence, consequence, or decision. A “common assumption → observed constraint → revised decision” sequence is useful only when the assumption and constraint are grounded in supplied material.

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

### Use perspective without inventing a persona

First person is evidence-bearing language. Use “I” or “we” only when the user supplies the speaker and experience. If the source has operational detail but no first-person authority, write from the situation itself: describe what changes on the shelf, in the workflow, or in the buyer's decision. If neither experience nor detail exists, keep the voice direct and neutral and mark the missing input.

One specific judgment is more credible than scattered conversational fillers. Prefer a defensible stance such as “adding more ceiling light does not solve a shadow under the second shelf” when the mechanism is supported. Avoid generic attitude markers such as “讲真,” “显然,” or “毫无疑问” unless they match a supplied voice sample.

## 5. Preserve truth and voice

- Never create a statistic, customer story, citation, product feature, test result, or personal experience.
- Do not turn a technical or academic document into casual marketing copy.
- Do not delete a limitation merely because it reduces persuasion.
- Keep brand names, API names, units, formulas, and quoted text unchanged unless the user explicitly authorizes a correction.
- In ARMOR work, apply `profiles/armor.yaml` and treat unresolved product claims as review items.

## 6. No-AI-slop editorial gates

Apply these as semantic editorial checks, not blanket regex bans:

- **Portability test:** if a sentence could move unchanged to another company, product, market, or person, remove it or ground it in supplied facts, mechanisms, consequences, or judgment.
- **Minimum effective edit:** do not rewrite a strong sentence merely to make the document more uniform. Preserve useful roughness, cadence, bluntness, humor, uncertainty, and deliberate asymmetry.
- **No performed insight:** remove stock exclusivity setups, interpretive commentary, fake profundity, synonym cycling, and dramatic fragments when they add posture rather than information.
- **Contextual formatting:** emoji, bold, bullets, short headings, and dashes are not inherently wrong. Keep them when the publication surface needs them; remove them when they decorate weak prose or create repetitive AI-like structure.
- **Read-aloud gate:** final prose should sound natural when read to a sharp colleague while preserving the intended professional register.

These gates are adapted from the editorial principles in petergyang/no-ai-slop and intentionally remain agent-reviewed where deterministic detection would create false positives.

## 7. Post-repair gates

After writing the full revision, check:

1. Every original factual claim is either preserved, weakened safely, sourced, or marked for confirmation.
2. No paragraph is generic enough to be pasted into a different article unchanged.
3. The introduction earns its space and does not restate the title.
4. Each section adds information instead of repeating a conclusion.
5. Evidence strength matches wording strength.
6. Sentence and paragraph rhythm follows meaning rather than a uniform template.
7. Protected content and deliberate style choices were not “corrected” mechanically.
8. A second audit finds fewer high-confidence, high-impact issues—or clearly explains why a remaining issue is intentional.
9. The opening is supported by source material and does not merely restate the title.
10. Section lengths and headings are not mechanically symmetrical unless the genre requires a reference layout.
11. Any first-person experience, quotation, dialogue, humor, or field detail is attributable to supplied material.
12. The ending completes a decision, implication, or next action instead of repeating a generic summary or attaching an unnecessary FAQ.
13. The introduction does not lexically repeat the first headed section; open the first section with new information.
14. No sentence asserts generalized buyer/shopper behavior without a traceable source and scope.
15. No roadmap or list-count announcement (for example, “this article covers the four specs”) substitutes for the argument itself.
16. Four or more parallel titled spec sections are folded into the argument or justified as a genuine reference layout, not generated as a spec-tour.

A clean deterministic scan after repair is not sufficient: if any gate above still fails, rewrite again or mark the unresolved item visibly for confirmation.

The target is a more specific, coherent, honest article with a recognizable editorial voice. It is not a promise to bypass Turnitin, ZeroGPT, or any other detector.
