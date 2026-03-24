"""
SAAQ Analyzer Service — v7 FINAL
Sends survey responses to Claude API → returns structured report JSON.

Incorporates Mark's RefiningSAAQ1 + RefiningSAAQ2-AlgorithmicTweaks:
  - Center of Gravity / Leading Edge / Crash Stage model
  - Content vs structure distinction (language ≠ stage)
  - Cross-domain consistency requirement (3+ domains for stage bump)
  - S7 inflation prevention (need 2+ structural indicators)
  - Operational stage definitions (S1-S10) from Mark
  - Shadow crash definitions (S1-S10) from Mark
  - Five scoring axes: authority, conflict, identity, stress, complexity
  - Epistemic restraint, confidence calibration
  - AI-assisted JSON repair
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
    text = text.replace("\u201C", "'").replace("\u201D", "'")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\t", " ")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        decoder = json.JSONDecoder()
        result, _ = decoder.raw_decode(text)
        return result
    except json.JSONDecodeError:
        pass
    fixed = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    if client is None:
        try:
            client = get_client()
        except Exception:
            pass
    if client:
        try:
            print("  Attempting AI-assisted JSON repair...")
            model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            fixed_text = ""
            with client.messages.stream(
                model=model, max_tokens=16000,
                messages=[{"role": "user", "content": f"The following JSON is malformed. Fix it and return ONLY valid JSON. No text before or after. No markdown fences:\n\n{text[:30000]}"}],
            ) as stream:
                for chunk in stream.text_stream:
                    fixed_text += chunk
            fixed_text = fixed_text.strip()
            if fixed_text.startswith("```"): fixed_text = fixed_text.split("\n", 1)[1]
            if fixed_text.endswith("```"): fixed_text = fixed_text.rsplit("```", 1)[0]
            fixed_text = fixed_text.strip()
            fb = fixed_text.find("{")
            if fb > 0: fixed_text = fixed_text[fb:]
            lb = fixed_text.rfind("}")
            if lb >= 0: fixed_text = fixed_text[:lb + 1]
            return json.loads(fixed_text)
        except Exception as e:
            print(f"  AI repair failed: {e}")

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
        t_inst = "Responses are SHORT. Lower confidence significantly. Surface-level observations only. No deep wound formulations."
    elif avg_words < 50:
        thickness = "MODERATE"
        t_inst = "Responses are moderate. Use measured confidence. Hypotheses must be flagged as tentative."
    else:
        thickness = "RICH"
        t_inst = "Responses are rich. Deeper hypotheses permitted but still distinguish observation from inference."

    return f"""You are an expert developmental psychologist and leadership diagnostician for SkillfullyAware.
Analyze the following survey responses for {subject}.

## RESPONSES FOR: {subject}
{response_text}

## NARRATIVE THICKNESS: {thickness} (avg {avg_words} words/response)
{t_inst}

## EPISTEMIC RULES
- Use hedged language: 'suggests', 'may indicate', 'appears consistent with', 'worth exploring'
- NEVER: 'clearly shows', 'proves', 'confirms', 'is driven by', 'stems from'
- ALWAYS distinguish OBSERVATION (what they said, with quotes) from INFERENCE (what you interpret)
- Match confidence to data thickness

## THREE-PART STAGING MODEL (CRITICAL)
Do NOT assign a single stage. Score THREE things separately:
1. CENTER OF GRAVITY (CoG) = where they operate most of the time, across multiple domains
2. LEADING EDGE = next-stage capacities that are real but not yet stable
3. CRASH STAGE = where they regress under stress (use shadow crash definitions below)

Format the stage title as: "CoG: S[N] (Name) | Leading Edge: S[N+1] (Name) | Crash: S[N] (Name)"

## CONTENT vs STRUCTURE RULE
Lexical sophistication NEVER by itself raises stage. Someone can TALK about complexity while OPERATING from S5/S6. Weight meaning-making STRUCTURE over vocabulary:
- How do they justify decisions?
- What counts as truth for them?
- How do they handle conflict?
- Can they decenter from their own position?
- Do they treat roles, systems, identity as constructed?

## CROSS-DOMAIN CONSISTENCY
No stage bump unless the same structure appears across 3+ domains: work/leadership, conflict/relationship, self-reflection, stress response, meaning/purpose, ethics, money, body/energy.

