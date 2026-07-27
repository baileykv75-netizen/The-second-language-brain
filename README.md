# The Second Language Brain

A speaking-first IELTS knowledge system. Start with a Speaking Case, form a defensible view, speak before reading notes, then use the linked language nodes as support.

## Start Here

- Mobile app view: [GitHub Pages](https://baileykv75-netizen.github.io/The-second-language-brain/)
- Project plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)
- Today's review: [2026-07-27](Review_System/due/2026-07-27.md)
- Add a new structured session: [inbox/](inbox/)
- Session template: [templates/session_template.md](templates/session_template.md)
- ChatGPT Project instructions: [prompts/chatgpt_project_instructions.md](prompts/chatgpt_project_instructions.md)
- Full session history: [indexes/sessions.md](indexes/sessions.md)

## Quick Stats

- Sessions: 3
- Speaking cases: 3
- Vocabulary nodes: 12
- Grammar mistakes: 9
- Expressions: 14
- Mini responses: 7
- Personal stories: 2

## Main Entrances

| Area | Open |
| --- | --- |
| Review | [Due list](Review_System/due/2026-07-27.md) |
| Speak | [Speaking cases](indexes/speaking_cases.md) |
| Topics | [Topic tree](IELTS_Topics/) |
| Skills | [Skill tree](Skill_Tree/) |
| Vocabulary | [Vocabulary index](indexes/vocabulary.md) |
| Grammar mistakes | [Mistake log](indexes/mistakes.md) |
| Expressions | [Expression bank](indexes/expressions.md) |
| Mini responses | [Response bank](indexes/responses.md) |
| Personal stories | [Story bank](indexes/personal_stories.md) |

## Latest Sessions

- [Herbicide-Free Campus Article Practice](Daily_Sessions/2026-07-16_herbicide_free_campus_article_practice.md)
- [AI Consciousness and Evolution](Daily_Sessions/2026-07-12_ai_consciousness_and_evolution.md)
- [AI Game Ideas](Daily_Sessions/2026-07-12_ai_game_ideas.md)

## Speaking Cases

- [Herbicide-Free Campus Article Practice](Speaking_Cases/2026-07-16_herbicide_free_campus_article_practice.md)
- [AI Consciousness and Evolution](Speaking_Cases/2026-07-12_ai_consciousness_and_evolution.md)
- [AI Game Ideas](Speaking_Cases/2026-07-12_ai_game_ideas.md)

## Topic Tree

- [Agriculture](indexes/topic_agriculture.md)
- [Artificial Intelligence](indexes/topic_artificial_intelligence.md)
- [Campus Life](indexes/topic_campus_life.md)
- [Career](indexes/topic_career.md)
- [Climate Change](indexes/topic_climate_change.md)
- [Creative Projects](indexes/topic_creative_projects.md)
- [Culture](indexes/topic_culture.md)
- [Economy](indexes/topic_economy.md)
- [Education](indexes/topic_education.md)
- [Entrepreneurship](indexes/topic_entrepreneurship.md)
- [Environment](indexes/topic_environment.md)
- [Ethics](indexes/topic_ethics.md)

## Speaking Skill Tree

- [Describe Systems](indexes/skill_describe_systems.md)
- [Explain Reasons](indexes/skill_explain_reasons.md)
- [Express Personal Opinions](indexes/skill_express_personal_opinions.md)
- [Use Collocations](indexes/skill_use_collocations.md)

## Recent Vocabulary

- [Technical vs Technological](Skill_Tree/Vocabulary/2026-07-16_herbicide_free_campus_article_practice_technical_vs_technological.md)
- [Coexist peacefully](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_coexist_peacefully.md)
- [Consciousness](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_consciousness.md)
- [Harsh environment](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_harsh_environment.md)
- [Intrinsic value](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_intrinsic_value.md)
- [Parameters](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_parameters.md)
- [Plausible](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_plausible.md)
- [Sandbox evolution](Skill_Tree/Vocabulary/2026-07-12_ai_consciousness_and_evolution_sandbox_evolution.md)

## Recent Grammar Mistakes

- [It depends if this kind of material is safe.](Mistake_Log/2026-07-16_herbicide_free_campus_article_practice_grammar_1.md)
- [They need to find a outlet.](Mistake_Log/2026-07-16_herbicide_free_campus_article_practice_grammar_2.md)
- [If it is harmful for all human beings, we should stop it.](Mistake_Log/2026-07-16_herbicide_free_campus_article_practice_grammar_3.md)
- [I will stop them doing these kinds of things.](Mistake_Log/2026-07-16_herbicide_free_campus_article_practice_grammar_4.md)
- [AI was just a tool.](Mistake_Log/2026-07-12_ai_consciousness_and_evolution_grammar_1.md)

## Expression Bank

- [Be in the present moment](Expression_Bank/2026-07-16_herbicide_free_campus_article_practice_be_in_the_present_moment.md)
- [Come at a cost](Expression_Bank/2026-07-16_herbicide_free_campus_article_practice_come_at_a_cost.md)
- [Contaminate waterways](Expression_Bank/2026-07-16_herbicide_free_campus_article_practice_contaminate_waterways.md)
- [Contribute to](Expression_Bank/2026-07-16_herbicide_free_campus_article_practice_contribute_to.md)
- [Find an outlet](Expression_Bank/2026-07-16_herbicide_free_campus_article_practice_find_an_outlet.md)

## Mini Response Bank

- [Balanced view on chemical use](Response_Bank/2026-07-16_herbicide_free_campus_article_practice_balanced_view_on_chemical_use.md)
- [Environmental responsibility](Response_Bank/2026-07-16_herbicide_free_campus_article_practice_environmental_responsibility.md)
- [Finding an outlet for pressure](Response_Bank/2026-07-16_herbicide_free_campus_article_practice_finding_an_outlet_for_pressure.md)
- [Describe my sandbox evolution game](Response_Bank/2026-07-12_ai_consciousness_and_evolution_describe_my_sandbox_evolution_game.md)
- [Discuss AI consciousness](Response_Bank/2026-07-12_ai_consciousness_and_evolution_discuss_ai_consciousness.md)

## Personal Stories

- [My Sandbox Evolution Game](Personal_Stories/2026-07-12_ai_consciousness_and_evolution_my_sandbox_evolution_game.md)
- [Zhejiang travel experience](Personal_Stories/2026-07-12_ai_game_ideas_zhejiang_travel_experience.md)

## How To Update This Brain

For the normal GPT web workflow, use the Project instructions and save a completed speaking case to `inbox/`. GitHub Actions will run the pipeline automatically.

```text
Read prompts/chatgpt_project_instructions.md, then create one SPEAKING_CASE_UPDATE in inbox/.
Do not rewrite existing case files directly.

[paste structured session summary]
```

For local Windows workflow:

```powershell
python scripts/run_pipeline.py inbox/2026-07-12_AI_Game_Ideas.md
```

`scripts/run_pipeline.py` processes the session, rebuilds indexes, creates today's review list, refreshes this README, updates the GitHub Pages app, and runs repository validation.

Do not edit `docs/data.json` manually except for debugging. It is generated from Markdown nodes.

## Content Rules

- English is used for model answers, examples, expressions, and speaking output.
- Chinese is used for grammar explanations, review notes, and learning guidance.
- The scripts organize and link your material. They do not rewrite your personal ideas.

_Dashboard last generated: 2026-07-27_
