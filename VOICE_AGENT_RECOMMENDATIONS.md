# Voice Agent Recommendations

## Core Recommendation

Build a narrow voice agent that gets on a call with the customer, asks the internal team's questions, captures the answers, collects any questions the customer has, and then hands the conversation to an LLM summarizer for the internal team.

Do not build a broad autonomous agent system right now.

The Anthropic article should be used as a simplicity warning, not as a checklist of patterns to combine. For this product, the right choice is a simple workflow around a focused voice agent.

## What The System Is

This system has two AI parts:

1. A voice agent that runs the customer call.
2. A post-call LLM summarizer that prepares the internal review packet.

Everything else should be normal product code: case creation, call link, status tracking, storage, and dashboard review.

## User Flow

1. Internal team creates an RFI case.
2. Internal team writes the questions they need answered.
3. Customer receives a call link through email or portal.
4. Customer joins the voice call.
5. Voice agent asks the internal team's questions one by one.
6. Voice agent captures the customer's answers.
7. Voice agent asks whether the customer has any questions.
8. Voice agent captures customer questions and any safe process-level responses.
9. Call ends.
10. LLM summarizer creates a structured summary for the internal team.
11. Internal team reviews the answers, customer questions, and summary.

## Voice Agent Scope

The voice agent's job is to conduct a focused interview.

It should:

- Ask the exact questions provided by the internal team.
- Ask them one at a time.
- Wait for the customer's answer before moving on.
- Ask a short clarifying follow-up only when the answer is unclear or incomplete.
- Capture the final answer for each internal question.
- Collect customer questions during the call.
- At the end, explicitly ask: "Do you have any questions for our team?"
- Mark unanswered or unclear items instead of pretending they were answered.

It should not:

- Invent extra risk questions.
- Run an open-ended investigation.
- Ask unlimited follow-ups.
- Make approval, underwriting, legal, pricing, or policy commitments.
- Claim it reviewed files unless that capability is explicitly added later.

## Follow-Up Rule

Use one simple rule:

The agent may ask at most one clarifying follow-up per internal question.

That follow-up is only for getting a usable answer to the question already written by the internal team. It is not for discovering new questions or expanding the scope of the call.

## Customer Questions

Customer questions are first-class output.

The system should store:

- Customer question text.
- Whether the agent answered it.
- The agent's response, if any.
- Whether it needs human follow-up.

The agent can answer basic process questions, such as what happens next or how answers will be reviewed.

The agent should defer questions about:

- Approval likelihood.
- Loan terms.
- Underwriting decisions.
- Policy exceptions.
- Legal or compliance commitments.

## Post-Call LLM Summarizer

After the call, run one LLM step that produces the internal review packet.

Inputs:

- Internal team questions.
- Captured answers.
- Customer questions.
- Transcript, if available.
- Case/application metadata, if available.

Outputs:

- Short call summary.
- Question-by-question answer table.
- Unanswered or unclear items.
- Customer questions.
- Items requiring internal follow-up.

This summarizer should not decide the case outcome. It prepares review material for the internal team.

## Recommended Stored Data

For each internal question:

- `question_id`
- `question_text`
- `answer_text`
- `answer_status`: `answered`, `unclear`, or `not_answered`
- `clarifying_follow_up_asked`
- `evidence_quote`

For each customer question:

- `question_text`
- `agent_response`
- `needs_human_followup`

For the call:

- `transcript`
- `summary_text`
- `review_packet_json`

## Near-Term Implementation Plan

### Slice 1: Improve Voice Capture

Replace plain answer capture with structured answer capture:

- answer text
- answer status
- evidence quote
- whether a follow-up was asked

Add a separate tool for capturing customer questions.

### Slice 2: Tighten Agent Instructions

Rewrite the voice agent prompt around the narrow interview behavior:

- ask only internal questions
- one follow-up max per question
- collect customer questions
- defer risky customer questions
- never pretend unclear answers are complete

### Slice 3: Add Post-Call Summarizer

Add a backend LLM call after the call completes.

It should generate the internal review packet from the captured answers, customer questions, and transcript.

### Slice 4: Update Internal Review UI

Show the internal team:

- each question
- captured answer
- answer status
- customer questions
- summary
- follow-up needed

## Later, Not Now

Google Drive can be added later as context for the internal team or summarizer.

Do not add Google Drive into the live call flow yet. The first version should prove the voice agent can reliably collect answers and customer questions.

Optional model-generated questions should also wait. They are not needed for the current version and would make the call harder to control.
