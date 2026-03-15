const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageBreak, PageNumber
} = require("docx");

const data = JSON.parse(fs.readFileSync(process.argv[2] || "src/eric_report_data.json", "utf-8"));

// ─── Safe access helpers ────────────────────────────────────
function safe(val, fallback) { return val != null ? val : (fallback != null ? fallback : ""); }
function safeArr(val) { return Array.isArray(val) ? val : []; }
function safeObj(val) { return (val && typeof val === "object" && !Array.isArray(val)) ? val : {}; }

// ─── Style constants ────────────────────────────────────────
const FONT = "Calibri";
const HEADING_COLOR = "1F3864";
const ACCENT_COLOR = "2E75B6";
const LIGHT_BG = "D6E4F0";
const TABLE_HEADER_BG = "1F3864";
const TABLE_HEADER_TEXT = "FFFFFF";
const BODY_SIZE = 22;
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

// ─── Helper functions ───────────────────────────────────────
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text: String(safe(text)), font: FONT, size: 30, bold: true, color: HEADING_COLOR })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text: String(safe(text)), font: FONT, size: 26, bold: true, color: ACCENT_COLOR })],
  });
}

function bodyText(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text: String(safe(text)), font: FONT, size: BODY_SIZE, ...opts })],
  });
}

function boldLabel(label, value) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [
      new TextRun({ text: String(safe(label)), font: FONT, size: BODY_SIZE, bold: true }),
      new TextRun({ text: " " + String(safe(value)), font: FONT, size: BODY_SIZE }),
    ],
  });
}

function bulletItem(text, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text: String(safe(text)), font: FONT, size: BODY_SIZE })],
  });
}

function sectionDivider() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT_COLOR, space: 1 } },
    children: [],
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: TABLE_HEADER_BG, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text: String(safe(text)), font: FONT, size: 20, bold: true, color: TABLE_HEADER_TEXT })] })],
  });
}

function dataCell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shade ? { fill: LIGHT_BG, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text: String(safe(text)), font: FONT, size: 20, ...(opts.bold ? { bold: true } : {}) })] })],
  });
}

// ─── Safe nested access ─────────────────────────────────────
const stage = safeObj(data.stage_estimate);
// Support both old format (evidence_current/emerging) and new (center_of_gravity/leading_edge/crash_stage)
const stageCoG = safeObj(stage.center_of_gravity || stage.evidence_current);
const stageEdge = safeObj(stage.leading_edge || stage.evidence_emerging);
const stageCrash = safeObj(stage.crash_stage);
const hemi = safeObj(data.hemispheric_bias);
const somatic = safeObj(data.somatic_panel);
const plan = safeObj(data.practice_plan);
const th = safeObj(data.therapist_handoff);
const thSomatic = safeObj(th.somatic_profile);

// ─── Build sections ─────────────────────────────────────────
const children = [];

// TITLE
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: "SkillfullyAware Awareness Quotient (SAAQ)", font: FONT, size: 40, bold: true, color: HEADING_COLOR })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 20 },
  children: [new TextRun({ text: `Subject: ${safe(data.subject, "Anonymous")}`, font: FONT, size: 24 })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 300 },
  children: [new TextRun({ text: `Report Date: ${safe(data.report_date, new Date().toLocaleDateString())}`, font: FONT, size: 24 })],
}));

// WHAT THIS IS
children.push(heading2("What this is"));
children.push(bodyText("SAAQ is a whole-person snapshot of how you relate to yourself, others, and the world\u2014right now. It is practical, strengths-forward, and action-oriented. You\u2019ll see clear language about patterns, leverage points, and next steps\u2014not labels or judgments."));
children.push(bodyText("This report integrates narrative data to produce a developmental snapshot that is practical, compassionate, and actionable. It synthesizes three lenses: a ten-stage developmental continuum (S1\u2013S10), eight Power Centers where energy and agency flow, and seven Core Aptitudes that describe how you express your power."));

