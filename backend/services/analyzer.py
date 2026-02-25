"""
SAAQ Analyzer Service
Sends survey responses to Claude API → returns structured report JSON.
"""
import json
import os
from datetime import datetime
from anthropic import Anthropic


def get_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=api_key)


def build_prompt(subject: str, responses: dict[str, str]) -> str:
    response_text = ""
    for q, a in responses.items():
        response_text += f"\n**Q: {q}**\nA: {a}\n"

    num_q = len(responses)
    version = "29Q" if num_q > 20 else "15Q"
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are an expert developmental psychologist and leadership diagnostician for SkillfullyAware.
Analyze the following survey responses for {subject} and produce a comprehensive SAAQ diagnostic report.

## SURVEY RESPONSES FOR: {subject}
{response_text}

## YOUR TASK
Produce a JSON object with the following structure. Be specific, evidence-based, and compassionate.
Every claim must be grounded in the actual survey text. Use direct references to what the person said.
Use curly/smart quotes (\u201C \u201D) for any quotes within string values to avoid JSON parsing issues.

## STAGE MODEL (S1-S10)
- S1 Reactive Self: Impulse-led, minimal regulation
- S2 Boundary Pusher: Tests limits, experiments with control
- S3 Tribal Belonger: Identity fused with group/role
- S4 Loyal Belonger: Duty, structure, role-based identity
- S5 Skilled Specialist: Precision, expertise, mastery
- S6 Results Driver: Goal-oriented, pragmatic, strategic
- S7 Perspective Connector: Multiple perspectives, empathy, dialogue
- S8 Systems Architect: Designs systems from core values
- S9 Integrative Seer: Holds paradox, meta-awareness
- S10 Meta-Builder: Synthesizes paradigms, transpersonal

## OUTPUT FORMAT
Return ONLY valid JSON (no markdown fences, no preamble) matching this schema:

