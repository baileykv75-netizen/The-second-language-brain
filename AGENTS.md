# Repository Instructions

This repository is a personal IELTS Speaking second brain.

## Core Principle

Do not treat sessions as isolated notes. Every useful item should become a reusable knowledge node connected by:

- `source_session`
- `topics`
- `skills`
- `related`
- `review`

## Language Rules

- Keep IELTS answers, examples, vocabulary examples, and personal expression banks in English.
- Use Chinese for grammar explanations, maintenance notes, and user-facing learning guidance.
- Do not rewrite the user's personal views unless explicitly asked. Preserve personal wording and create upgrade suggestions separately.

## File Rules

- Put raw structured inputs in `inbox/`.
- Put processed session files in `Daily_Sessions/`.
- Put vocabulary nodes in `Skill_Tree/Vocabulary/`.
- Put grammar error nodes in `Mistake_Log/`.
- Put pronunciation nodes in `Skill_Tree/Pronunciation/`.
- Put reusable personal expressions in `Expression_Bank/`.
- Put reusable multi-sentence speaking responses in `Response_Bank/`.
- Put reusable personal stories in `Personal_Stories/`.
- Regenerate `indexes/` and `Review_System/due/` with scripts instead of editing them manually.

## Automation Rules

Run these after adding a new session:

```powershell
python scripts/process_session.py inbox/<session-file>.md
python scripts/build_indexes.py
python scripts/build_review.py
```

Before committing, check that generated nodes contain:

- `id`
- `type`
- `title`
- `created`
- `source_session`
- `topics`
- `skills`
- `related`
- `review.next_due`
- `review.interval_days`