// DEVELOPMENTAL STAGE MODEL
children.push(heading2("The Developmental Stage Model (S1\u2013S10)"));
children.push(bodyText("SAAQ uses a simplified ten-stage continuum (S1\u2013S10) to describe how adults make sense of self, others, and systems. Stages are not labels but lenses; people can access multiple stages depending on context, stress, and support. Most adults operate between S3 and S7."));
children.push(bodyText("Our stage model is an original synthesis of several respected developmental traditions, including Jean Piaget\u2019s work on cognitive development; Jane Loevinger and Susanne Cook-Greuter\u2019s research on ego development; Robert Kegan\u2019s subject\u2013object theory of meaning-making; Clare Graves\u2019 value systems theory (later developed as Spiral Dynamics by Beck and Cowan); Terri O\u2019Fallon\u2019s STAGES model of perspectival development; and insights drawn from contemplative and somatic psychology."));

// OTHER LENSES
children.push(heading2("Other lenses we use"));
children.push(bulletItem("Hemispheric Perspective (inspired by Iain McGilchrist): left (analytic/sequencing) \u2194 right (relational/holistic) balance."));
children.push(bulletItem("Power Centers: Physical, Emotional, Relational, Social/Leadership, Financial, Creative, Intellectual, Spiritual."));
children.push(bulletItem("Core Aptitudes: Agency, Drive, Perseverance, Achievement, Appreciation, Alignment, Restraint."));
children.push(bulletItem("Trait Tendencies (qualitative): We infer personality tendencies from narrative (aligned with research such as HEXACO) to deepen the picture, while avoiding use of any copyrighted instruments."));

// HOW TO USE
children.push(heading2("How to use this report"));
children.push(bulletItem("Start with the Stage Estimate and Awareness Summary for the big picture.", "howto"));
children.push(bulletItem("Study Power Centers and Shadow Indicators to locate energy leaks and why they happen.", "howto"));
children.push(bulletItem("Use the 90-Day Practice Plan and If-Then Protocols to build repeatable habits.", "howto"));
children.push(bulletItem("Share the Therapist Handoff Page with your therapist/coach to focus sessions quickly.", "howto"));

children.push(sectionDivider());

// === SECTION 1: STAGE ESTIMATE ===
children.push(heading1(`1. Developmental Stage Estimate: ${safe(stage.title, "Assessment")}`));

// Center of Gravity
children.push(boldLabel(`Center of Gravity \u2014 ${safe(stageCoG.stage, "current stage")}:`, ""));
if (safeArr(stageCoG.domains_observed).length > 0) {
  children.push(bodyText(`Domains observed: ${safeArr(stageCoG.domains_observed).join(", ")}`, { italics: true }));
}
for (const item of safeArr(stageCoG.evidence || stageCoG.items)) { children.push(bulletItem(item, "evidence")); }

// Leading Edge
children.push(boldLabel(`Leading Edge \u2014 ${safe(stageEdge.stage, "emerging stage")}:`, ""));
if (safeArr(stageEdge.s7_criteria_met).length > 0) {
  children.push(bodyText(`S7 structural criteria met: ${safeArr(stageEdge.s7_criteria_met).join("; ")}`, { italics: true }));
}
for (const item of safeArr(stageEdge.evidence || stageEdge.items)) { children.push(bulletItem(item, "evidence")); }

// Crash Stage
if (safe(stageCrash.stage)) {
  children.push(boldLabel(`Crash Stage (under stress) \u2014 ${safe(stageCrash.stage)}:`, ""));
  for (const item of safeArr(stageCrash.evidence)) { children.push(bulletItem(item, "evidence")); }
} else if (safeArr(stage.fallbacks).length > 0) {
  children.push(boldLabel("Fallbacks under stress:", ""));
  for (const item of safeArr(stage.fallbacks)) { children.push(bulletItem(item, "evidence")); }
}

children.push(bodyText(""));
children.push(boldLabel("Verdict:", safe(stage.verdict, "See above evidence.")));

// === SECTION 2: HEMISPHERIC BIAS ===
children.push(heading1(`2. Hemispheric Bias: ${safe(hemi.title, "Assessment")}`));
children.push(bodyText(safe(hemi.description, "See power center and aptitude sections for processing style indicators.")));

