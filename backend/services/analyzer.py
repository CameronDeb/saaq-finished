"""
SAAQ Analyzer Service
Sends survey responses to Claude API → returns structured report JSON.

v6 — All fixes:
  - Epistemic restraint, confidence calibration, observation vs inference
  - Sharper aptitude logic (shutdown ≠ restraint)
  - Developmental hemispheric framing
  - QA table validates reasoning quality
  - Narrative thickness detection
  - AI-assisted JSON repair as final fallback
  - 20000 max tokens for 30Q responses
  - STAGE-SPECIFIC EVIDENCE RULES: meta-awareness is S9, not S7
  - Clear distinctions between what counts as evidence for each stage
"""
import json
import os
import re
from datetime import datetime
from anthropic import Anthropic


def get_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=api_key)


def _clean_and_parse_json(text: str, client=None) -> dict:
    """Robustly parse JSON from Claude's response. If all else fails, ask Claude to fix it."""
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    first_brace = text.find("{")
    if first_brace > 0:
        text = text[first_brace:]

    last_brace = text.rfind("}")
    if last_brace >= 0:
        text = text[:last_brace + 1]

    # Normalize quotes and whitespace
    text = text.replace("\u201C", "'").replace("\u201D", "'")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\t", " ")

    # Attempt 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: raw_decode (handles trailing junk)
    try:
        decoder = json.JSONDecoder()
        result, _ = decoder.raw_decode(text)
        return result
    except json.JSONDecodeError:
        pass

    # Attempt 3: fix trailing commas
    fixed = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 4: ask Claude to fix the JSON
    if client is None:
        try:
            client = get_client()
        except Exception:
            pass

    if client:
        try:
            print("  Attempting AI-assisted JSON repair...")
            model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            fix_msg = client.messages.create(
                model=model,
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": f"The following JSON is malformed. Fix it and return ONLY valid JSON. Do not add any text before or after. Do not use markdown fences. Just the fixed JSON:\n\n{text[:30000]}"
                }],
            )
            fixed_text = fix_msg.content[0].text.strip()
            if fixed_text.startswith("```"):
                fixed_text = fixed_text.split("\n", 1)[1]
            if fixed_text.endswith("```"):
                fixed_text = fixed_text.rsplit("```", 1)[0]
            fixed_text = fixed_text.strip()
            fb = fixed_text.find("{")
            if fb > 0:
                fixed_text = fixed_text[fb:]
            lb = fixed_text.rfind("}")
            if lb >= 0:
                fixed_text = fixed_text[:lb + 1]
            return json.loads(fixed_text)
        except Exception as e:
            print(f"  AI repair failed: {e}")

    # Save debug file
    debug_path = os.path.join(os.path.dirname(__file__), "..", "debug_last_response.txt")
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f" DEBUG: Raw response saved to {debug_path}")
    except Exception:
        pass
    raise ValueError("Failed to parse Claude response as JSON after all attempts")