## S7 INFLATION PREVENTION
Perspective awareness alone does NOT equal S7. Require at least 2 of:
1. Identity organized around relationships (not just results)
2. Comfort holding tension between perspectives (not just acknowledging gray areas)
3. Self-critique of achievement identity
4. Evidence of relational repair practices
Without 2+, keep staged at S6 with pluralistic awareness.

## OPERATIONAL STAGE DEFINITIONS

S1 Impulsive Self: Meaning-making driven by immediate impulse, discomfort avoidance, raw need, survival reaction. Little reflective distance. Short time horizon.
Indicators: acts first reflects later, low frustration tolerance, fight/flight/freeze dominates, collapse into shutdown/lashing out/numbing/panic.

S2 Boundary-Tester: Centers on autonomy, control, advantage, testing limits. Rules as external constraints. Others as obstacles, allies, or audiences.
Indicators: pushes limits, resists control, exploits loopholes, status sensitivity, strategic charm, defiance, one-upmanship.

S3 Tribal Belonger: Identity fused with group, family, ideology. Rightness from loyalty, acceptance, shared norms.
Indicators: high conformity, 'people like us', fear of exclusion, borrowed beliefs, difficulty differentiating from family/culture.

S4 Conscientious Role Self: Identity organized around duty, responsibility, correctness, socially approved roles. Strong internalized rules.
Indicators: principled duty, clear right/wrong, role loyalty, guilt/shame when failing standards, respect for systems, suppression of impulses.

S5 Methodic Expert: Centers on competence, accuracy, mastery, internally coherent systems. Trust in method, evidence, precision.
Indicators: nuanced technical thinking, preference for method/proof, expertise identity, critiques vagueness, values accuracy over harmony, perfectionism.

S6 Outcome Achiever: Identity organized around results, effectiveness, strategy, performance, measurable progress.
Indicators: goals, metrics, optimization, efficiency, scaling, planning, achievement pressure, leadership through execution, burnout risk, self-worth tied to output.

S7 Perspective Connector: Meaning-making includes multiple valid perspectives, relational awareness, contextual thinking, recognition own view is partial.
Indicators: holds differing views without collapse into right/wrong, values mutual understanding, cognitive humility, recognizes context, seeks repair/inclusion/nuanced dialogue. Risk of over-relativism or conflict avoidance.

S8 Authoring Strategist: Identity self-authored and values-driven. Integrates multiple perspectives into coherent direction. Less defined by tribe, role, or performance.
Indicators: acts from chosen principles, builds values-aligned systems, decides amid ambiguity, distributes authority, coherent life/work authorship.

S9 Construct-Aware Integrator: Recognizes self, systems, roles, perspectives are constructed. Comfort with paradox, ambiguity, recursive self-awareness.
Indicators: sees frameworks as partial tools, observes identity-formation itself, high humility, paradox tolerance, tracks competing truths without urgent closure.

S10 Transpersonal Meta-Builder: Ecosystemic, transpersonal, generative across paradigms.
Indicators: cross-paradigm synthesis, ecosystem stewardship, transpersonal purpose, low attachment to personal credit.

## SHADOW CRASH DEFINITIONS (use these for Crash Stage)

S1 crash: Nervous system becomes primary. Shutdown, isolation, numbing, explosion, panic, freeze, doom-scrolling, helplessness, raw overwhelm.
S2 crash: Oppositionality, edge-testing, blame, contempt, domination, punishing others, power struggle.
S3 crash: People-pleasing, belonging panic, approval-seeking, hiding true view, conforming to preserve acceptance.
S4 crash: Rigidity, moralism, black-and-white judgment, harsh self-criticism, duty fixation, compulsive order, 'should' language, shame spirals.
S5 crash: Analysis paralysis, retreating into intellect, emotional detachment, over-explaining, inability to act without perfect certainty.
S6 crash: Productivity compulsion, metric-fixation, urgency, identity fusion with results, burnout, overwork, 'never enough.'
S7 crash: Diffusion, over-relativism, conflict avoidance, weak boundaries, over-accommodating, 'all perspectives are true' paralysis.
S8 crash: Over-authorship, isolation, strategic hardening, dismissing input, lone-wolf leadership.
S9 crash: Meta-detachment, disembodiment, endless reframing, inability to land, paradox without responsibility.
S10 crash: Grandiosity, spiritual bypass, ungrounded universality, sanctified self-importance.