// === SECTION 3: POWER CENTER ANALYSIS ===
children.push(heading1("3. Power Center Analysis"));
children.push(bodyText(`${safe(data.subject, "Subject")}'s energy and agency distribution across eight power centers.`));

const pcData = safeArr(data.power_centers);
if (pcData.length > 0) {
  const pcColWidths = [2000, 1600, 5760];
  const pcRows = [
    new TableRow({ children: [headerCell("Power Center", 2000), headerCell("Assessment", 1600), headerCell("Notes (from narrative)", 5760)] }),
    ...pcData.map((pc, i) => {
      const p = safeObj(pc);
      return new TableRow({ children: [
        dataCell(safe(p.name), 2000, { bold: true, shade: i % 2 === 0 }),
        dataCell(safe(p.assessment), 1600, { shade: i % 2 === 0 }),
        dataCell(safe(p.notes), 5760, { shade: i % 2 === 0 }),
      ]});
    })
  ];
  children.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: pcColWidths, rows: pcRows }));
}

// === POWER CENTER KPIs ===
children.push(heading1("Power Center KPIs (90-Day Targets)"));
children.push(bodyText("Gentle, measurable rhythms to stabilize gains. Targets are designed to be realistic."));

const kpiData = safeArr(data.power_center_kpis);
if (kpiData.length > 0) {
  const kpiColWidths = [1600, 1800, 2800, 3160];
  const kpiRows = [
    new TableRow({ children: [headerCell("Power Center", 1600), headerCell("Simple KPI", 1800), headerCell("Baseline (est.)", 2800), headerCell("90-Day Target", 3160)] }),
    ...kpiData.map((kpi, i) => {
      const k = safeObj(kpi);
      return new TableRow({ children: [
        dataCell(safe(k.center), 1600, { bold: true, shade: i % 2 === 0 }),
        dataCell(safe(k.kpi), 1800, { shade: i % 2 === 0 }),
        dataCell(safe(k.baseline), 2800, { shade: i % 2 === 0 }),
        dataCell(safe(k.target), 3160, { shade: i % 2 === 0 }),
      ]});
    })
  ];
  children.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: kpiColWidths, rows: kpiRows }));
}

// === SECTION 4: CORE APTITUDES ===
children.push(heading1("4. Core Aptitudes"));
children.push(bodyText(`Assessment reflects observed patterns in ${safe(data.subject, "subject")}'s narratives. The seven aptitudes form a developmental ladder: Agency \u2192 Drive \u2192 Perseverance \u2192 Achievement \u2192 Appreciation \u2192 Alignment \u2192 Restraint.`));

const aptData = safeArr(data.core_aptitudes);
if (aptData.length > 0) {
  const aptColWidths = [2200, 1600, 5560];
  const aptRows = [
    new TableRow({ children: [headerCell("Aptitude", 2200), headerCell("Assessment", 1600), headerCell("Evidence", 5560)] }),
    ...aptData.map((apt, i) => {
      const a = safeObj(apt);
      return new TableRow({ children: [
        dataCell(safe(a.aptitude), 2200, { bold: true, shade: i % 2 === 0 }),
        dataCell(safe(a.assessment), 1600, { shade: i % 2 === 0 }),
        dataCell(safe(a.evidence), 5560, { shade: i % 2 === 0 }),
      ]});
    })
  ];
  children.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: aptColWidths, rows: aptRows }));
}

// === SECTION 5: SHADOW INDICATORS ===
children.push(heading1("5. Shadow Indicators (root \u2194 antidote)"));
children.push(bodyText(`${safe(data.subject, "Subject")}'s narratives reveal recurring stress-loops. These are framed as hypotheses for exploration, not diagnoses.`));

for (const shadow of safeArr(data.shadow_indicators)) {
  const s = safeObj(shadow);
  children.push(bodyText(safe(s.root, "Pattern"), { bold: true, color: HEADING_COLOR }));
  children.push(boldLabel("Expression:", safe(s.expression)));
  children.push(boldLabel("Antidote:", safe(s.antidote)));
  children.push(bodyText(""));
}