{{
  "subject": "{subject}",
  "report_date": "{today}",
  "version": "{version}",

  "stage_estimate": {{
    "title": "S[N] \u2192 S[N+1] (Stage Name toward Next Stage Name)",
    "evidence_current": {{
      "stage": "S[N] (Stage Name)",
      "items": ["evidence 1 with quotes from responses", "evidence 2", "evidence 3", "evidence 4"]
    }},
    "evidence_emerging": {{
      "stage": "S[N+1] (Stage Name)",
      "items": ["evidence 1", "evidence 2", "evidence 3"]
    }},
    "fallbacks": ["fallback pattern 1", "fallback pattern 2", "fallback pattern 3"],
    "verdict": "Comprehensive paragraph summarizing developmental position and growth edges."
  }},

  "hemispheric_bias": {{
    "title": "Left/Right-[Dominant/Tilted/Anchored] (description)",
    "description": "Detailed paragraph on hemispheric processing patterns with evidence from responses."
  }},

  "power_centers": [
    {{"name": "Vital (Physical/Sexual)", "assessment": "Assessment", "notes": "Evidence from narrative"}},
    {{"name": "Emotional", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Relational", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Social/Leadership", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Financial", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Creative", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Intellectual", "assessment": "Assessment", "notes": "Evidence"}},
    {{"name": "Spiritual", "assessment": "Assessment", "notes": "Evidence"}}
  ],

  "power_center_kpis": [
    {{"center": "Vital", "kpi": "metric name", "baseline": "current state", "target": "90-day goal"}},
    {{"center": "Emotional", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Relational", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Social/Leadership", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Financial", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Creative", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Intellectual", "kpi": "metric", "baseline": "state", "target": "goal"}},
    {{"center": "Spiritual", "kpi": "metric", "baseline": "state", "target": "goal"}}
  ],

  "core_aptitudes": [
    {{"aptitude": "Autonomy/Influence", "assessment": "Level", "evidence": "From narrative"}},
    {{"aptitude": "Drive", "assessment": "Level", "evidence": "From narrative"}},
    {{"aptitude": "Perseverance", "assessment": "Level", "evidence": "From narrative"}},
    {{"aptitude": "Achievement", "assessment": "Level", "evidence": "From narrative"}},
    {{"aptitude": "Alignment", "assessment": "Level", "evidence": "From narrative"}},
    {{"aptitude": "Restraint", "assessment": "Level", "evidence": "From narrative"}}
  ],

  "shadow_indicators": [
    {{
      "root": "Root [fear/anger/shame/avoidance] \u2192 core dynamic",
      "expression": "Pattern Name: How it shows up specifically for this person.",
      "antidote": "Specific practices and reframes tailored to this person."
    }}
  ],

  "somatic_panel": {{
    "early_warnings": ["warning 1", "warning 2", "warning 3", "warning 4"],
    "green_lights": ["sign 1", "sign 2", "sign 3", "sign 4"],
    "reset_protocols": ["protocol 1 (specific breath/body technique)", "protocol 2", "protocol 3"]
  }},

  "awareness_summary": "Comprehensive paragraph synthesizing the whole person. Reference specific responses.",

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
      {{"name": "Focus on the Positive", "application": "Personalized for this person"}},
      {{"name": "Prime Ahead", "application": "Personalized"}},
      {{"name": "Name it to Tame it", "application": "Personalized"}},
      {{"name": "Shift / Open / Stay", "application": "Personalized"}},
      {{"name": "Zooming", "application": "Personalized"}}
    ],
    "if_then_protocols": ["If X \u2192 Then Y (specific to their patterns)", "protocol 2", "protocol 3"],
    "agreements_boundaries": ["boundary 1", "boundary 2", "boundary 3"],
    "milestones": ["milestone 1 (measurable)", "milestone 2", "milestone 3", "milestone 4"],
    "reflection_prompts": ["prompt 1", "prompt 2", "prompt 3"]
  }},

  "therapist_handoff": {{
    "stage": "Clinical stage summary.",
    "hemispheric_tilt": "Clinical hemispheric summary.",
    "somatic_profile": {{
      "stress_signs": "Clinical stress presentation.",
      "green_lights": "Clinical positive indicators.",
      "reset_levers": "Clinical interventions that work."
    }},
    "strengths": ["strength 1", "strength 2", "strength 3", "strength 4", "strength 5"],
    "risks": ["risk 1", "risk 2", "risk 3", "risk 4", "risk 5"],
    "clinical_interventions": ["intervention 1", "intervention 2", "intervention 3", "intervention 4", "intervention 5"]
  }},

  "qa_table": [
    {{"category": "Intro framing", "status": "Pass"}},
    {{"category": "Stage Estimate", "status": "Pass"}},
    {{"category": "Hemispheric Bias", "status": "Pass"}},
    {{"category": "Power Center Analysis", "status": "Pass"}},
    {{"category": "Power Center KPIs", "status": "Pass"}},
    {{"category": "Core Aptitudes", "status": "Pass"}},
    {{"category": "Shadow Indicators", "status": "Pass"}},
    {{"category": "Somatic Signature Panel", "status": "Pass"}},
    {{"category": "Awareness Quotient Summary", "status": "Pass"}},
    {{"category": "90-Day Practice Plan", "status": "Pass"}},
    {{"category": "Therapist Handoff Page", "status": "Pass"}},
    {{"category": "Appendix", "status": "Pass"}}
  ]
}}

CRITICAL:
1. Every assessment must cite specific words/phrases from the survey responses.
2. Be compassionate but honest. Growth-oriented, not flattering.
3. Shadow indicators must identify REAL patterns specific to THIS person.
4. The 90-day plan must be realistic and specific.
5. Use curly quotes (\u201C\u201D) for any quoted text within JSON strings.
6. Return ONLY valid JSON. No markdown, no preamble, no explanation."""


async def analyze_responses(subject: str, responses: dict[str, str]) -> dict:
    """Send responses to Claude API and return structured analysis."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    return json.loads(text)


def analyze_responses_sync(subject: str, responses: dict[str, str]) -> dict:
    """Synchronous version for CLI/batch use."""
    client = get_client()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    prompt = build_prompt(subject, responses)

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    return json.loads(text)