def build_prompt(subject: str, responses: dict[str, str]) -> str:
    response_text = ""
    for q, a in responses.items():
        response_text += f"\n**Q: {q}**\nA: {a}\n"

    num_q = len(responses)
    num_words = sum(len(a.split()) for a in responses.values())
    avg_words = num_words // max(num_q, 1)
    version = "30Q" if num_q > 20 else "15Q"
    today = datetime.now().strftime("%B %d, %Y")

    if avg_words < 20:
        thickness = "THIN"
        thickness_instruction = "Responses are SHORT and THIN. You MUST significantly lower confidence, reduce psychological depth claims, simplify therapist handoff language, and avoid deep wound formulations. State only what is directly observable."
    elif avg_words < 50:
        thickness = "MODERATE"
        thickness_instruction = "Responses are moderate length. Use measured confidence. Hypotheses are acceptable but must be clearly flagged as tentative."
    else:
        thickness = "RICH"
        thickness_instruction = "Responses are detailed and rich. You may offer deeper interpretive hypotheses, but still distinguish observation from inference."

    return f"""You are an expert developmental psychologist and leadership diagnostician for SkillfullyAware.
Analyze the following survey responses for {subject} and produce a comprehensive SAAQ diagnostic report.

## SURVEY RESPONSES FOR: {subject}
{response_text}

## NARRATIVE THICKNESS: {thickness} (average {avg_words} words per response)
{thickness_instruction}

## CRITICAL EPISTEMIC RULES

1. EPISTEMIC RESTRAINT: Use hedged, calibrated language throughout. NEVER assert inferred psychological dynamics as fact.
   - REQUIRED phrases: 'suggests', 'may indicate', 'appears consistent with', 'worth exploring', 'tentative hypothesis'
   - FORBIDDEN phrases: 'clearly shows', 'demonstrates that', 'reveals deep', 'proves', 'confirms', 'is driven by', 'stems from'

2. OBSERVATION vs INFERENCE: In EVERY section, clearly distinguish:
   - What the respondent EXPLICITLY SAID (use their actual words with single quotes)
   - What you INFER from that (flag with 'this may suggest', 'one possible reading is')

3. CONFIDENCE CALIBRATION: Match confidence to data thickness.
   - Short/vague answers = low confidence, surface-level only
   - Detailed/specific answers = moderate confidence, tentative hypotheses
   - Rich/emotional answers = higher confidence, deeper interpretation (still hedged)
   - NEVER make deep wound/shame formulations from a single short answer

## STAGE-SPECIFIC EVIDENCE RULES — CRITICAL

You MUST only attribute evidence to the correct stage. DO NOT mix up similar-sounding concepts across stages. Here is what counts as valid evidence for each stage:

S1 Reactive Self: Pure impulse, no regulation, force/avoidance in conflict
S2 Boundary Pusher: Testing limits, experimenting with control, rules as external
S3 Tribal Belonger: Identity fused with group, conformity for belonging, us-vs-them
S4 Loyal Belonger: Duty-bound, role-based identity, right/wrong binary thinking, rule-following, seeks order/predictability
S5 Skilled Specialist: Precision, expertise focus, mastery of systems, analytical rigor, procedural competence, can be perfectionistic
S6 Results Driver: Pragmatic goal-orientation, strategic thinking, measuring success by outcomes, efficiency focus, can over-drive
S7 Perspective Connector: SPECIFICALLY — holding multiple perspectives simultaneously, genuine empathy for opposing views, valuing dialogue over debate, seeking win-win, ethical action that considers multiple stakeholders. NOTE: Simple perspective-taking or asking questions about others' views is NOT necessarily S7 — it can appear at S5/S6. True S7 involves genuinely holding multiple valid viewpoints without collapsing into one.
S8 Systems Architect: Designing systems from core values, self-authored identity, integrating multiple perspectives into coherent strategy, vision-driven
S9 Integrative Seer: META-AWARENESS (seeing self AND systems as constructed), holding paradox without resolution, comfortable with fundamental ambiguity, transpersonal humility. NOTE: Meta-awareness is EXCLUSIVELY S9. Do NOT attribute it to S7 or any earlier stage.
S10 Meta-Builder: Synthesizing paradigms into new wholes, ecosystem-level work, transpersonal perspective

CRITICAL STAGE DISTINCTIONS — DO NOT CONFUSE THESE:
- META-COGNITION (thinking about your own thinking) can appear as early as S5. It is NOT evidence of S7 or S9.
- META-AWARENESS (seeing the self as a constructed perspective, recognizing all frameworks as partial) is S9 ONLY.
- PERSPECTIVE-TAKING (trying to understand someone else's view) appears at S5/S6. It becomes S7 only when multiple perspectives are held simultaneously as equally valid without defaulting to one.
- SELF-REFLECTION (noticing your own patterns) appears at S5+. It is NOT automatically S7 evidence.
- COMPLEXITY RECOGNITION (acknowledging gray areas) can be S6. It becomes S7 when the person actively values and seeks out opposing perspectives, not just acknowledges they exist.
- EMPATHY (feeling for others) appears at many stages. S7 empathy specifically involves understanding AND valuing fundamentally different worldviews.

## APTITUDE LOGIC — CRITICAL DISTINCTIONS

The seven SAAQ aptitudes form a developmental ladder:
Agency -> Drive -> Perseverance -> Achievement -> Appreciation -> Alignment -> Restraint

- RESTRAINT is NOT shutdown, suppression, inhibition, avoidance, or going quiet. It is MATURE capacity to consciously pause and choose wisely. If someone withdraws, numbs, or goes silent, score as 'underdeveloped' or 'distorted.'
- AGENCY is experiencing oneself as a SOURCE of action. Passivity and chronic deference = LOW agency.
- PERSEVERANCE: distinguish from compulsive pushing through. Healthy perseverance includes ability to rest.
- APPRECIATION: capacity to recognize value beyond personal attainment — shift from 'doing' to 'valuing.'

## HEMISPHERIC FRAMING
- Use DEVELOPMENTAL language, NOT neurological claims
- Say 'left-tilted processor' NOT 'significant left-hemispheric dominance'
- Frame as processing STYLE, not brain structure

## SHADOW INDICATORS
- Frame as hypotheses, not diagnoses
- Use 'possible', 'may reflect', 'worth exploring'
- Do NOT build wound narratives from single short answers

## THERAPIST HANDOFF
- Frame as 'structured reflections for clinical consideration'
- Use 'possible themes', 'areas to explore', 'preliminary observations'
- Should help therapist know where to START, not what to conclude

## QA TABLE
- Score REASONING QUALITY, not section completeness
- 'Pass' = well-evidenced and epistemically restrained
- 'Conditional — [reason]' = plausible but confidence may exceed evidence
- 'Needs Review — [reason]' = claims exceed data

## JSON RULES
- Use only straight single quotes (') inside string values
- No smart/curly quotes, no unescaped backslashes, no trailing commas
- Make sure every string is properly closed
- Return ONLY the JSON object. No text before or after.

## STAGE MODEL (S1-S10)
SAAQ uses a ten-stage continuum. Our stage model is an original synthesis of: Jean Piaget's cognitive development; Jane Loevinger and Susanne Cook-Greuter's ego development; Robert Kegan's subject-object theory; Clare Graves' value systems theory (Spiral Dynamics); Terri O'Fallon's STAGES model; and contemplative/somatic psychology.

## POWER CENTERS
Physical, Emotional, Relational, Social/Leadership, Financial, Creative, Intellectual, Spiritual

## OUTPUT FORMAT — RETURN ONLY VALID JSON:

{{
  "subject": "{subject}",
  "report_date": "{today}",
  "version": "{version}",

  "stage_estimate": {{
    "title": "S[N] -> S[N+1] (Stage Name toward Next Stage Name)",
    "evidence_current": {{
      "stage": "S[N] (Stage Name)",
      "items": ["OBSERVATION: respondent said '[quote]'. INFERENCE: this appears consistent with S[N] because [stage-specific reasoning]", "item 2", "item 3", "item 4"]
    }},
    "evidence_emerging": {{
      "stage": "S[N+1] (Stage Name)",
      "items": ["OBSERVATION: '[quote]'. INFERENCE: this may suggest emerging S[N+1] because [cite specific S[N+1] criteria from the stage rules above]", "item 2", "item 3"]
    }},
    "fallbacks": ["Under stress pattern 1", "pattern 2", "pattern 3"],
    "verdict": "Calibrated paragraph with confidence level. Reference specific stage criteria."
  }},

  "hemispheric_bias": {{
    "title": "[Left/Right]-Tilted (developmental description)",
    "description": "Developmental framing only. Distinguish observation from inference."
  }},

  "power_centers": [
    {{"name": "Physical", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Emotional", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Relational", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Social/Leadership", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Financial", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Creative", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Intellectual", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Spiritual", "assessment": "Assessment", "notes": "Evidence"}}
  ],

  "power_center_kpis": [
    {{"center": "Physical", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Emotional", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Relational", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Social/Leadership", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Financial", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Creative", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Intellectual", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Spiritual", "kpi": "metric", "baseline": "state", "target": "goal"}}
  ],

  "core_aptitudes": [
    {{"aptitude": "Agency", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Drive", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Perseverance", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Achievement", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Appreciation", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Alignment", "assessment": "Level", "evidence": "Evidence"}},
    {{"aptitude": "Restraint", "assessment": "Level", "evidence": "CRITICAL: shutdown/suppression/avoidance = LOW restraint"}}
  ],

  "shadow_indicators": [
    {{
      "root": "Possible pattern (hedged language)",
      "expression": "How it may show up. Observation vs inference clearly marked.",
      "antidote": "Practical, proportionate practices."
    }}
  ],

  "somatic_panel": {{
    "early_warnings": ["warning 1", "warning 2", "warning 3", "warning 4"],
    "green_lights": ["sign 1", "sign 2", "sign 3", "sign 4"],
    "reset_protocols": ["protocol 1", "protocol 2", "protocol 3"]
  }},

  "awareness_summary": "Calibrated synthesis with confidence level.",

  "hexaco_traits": [
    {{"trait": "Honesty-Humility", "assessment": "Level", "note": "Evidence"}},
    {{"trait": "Emotionality", "assessment": "Level", "note": "Evidence"}},
    {{"trait": "Extraversion", "assessment": "Level", "note": "Evidence"}},
    {{"trait": "Agreeableness", "assessment": "Level", "note": "Evidence"}},
    {{"trait": "Conscientiousness", "assessment": "Level", "note": "Evidence"}},
    {{"trait": "Openness to Experience", "assessment": "Level", "note": "Evidence"}}
  ],

  "practice_plan": {{
    "theme": "3-5 word theme. One sentence expansion.",
    "weekly_cadence": ["anchor 1", "anchor 2", "anchor 3", "anchor 4"],
    "daily_minimums": ["minimum 1", "minimum 2", "minimum 3", "minimum 4"],
    "five_practices": [
      {{"name": "Focus on the Positive", "application": "Personalized"}},
      {{"name": "Prime Ahead", "application": "Personalized"}},
      {{"name": "Name it to Tame it", "application": "Personalized"}},
      {{"name": "Shift / Open / Stay", "application": "Personalized"}},
      {{"name": "Zooming", "application": "Personalized"}}
    ],
    "if_then_protocols": ["protocol 1", "protocol 2", "protocol 3"],
    "agreements_boundaries": ["boundary 1", "boundary 2", "boundary 3"],
    "milestones": ["milestone 1", "milestone 2", "milestone 3", "milestone 4"],
    "reflection_prompts": ["prompt 1", "prompt 2", "prompt 3"]
  }},

  "therapist_handoff": {{
    "stage": "Preliminary observation for clinical consideration.",
    "hemispheric_tilt": "Processing style observation.",
    "somatic_profile": {{
      "stress_signs": "What respondent described.",
      "green_lights": "Positive indicators.",
      "reset_levers": "What they described working."
    }},
    "strengths": ["strength 1", "strength 2", "strength 3", "strength 4", "strength 5"],
    "risks": ["possible risk 1", "risk 2", "risk 3", "risk 4", "risk 5"],
    "clinical_interventions": ["consider exploring 1", "area 2", "area 3", "area 4", "area 5"]
  }},

  "qa_table": [
    {{"category": "Intro framing", "status": "Pass/Conditional/Needs Review"}},
    {{"category": "Stage Estimate", "status": "assessment — check stage evidence matches stage-specific criteria"}},
    {{"category": "Hemispheric Bias", "status": "assessment"}},
    {{"category": "Power Center Analysis", "status": "assessment"}},
    {{"category": "Power Center KPIs", "status": "assessment"}},
    {{"category": "Core Aptitudes", "status": "assessment — check restraint logic"}},
    {{"category": "Shadow Indicators", "status": "assessment"}},
    {{"category": "Somatic Signature Panel", "status": "assessment"}},
    {{"category": "Awareness Quotient Summary", "status": "assessment"}},
    {{"category": "90-Day Practice Plan", "status": "assessment"}},
    {{"category": "Therapist Handoff Page", "status": "assessment"}},
    {{"category": "Appendix", "status": "Pass"}}
  ]
}}

FINAL REMINDERS:
1. Cite specific words/phrases from responses.
2. Match confidence to data thickness.
3. 7 aptitudes: Agency -> Drive -> Perseverance -> Achievement -> Appreciation -> Alignment -> Restraint.
4. Restraint is MATURE SELF-GOVERNANCE. Shutdown/avoidance = LOW restraint.
5. Hemispheric framing is DEVELOPMENTAL, not neurological.
6. Shadows are HYPOTHESES, not diagnoses.
7. Therapist handoff suggests areas to EXPLORE.
8. QA table scores REASONING QUALITY.
9. STAGE EVIDENCE MUST MATCH STAGE-SPECIFIC CRITERIA. Meta-awareness = S9 ONLY. Simple perspective-taking = S5/S6. True simultaneous perspective-holding = S7.
10. Use only straight quotes (') inside strings. NO smart quotes.
11. Return ONLY valid JSON. No markdown, no preamble, no text after closing brace."""


async def analyze_responses(subject: str, responses: dict[str, str]) -> dict:
    """Send responses to Claude API and return structured analysis."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)

    message = client.messages.create(
        model=model,
        max_tokens=20000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    return _clean_and_parse_json(text, client=client)


def analyze_responses_sync(subject: str, responses: dict[str, str]) -> dict:
    """Synchronous version for CLI/batch use."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)

    message = client.messages.create(
        model=model,
        max_tokens=20000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    return _clean_and_parse_json(text, client=client)