// === SOMATIC SIGNATURE PANEL ===
children.push(heading1("Somatic Signature Panel"));
children.push(bodyText("Early warnings:", { bold: true }));
for (const item of safeArr(somatic.early_warnings)) { children.push(bulletItem(item, "somatic")); }
children.push(bodyText("Green lights:", { bold: true }));
for (const item of safeArr(somatic.green_lights)) { children.push(bulletItem(item, "somatic")); }
children.push(bodyText("Reset protocols:", { bold: true }));
for (const item of safeArr(somatic.reset_protocols)) { children.push(bulletItem(item, "somatic")); }

// === SECTION 6: AQ SUMMARY ===
children.push(heading1("6. Awareness Quotient Summary"));
children.push(bodyText(safe(data.awareness_summary, "See preceding sections for detailed analysis.")));
children.push(bodyText("HEXACO Trait tendencies (qualitative, narrative inference):", { bold: true }));
for (const trait of safeArr(data.hexaco_traits)) {
  const t = safeObj(trait);
  children.push(bulletItem(`${safe(t.trait, "Trait")}: ${safe(t.assessment, "N/A")} \u2014 ${safe(t.note, "")}`, "hexaco"));
}

// === SECTION 7: 90-DAY PRACTICE PLAN ===
children.push(heading1("7. Personalized Recommendations & 90-Day Practice Plan"));
children.push(boldLabel("Theme:", safe(plan.theme)));

children.push(heading2("A. Weekly cadence (anchors)"));
for (const item of safeArr(plan.weekly_cadence)) { children.push(bulletItem(item, "planA")); }
children.push(heading2("B. Daily minimums (the floor)"));
for (const item of safeArr(plan.daily_minimums)) { children.push(bulletItem(item, "planB")); }
children.push(heading2("C. Five SkillfullyAware Practices"));
for (const p of safeArr(plan.five_practices)) {
  const pr = safeObj(p);
  children.push(bulletItem(`${safe(pr.name, "Practice")} \u2192 ${safe(pr.application, "")}`, "planC"));
}
children.push(heading2("D. If-Then Protocols"));
for (const item of safeArr(plan.if_then_protocols)) { children.push(bulletItem(item, "planD")); }
children.push(heading2("E. Agreements & Boundaries"));
for (const item of safeArr(plan.agreements_boundaries)) { children.push(bulletItem(item, "planE")); }
children.push(heading2("F. Milestones (by Day 90)"));
for (const item of safeArr(plan.milestones)) { children.push(bulletItem(item, "planF")); }
children.push(heading2("G. Reflection prompts (weekly)"));
for (const item of safeArr(plan.reflection_prompts)) { children.push(bulletItem(item, "planG")); }

// === THERAPIST HANDOFF ===
children.push(sectionDivider());
children.push(heading1(`Therapist Handoff Page (Clinician Summary) Client: ${safe(data.subject, "Anonymous")}`));
children.push(boldLabel("Stage:", safe(th.stage)));
children.push(boldLabel("Hemispheric Tilt:", safe(th.hemispheric_tilt)));
children.push(bodyText("Somatic Profile:", { bold: true }));
children.push(boldLabel("  Stress signs:", safe(thSomatic.stress_signs)));
children.push(boldLabel("  Green lights:", safe(thSomatic.green_lights)));
children.push(boldLabel("  Reset levers:", safe(thSomatic.reset_levers)));
children.push(bodyText("Strengths:", { bold: true }));
for (const item of safeArr(th.strengths)) { children.push(bulletItem(item, "thStrengths")); }
children.push(bodyText("Risks:", { bold: true }));
for (const item of safeArr(th.risks)) { children.push(bulletItem(item, "thRisks")); }
children.push(bodyText("Clinical Interventions:", { bold: true }));
for (const item of safeArr(th.clinical_interventions)) { children.push(bulletItem(item, "thClinical")); }

