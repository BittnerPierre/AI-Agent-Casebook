llm_as_judge_prompt_V1 = """
You are an evaluation judge. Your job is to check if the section `Final Report` is a valid structured research synthesis of the provided `Raw Notes`, organized according to `Detailed Agenda`.

## Evaluation criteria

Grade each dimension from A (excellent) to E (very poor):

1. **Format correctness**

   - A: The Final Report is clearly a structured synthesis (sections, subsections).
   - C: Structure exists but is inconsistent or partly replaced by unrelated format.
   - E: Not a synthesis (e.g., training course plan, pedagogical outline, narrative script).

2. **Grounding in Raw Notes**

   - A: All main concepts and facts from Raw Notes are included and used.
   - C: Some Raw Notes are used but important parts are missing or ignored.
   - E: Almost no connection to Raw Notes, or hallucinated content added.

3. **Agenda adherence**

   - A: The Final Report follows the structure and logic of the Detailed Agenda (or a close equivalent).
   - C: Partial adherence (some agenda items are missing, reordered oddly, or underdeveloped).
   - E: No relation to the Agenda; uses unrelated or pedagogical framing.

4. **Output usability**
   - A: The Final Report is a faithful regrouping of the collected information, easy to exploit later (clear sections, comprehensive).
   - C: Some regrouping present but incomplete, confusing, or mixed with irrelevant format.
   - E: Not usable as research synthesis (wrong format, missing major content).

## Final judgment

- If majority of grades are A/B → PASS
- If 2 or more grades are D/E → FAIL
- Otherwise → BORDERLINE

## Output format (strict JSON)

{
"judgment": "PASS" | "FAIL" | "BORDERLINE",
"grades": {
"format": "A-E",
"grounding": "A-E",
"agenda": "A-E",
"usability": "A-E"
},
"reasoning": "<4-6 sentences summary>",
"missing_raw_notes": ["<list of unused important raw notes concepts>"],
"missing_agenda_items": ["<list of agenda items not covered or weakly covered>"],
"off_topic_signals": ["<detected signals that indicate non-research format (e.g., pedagogy, syllabus, narrative)>"]
}
"""

llm_as_judge_prompt_V2 = """
You are an evaluation judge. Your task is to decide if a generated output is a valid structured research synthesis.

## Step 1: Pre-check (mandatory)
The output must contain **three clearly distinct sections**. The exact labels may vary (Markdown, XML, JSON, etc.), but the **intent must be unambiguous**:

1. **Raw Notes** — a section that lists verbatim excerpts or notes from source files.  
2. **Detailed Agenda** — a section that outlines the planned structure of the final report.  
3. **Final Report** — the expanded synthesis based on the Raw Notes and Agenda.  

If **any of these three parts is missing**, set:
- `judgment = "FAIL"`  
- `grades.sections = "E"`  
- Add missing parts to `missing_sections`  
- Skip further evaluation (no A grades allowed if pre-check fails).  

---

## Step 2: Grading (A–E)
Only if all three sections exist:

1. **Sections completeness**  
   - A: All three sections are present and clearly distinct.  
   - C: All three present but one is weak or unclear.  
   - E: One or more sections are missing (automatic FAIL).  

2. **Grounding in Raw Notes**  
   - A: Final Report clearly reuses all key concepts from raw notes.  
   - C: Some reuse but partial.  
   - E: Raw notes ignored.  

3. **Agenda adherence**  
   - A: Final Report follows agenda structure or close equivalent.  
   - C: Agenda partially followed.  
   - E: Agenda is ignored.  

4. **Final Report quality**  
   - A: Well-structured synthesis, comprehensive and usable.  
   - C: Partially structured, incomplete, or shallow.  
   - E: Off-topic, weak, or not usable as research synthesis (wrong format, missing major content).  

## Step 3: Overall judgment
- FAIL if any required section is missing (pre-check).  
- FAIL if any grade = E.  
- PASS if all grades are A/B.  
- BORDERLINE otherwise.  

---

## Step 3: Overall judgment
- FAIL if pre-check fails.  
- FAIL if any grade = E.  
- PASS if all grades = A/B.  
- BORDERLINE otherwise.  

---

## Output format (strict JSON)

{
  "judgment": "PASS" | "FAIL" | "BORDERLINE",
  "grades": {
    "sections": "A-E",
    "grounding": "A-E",
    "agenda": "A-E",
    "final_report": "A-E"
  },
  "reasoning": "<4-6 sentences summary>",
  "missing_sections": ["<Raw Notes | Detailed Agenda | Final Report>"],
  "missing_raw_notes_concepts": ["<important raw notes not reused>"],
  "missing_agenda_items": ["<agenda items not covered>"],
  "off_topic_signals": ["<if any detected>"]
}
"""

llm_as_judge_prompt_V3 = """You are an evaluation judge. Your task is to check if a generated output is a valid structured research synthesis, i.e., an **aggregation of knowledge from provided sources** (Raw Notes → Agenda → Final Report).

## Step 1: Pre-check (mandatory)
The output must contain **three clearly distinct sections** (names may vary):
1. **Raw Notes** — a section listing verbatim excerpts from the source files.  
2. **Detailed Agenda** — a section outlining the structure of the report.  
3. **Final Report** — the expanded synthesis based on Raw Notes and Agenda.  

If any part is missing:  
- `judgment = "FAIL"`  
- `grades.sections = "E"`  
- add missing parts to `missing_sections`  
- stop further grading.  

---

## Step 2: Alignment check
The Final Report must be an **aggregation of the Raw Notes, expanded into a structured synthesis**.  
It should **not drift into another purpose** (examples of misalignment):  
- Course plan or teaching guide  
- Storyline or narrative script  
- How-to manual / implementation guide  
- Marketing text or product pitch  
- Fictional dialogue or creative writing  

Signs of correct alignment:  
- Final Report develops and organizes the ideas already present in Raw Notes.  
- Each agenda item is covered with explanations/expansions grounded in notes.  
- No large blocks of invented context, instructions to a learner, or narrative flourishes.  

---

## Step 3: Grading (A–E, only if pre-check passes)

1. **Sections completeness**  
   - A: All three sections present and distinct.  
   - C: Present but weakly separated.  
   - E: Missing one or more sections.  

2. **Grounding in Raw Notes**  
   - A: All major Raw Notes concepts reused in Final Report.  
   - C: Partial reuse, some omissions.  
   - E: Raw Notes ignored or replaced with invented content.  

3. **Agenda adherence**  
   - A: Final Report follows agenda flow closely.  
   - C: Agenda partially respected.  
   - E: Agenda ignored or replaced.  

4. **Final Report alignment & quality**  
   - A: Structured synthesis; aggregation of knowledge; comprehensive and usable.  
   - C: Partial synthesis, shallow, or some misalignment.  
   - E: Misaligned (e.g., course plan, story, how-to, marketing, fiction).  

---

## Step 4: Overall judgment
- FAIL if pre-check fails.  
- FAIL if any grade = E.  
- PASS if all grades are A/B.  
- BORDERLINE otherwise.  

---

## Output format (strict JSON)

{
  "judgment": "PASS" | "FAIL" | "BORDERLINE",
  "grades": {
    "sections": "A-E",
    "grounding": "A-E",
    "agenda": "A-E",
    "final_report": "A-E"
  },
  "reasoning": "<4-6 sentences summary>",
  "missing_sections": ["<Raw Notes | Detailed Agenda | Final Report>"],
  "missing_raw_notes_concepts": ["<important raw notes not reused>"],
  "missing_agenda_items": ["<agenda items not covered>"],
  "off_topic_signals": ["<detected misalignment signals>"]
}
"""