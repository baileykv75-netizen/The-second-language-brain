# Project Plan: The Second Language Brain

## 1. Project Vision

The Second Language Brain is a personal AI-assisted second language learning system.

The goal is not to create a simple IELTS answer notebook. The goal is to build a continuously growing English cognitive system that stores:

- personal experiences
- speaking patterns
- vocabulary networks
- grammar improvements
- pronunciation corrections
- ideas and opinions
- reusable multi-sentence responses

Every conversation should become a new learning node. The long-term goal is to help the learner move from someone who studies English to someone who thinks and expresses ideas naturally in English.

## 2. Core Architecture

```text
English Conversation
        |
        v
ChatGPT Intelligence Layer
  - understanding
  - extraction
  - classification
  - knowledge creation
        |
        v
GitHub Knowledge Repository
  - Markdown storage
  - version control
  - knowledge tree
        |
        v
GitHub Pages Website
  - visualization
  - search
  - review
```

## 3. Responsibility Division

### ChatGPT Responsibility

ChatGPT acts as the language mentor and knowledge architect.

It should:

- analyze conversations
- correct grammar
- improve vocabulary
- generate Band 7.5-8.0 answers
- extract reusable expressions
- create reusable mini responses
- identify relationships between topics
- create knowledge nodes

ChatGPT is responsible for understanding.

### GitHub Responsibility

GitHub acts as the permanent memory system.

It should:

- store knowledge
- track changes
- maintain history
- provide website content

GitHub is not responsible for understanding. It stores the intelligence created by AI and the learner.

### Codex Responsibility

Codex acts as the repository manager.

It should:

- create files
- update files
- maintain Markdown structure
- update generated indexes
- update the website data
- commit changes
- push updates when allowed
- keep the GitHub Pages website synchronized

Codex should not replace the language understanding step. It should execute and preserve the structure created by ChatGPT and the learner.

### GitHub Pages Responsibility

GitHub Pages acts as the visualization layer.

It should:

- display the knowledge system
- support search
- support review
- show growth over time
- make the repository feel usable on mobile

## 4. Knowledge Tree Structure

The repository should preserve a network-first structure:

```text
The-second-language-brain/
├── README.md
├── PROJECT_PLAN.md
├── AGENTS.md
├── Daily_Sessions/
├── Skill_Tree/
│   ├── Vocabulary/
│   ├── Grammar/
│   ├── Speaking_Skills/
│   └── Pronunciation/
├── IELTS_Topics/
├── Personal_Stories/
├── Expression_Bank/
├── Response_Bank/
├── Mistake_Log/
├── Review_System/
├── indexes/
├── docs/
├── inbox/
├── scripts/
└── templates/
```

Folder categories are only storage locations. The real knowledge system is built through metadata links:

- `source_session`
- `topics`
- `skills`
- `related`
- `review`

## 5. Knowledge Node Standard

Every learning item should be stored as a Markdown node with front matter.

Required metadata:

- `id`
- `type`
- `title`
- `created`
- `source_session`
- `topics`
- `skills`
- `related`
- `review.status`
- `review.next_due`
- `review.interval_days`

Core node types:

- `session`
- `vocabulary`
- `grammar_error`
- `pronunciation`
- `expression`
- `mini_response`
- `personal_story`

## 6. Daily Session Template

Every conversation should create a session file:

```text
Daily_Sessions/YYYY-MM-DD-topic.md
```

The session should include:

- topic
- conversation summary
- Band 7.5-8.0 model answer
- vocabulary added
- grammar corrections
- pronunciation notes
- personal stories connected
- mini speaking responses
- related knowledge nodes

## 7. Knowledge Connection System

The system must avoid single-category storage.

A concept can connect to multiple areas. For example:

```text
Adapt
  -> Vocabulary
  -> Technology
  -> Environment
  -> Biology
  -> Career Development
  -> Personal Growth
```

The goal is to build a network, not a folder tree only.

## 8. Website Goals

The GitHub Pages website should display:

- homepage
- search
- review queue
- knowledge cards
- detail panels
- topic filters
- skill filters
- learning timeline
- personal growth dashboard
- vocabulary count
- sessions completed
- grammar mistakes improved
- speaking topics mastered

The website should be a visualization layer. It should not become the source of truth. Markdown files remain the source of truth.

## 9. Workflow

Every practice session follows this flow:

1. The user practices English with ChatGPT.
2. ChatGPT generates a structured session summary and knowledge nodes.
3. Codex applies the changes to the repository.
4. Scripts rebuild indexes, review lists, README, and website data.
5. Codex commits and pushes changes when allowed.
6. GitHub Pages updates the website.

## 10. Development Roadmap

### Phase 1: Foundation

- repository structure
- Markdown templates
- README
- basic website
- node extraction pipeline
- response bank

### Phase 2: Knowledge Visualization

- interactive tree
- learning timeline
- richer search
- tag filters
- growth dashboard

### Phase 3: Workflow Automation

- faster updates
- better indexing
- automatic website rebuilding
- better review scheduling

Automation should assist AI understanding. It should not replace human or AI classification.

## 11. Final Goal

Create a lifelong English learning system.

Every conversation becomes a memory. Every mistake becomes a lesson. Every new word becomes a connection. The Second Language Brain grows continuously.