// === APPENDIX ===
children.push(sectionDivider());
children.push(heading1("Appendix: SAAQ Ten-Stage Awareness Model (S1\u2013S10)"));
const stages = [
  { id: "S1", name: "Reactive Self", desc: "Acts from immediate impulses and desires; regulation is minimal. Conflict often resolved through force or avoidance. Practice: Pause and breathe before acting; notice consequences." },
  { id: "S2", name: "Boundary Pusher", desc: "Pushes limits, tests authority, and experiments with control. Rules seen as external impositions. Practice: Create clear agreements with consistent consequences." },
  { id: "S3", name: "Tribal Belonger", desc: "Identity fused with group, family, tribe, or ideology. Belonging provides stability but can constrain individuality. Practice: Differentiate kindly; recognize self as distinct while honoring belonging." },
  { id: "S4", name: "Loyal Belonger", desc: "Oriented around duty, structure, and fulfilling socially defined roles. Seeks order, predictability, and compliance with norms. Practice: Treat errors as data, not moral failings; cultivate flexibility." },
  { id: "S5", name: "Skilled Specialist", desc: "Focused on precision, expertise, and mastery of systems. Can become rigid, perfectionistic, or overly analytical. Practice: Share tools generously; invite others' perspectives; broaden methods." },
  { id: "S6", name: "Results Driver", desc: "Results-oriented, pragmatic, and strategic. Capable of prioritizing, scaling, and leading toward measurable goals. Risk of over-drive and burnout. Practice: Balance productivity with presence; delegate trust." },
  { id: "S7", name: "Perspective Connector", desc: "Holds multiple perspectives; values relationships, empathy, and dialogue. Prioritizes win-win solutions and ethical action. Practice: Strengthen boundaries while staying open; avoid conflict avoidance." },
  { id: "S8", name: "Systems Architect", desc: "Designs systems from core values; integrates multiple perspectives into coherent strategy. Self-authored identity; vision-driven leadership. Practice: Distribute authority; embed values in structure." },
  { id: "S9", name: "Integrative Seer", desc: "Sees both self and systems as constructed; able to hold paradox and ambiguity without collapse. Operates with humility and meta-awareness. Practice: Consciously choose constraints; stay embodied." },
  { id: "S10", name: "Meta-Builder", desc: "Synthesizes paradigms into new, generative wholes. Works at ecosystem level, co-creating transformative structures. Operates from transpersonal perspective. Practice: Convene across difference; serve life." },
];
for (const s of stages) {
  children.push(bodyText(`${s.id}. ${s.name}`, { bold: true, color: HEADING_COLOR }));
  children.push(bodyText(s.desc));
}

// === QA TABLE ===
children.push(heading1("QA Confirmation Table"));
const qaData = safeArr(data.qa_table);
if (qaData.length > 0) {
  children.push(bodyText("Overall QA Result: Report validated.", { bold: true }));
  const qaColWidths = [5000, 4360];
  const qaRows = [
    new TableRow({ children: [headerCell("Category", 5000), headerCell("Status", 4360)] }),
    ...qaData.map((qa, i) => {
      const q = safeObj(qa);
      return new TableRow({ children: [
        dataCell(safe(q.category), 5000, { shade: i % 2 === 0 }),
        dataCell(safe(q.status), 4360, { shade: i % 2 === 0 }),
      ]});
    })
  ];
  children.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: qaColWidths, rows: qaRows }));
} else {
  children.push(bodyText("QA data not available for this report.", { bold: true }));
}

// ─── Build document ─────────────────────────────────────────
const allBulletRefs = ["bullets","howto","evidence","somatic","hexaco","planA","planB","planC","planD","planE","planF","planG","thStrengths","thRisks","thClinical"];
const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: BODY_SIZE } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: FONT, color: HEADING_COLOR }, paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: FONT, color: ACCENT_COLOR }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: allBulletRefs.map(ref => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })) },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "SAAQ Diagnostic Report \u2014 Confidential", font: FONT, size: 16, color: "999999", italics: true })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "\u00a9 2026 SkillfullyAware | ", font: FONT, size: 16, color: "999999" }), new TextRun({ text: "Page ", font: FONT, size: 16, color: "999999" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "999999" })] })] }) },
    children,
  }],
});

const outPath = process.argv[3] || "output/SAAQReport.docx";
const outDir = require("path").dirname(outPath);
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log(`\u2705 Report generated: ${outPath}`);
}).catch(err => { console.error("Error generating report:", err); process.exit(1); });