## FIVE SCORING AXES (use these to determine stages)
1. Source of authority: external rules -> tribe -> expertise -> results -> mutuality -> self-authorship -> construct-awareness
2. Conflict handling: impulse -> dominance -> conformity -> duty -> analysis -> pragmatism -> dialogue -> principled authorship -> paradox-holding
3. Identity organization: need-based -> oppositional -> group-based -> role-based -> expert-based -> achiever-based -> pluralistic -> self-authored -> construct-aware
4. Stress response: collapse -> defiance -> merge -> rigidity -> analysis -> overdrive -> diffusion -> hardening -> meta-detachment
5. Time horizon / complexity: immediate -> tactical -> group-norm -> rule-order -> technical method -> strategic outcome -> multi-perspective -> values-systemic -> paradox/meta

## APTITUDE LOGIC
Seven aptitudes (developmental ladder): Agency -> Drive -> Perseverance -> Achievement -> Appreciation -> Alignment -> Restraint
- RESTRAINT = mature conscious choice. Shutdown/suppression/avoidance = LOW or DISTORTED restraint.
- AGENCY = source of action. Passivity/deference = LOW agency.
- APPRECIATION = recognizing value beyond personal attainment.

## HEMISPHERIC FRAMING
Developmental language only. 'Left-tilted processor' not 'left-hemispheric dominance.' Processing STYLE, not brain structure.

## POWER CENTERS
Physical, Emotional, Relational, Social/Leadership, Financial, Creative, Intellectual, Spiritual

