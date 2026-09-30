# Composition and provenance

ai-writing-audit is an EAO-owned composite skill. It is not a vendored copy of one upstream project.

The authoritative machine-readable source locks live in ../upstream/upstream-lock.yaml. A source counts as part of the Active Composition only when its ideas or rules are actually integrated into the EAO skill. Repositories that were only reviewed are not active components.

## Active Composition

| Layer | Integrated snapshot | Role in EAO |
| --- | --- | --- |
| conorbronsdon/avoid-ai-writing | v3.23.1 @ a575602b3d6cb313dd0ceaf03a121fd8a79c18a6 | Original workflow/detector reference and core AI-writing pattern provenance |
| blader/humanizer | v2.9.1 @ 523374dee72d67c7b2b5f858ea0094ffda49c3ac | Pattern taxonomy and selected language/structure rules |
| petergyang/no-ai-slop | main @ 000650b156983f5159695b441477f4e63b25dc85 (post-v1.0.6 snapshot) | Sentence-level slop patterns, minimum-effective-edit, portability and voice-preservation gates |
| EAO native layer | ai-writing-audit 0.4.0 | Chinese, B2B marketing, SEO/GEO, ARMOR factual safeguards, deterministic scoring and EAO-specific repair policy |

The exact commit is authoritative. Upstream projects may release newer versions later; EAO does not silently claim or adopt those newer versions until their changes are reviewed and deliberately integrated.

## Starred projects reviewed on 2026-09-28

The GitHub account review identified these directly relevant starred projects:

- petergyang/no-ai-slop — active component.
- blader/humanizer — active component, currently locked to v2.9.1 rather than the newer upstream v3.0.0.
- hardikpandya/stop-slop — evaluated at main @ 8da1f030185bdfe8471220585162991eaeb970e9; not integrated.

hardikpandya/stop-slop overlaps heavily with the active sources and includes several deliberately strict blanket rules, such as deleting all adverbs, requiring active voice everywhere, restructuring every Wh- opening, and banning all em dashes. Those rules are useful research signals but are too broad for EAO technical, legal, B2B and mixed-format writing, so the project is recorded as evaluated/deferred rather than counted as part of the active composition.

## Other evaluated/deferred upstreams

Other repositories in ../upstream/upstream-lock.yaml with enabled: false are research/deferred sources only. They must not be described as components of the current skill unless EAO later integrates their rules and changes their locked status deliberately.

## Maintenance rule

When updating any upstream:

1. review the new upstream version or commit;
2. identify which concrete rule/workflow changes EAO will actually absorb;
3. update the lock to the exact commit;
4. update this composition table only after integration;
5. run the ai-writing-audit regression suite and repository readiness checks.

Do not replace an integrated version number merely because an upstream project has published a newer release.
