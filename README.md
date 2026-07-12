# The Second Language Brain

Personal IELTS Speaking knowledge tree for building a long-term English expression system.

This repository is not an answer bank. It turns every speaking practice session into connected knowledge nodes:

- high-scoring IELTS expressions
- personal stories
- vocabulary
- grammar mistakes
- pronunciation notes
- topic links
- speaking skill links
- spaced review tasks

## Daily Workflow

1. Finish an IELTS Speaking practice session.
2. Ask ChatGPT to produce a structured session summary.
3. Save the summary in `inbox/`, for example:

   ```text
   inbox/2026-07-12_AI_Game_Ideas.md
   ```

4. Process the session:

   ```powershell
   python scripts/process_session.py inbox/2026-07-12_AI_Game_Ideas.md
   ```

   On Windows, you can also use the helper script. It will use system Python if available, otherwise it will try the bundled Codex Python runtime:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\run_pipeline.ps1 inbox\2026-07-12_AI_Game_Ideas.md
   ```

5. Rebuild indexes and review lists if needed:

   ```powershell
   python scripts/build_indexes.py
python scripts/build_review.py
```

6. Review the generated files under:

   - `Daily_Sessions/`
   - `Skill_Tree/`
   - `Expression_Bank/`
   - `Mistake_Log/`
   - `Review_System/due/`
   - `indexes/`

7. Commit and push the changes to GitHub.

## Content Policy

- English is used for model answers, examples, expressions, and speaking output.
- Chinese is used for grammar explanations, review notes, and maintenance rules.
- Scripts organize and link your material. They do not rewrite your ideas.

## Knowledge Node Metadata

Every generated knowledge node uses YAML-like front matter:

```yaml
---
id: vocab_spawn_20260712
type: vocabulary
title: spawn
created: 2026-07-12
source_session: session_20260712_ai_game_ideas
topics: [Technology, Games, Environment]
skills: [Explain Reasons, Describe Systems]
related: [ecosystem, adapt, thrive]
review:
  status: new
  next_due: 2026-07-13
  interval_days: 1
---
```

The metadata lets the repository behave like a knowledge graph, not just a folder of notes.

## Review System

The first version uses fixed spaced review intervals:

```text
1 day -> 3 days -> 7 days -> 14 days -> 30 days
```

Generated review files appear in `Review_System/due/`.