## JSON RULES
- Straight single quotes (') inside strings only. No smart quotes.
- No trailing commas, no unescaped backslashes.
- Every string properly closed.
- Return ONLY the JSON object. Nothing before or after.

## OUTPUT — RETURN ONLY VALID JSON:

{{
  "subject": "{subject}",
  "report_date": "{today}",
  "version": "{version}",

  "stage_estimate": {{
    "title": "CoG: S[N] ([Name]) | Leading Edge: S[N+1] ([Name]) | Crash: S[N] ([Name])",
    "center_of_gravity": {{
      "stage": "S[N] ([Name])",
      "evidence": ["OBSERVATION: '[quote]'. INFERENCE: consistent with S[N] because [cite specific indicators from stage definitions]", "item 2", "item 3", "item 4"],
      "domains_observed": ["work/leadership", "conflict", "money", "etc — list which domains show this stage"]
    }},
    "leading_edge": {{
      "stage": "S[N+1] ([Name])",
      "evidence": ["OBSERVATION: '[quote]'. INFERENCE: may suggest emerging S[N+1] because [cite indicators]. NOTE: [explain why this is structural, not just vocabulary]", "item 2", "item 3"],
      "s7_criteria_met": ["list which of the 4 S7 criteria are met, if relevant"]
    }},
    "crash_stage": {{
      "stage": "S[N] ([Name])",
      "evidence": ["OBSERVATION: under stress respondent described '[quote]'. INFERENCE: this pattern appears consistent with S[N] crash: [cite shadow crash definition]", "item 2"]
    }},
    "verdict": "Calibrated paragraph. State CoG, Leading Edge, Crash Stage, and confidence level. Explain cross-domain consistency."
  }},

  "hemispheric_bias": {{
    "title": "[Left/Right]-Tilted ([developmental description])",
    "description": "Developmental framing only. Observation vs inference."
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
    {{"aptitude": "Restraint", "assessment": "Level", "evidence": "shutdown/avoidance = LOW restraint"}}
  ],

  "shadow_indicators": [
    {{
      "root": "Possible pattern (hedged)",
      "expression": "How it may show up. Observation vs inference marked.",
      "antidote": "Practical, proportionate practices."
    }},
    {{
      "root": "Second pattern",
      "expression": "Description",
      "antidote": "Practices"
    }},
    {{
      "root": "Third pattern",
      "expression": "Description",
      "antidote": "Practices"
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
      {{"name": "Focus on the Positive", "application": "Personalized to this person's specific responses and patterns"}},
      {{"name": "Prime Ahead", "application": "Personalized — reference specific situations they described"}},
      {{"name": "Name it to Tame it", "application": "Personalized — reference their specific emotional patterns"}},
      {{"name": "Shift / Open / Stay", "application": "Personalized — reference their specific stress triggers"}},
      {{"name": "Zooming", "application": "Personalized — reference their specific thought patterns"}}
    ],
    "if_then_protocols": ["If [specific trigger from responses] -> Then [concrete action]", "If [trigger 2] -> Then [action 2]", "If [trigger 3] -> Then [action 3]", "If [trigger 4] -> Then [action 4]"],
    "agreements_boundaries": ["boundary 1 specific to their patterns", "boundary 2", "boundary 3"],
    "milestones": ["Week 4: [measurable milestone]", "Week 8: [measurable milestone]", "Week 12: [measurable milestone]", "Day 90: [integration milestone]"],
    "reflection_prompts": ["prompt 1 specific to their growth edges", "prompt 2", "prompt 3"]
  }},

  "therapist_handoff": {{
    "stage": "Preliminary: CoG appears S[N] with leading edge S[N+1] and crash pattern at S[N]. [Brief clinical summary using hedged language].",
    "hemispheric_tilt": "Processing style observation: [left/right]-tilted with [specific patterns]. [Clinical relevance].",
    "somatic_profile": {{
      "stress_signs": "Respondent described: [specific quotes about stress/body]. Possible clinical patterns: [hedged observations].",
      "green_lights": "Respondent described: [what works for them]. These suggest: [clinical observations].",
      "reset_levers": "Based on described experience: [specific interventions anchored to what they said works]."
    }},
    "strengths": ["strength 1 grounded in evidence", "strength 2", "strength 3", "strength 4", "strength 5"],
    "risks": ["possible risk 1 (hedged)", "risk 2", "risk 3", "risk 4", "risk 5"],
    "clinical_interventions": ["Consider exploring: [area 1]", "Consider exploring: [area 2]", "Consider exploring: [area 3]", "Consider exploring: [area 4]", "Consider exploring: [area 5]"]
  }},

  "qa_table": [
    {{"category": "Intro framing", "status": "Pass/Conditional/Needs Review — [reason]"}},
    {{"category": "Stage Estimate", "status": "[assessment] — uses CoG/Edge/Crash model, cross-domain check"}},
    {{"category": "Hemispheric Bias", "status": "[assessment]"}},
    {{"category": "Power Center Analysis", "status": "[assessment]"}},
    {{"category": "Power Center KPIs", "status": "[assessment]"}},
    {{"category": "Core Aptitudes", "status": "[assessment] — restraint logic checked"}},
    {{"category": "Shadow Indicators", "status": "[assessment]"}},
    {{"category": "Somatic Signature Panel", "status": "[assessment]"}},
    {{"category": "Awareness Quotient Summary", "status": "[assessment]"}},
    {{"category": "90-Day Practice Plan", "status": "[assessment] — all subsections complete"}},
    {{"category": "Therapist Handoff Page", "status": "[assessment] — exploratory framing checked"}},
    {{"category": "Appendix", "status": "Pass"}}
  ]
}}

FINAL REMINDERS:
1. THREE-PART STAGING: CoG + Leading Edge + Crash Stage. Never a single label.
2. Content vs structure: vocabulary does not equal stage. Weight HOW they make meaning.
3. Cross-domain: need 3+ domains for stage assignment.
4. S7 requires 2+ structural indicators (not just perspective talk).
5. Shadow crashes use the specific crash definitions above.
6. All 12 sections must be COMPLETE with substantive content. Do not leave any section empty.
7. Practice plan sections C-G must each have specific, personalized content.
8. Therapist handoff must have substantive content in every field.
9. Restraint = mature governance. Shutdown = LOW restraint.
10. Hedged language throughout. Shadows are hypotheses.
11. Straight quotes only. Valid JSON only. Nothing before or after."""


async def analyze_responses(subject: str, responses: dict[str, str]) -> dict:
    """Send responses to Claude API and return structured analysis."""
    import asyncio
    # Run sync streaming in a thread to avoid blocking the event loop
    return await asyncio.to_thread(_analyze_sync, subject, responses)


def _analyze_sync(subject: str, responses: dict[str, str]) -> dict:
    """Internal sync function that does the actual API call with streaming."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)
    text = ""
    with client.messages.stream(
        model=model, max_tokens=32000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk
    text = text.strip()
    return _clean_and_parse_json(text, client=client)


def analyze_responses_sync(subject: str, responses: dict[str, str]) -> dict:
    """Synchronous version for CLI/batch use."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)
    text = ""
    with client.messages.stream(
        model=model, max_tokens=32000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk
    text = text.strip()
    return _clean_and_parse_json(text, client=client)