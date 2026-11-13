// Builds presentation/Team2_Project18_Final_Presentation.pptx from the analysis outputs.
// Every number on the slides is read from presentation/deck_numbers.json and tables/text_numbers.json (written by code/report.py
// and code/final.py); the charts come from code/slide_figs.py.
// Run from the repository root:  npm install pptxgenjs react-icons react react-dom sharp  &&  node presentation/build_deck.js
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const sharp = require('sharp');
const gi = require('react-icons/gi');
const md = require('react-icons/md');

const ROOT = path.resolve(__dirname, '..');
const D = JSON.parse(fs.readFileSync(path.join(ROOT, 'presentation/deck_numbers.json'), 'utf8'));
const TX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tables/text_numbers.json'), 'utf8'));
const CH = (f) => path.join(ROOT, 'presentation/charts', f);
const OUT = path.join(ROOT, 'presentation/Team2_Project18_Final_Presentation.pptx');

// palette: forest ink, pine, plague red, pollen gold, LALIA blue
const INK = '17261F', PINE = '2B6A4E', RED = 'A3342B', GOLD = 'B07D1A', MUTED = '56635D', MIST = 'EEF3EF', RULE = 'D3DBD6', LALIA = '9ECAE1', LIGHT = 'CFE3D8';
const HEAD = 'Cambria', BODY = 'Calibri';
const W = 13.333, H = 7.5, MX = 0.6;

async function icon(Comp, color = '#FFFFFF', size = 256) {
  const svg = renderToStaticMarkup(React.createElement(Comp, { color, size }));
  const png = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return 'image/png;base64,' + png.toString('base64');
}

async function imgSize(f) { const m = await sharp(f).metadata(); return { w: m.width, h: m.height }; }
async function fit(slide, f, x, y, maxW, maxH, alt, align = 'center') {
  const s = await imgSize(f);
  let w = maxW, h = (maxW * s.h) / s.w;
  if (h > maxH) { h = maxH; w = (maxH * s.w) / s.h; }
  const dx = align === 'left' ? 0 : (maxW - w) / 2;
  slide.addImage({ path: f, x: x + dx, y: y + (maxH - h) / 2, w, h, altText: alt });
  return { x: x + dx, y: y + (maxH - h) / 2, w, h };
}

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.author = 'Team 2, EVST course project 18';
  pres.title = 'Environmental change before and after the First Pandemic';
  pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

  const footer = { text: { text: 'EVST Project 18 · Team 2 · Environmental change before and after the First Pandemic',
    options: { x: MX, y: 7.0, w: 9, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0 } } };
  pres.defineSlideMaster({
    title: 'CONTENT', background: { color: 'FFFFFF' },
    objects: [
      { placeholder: { options: { name: 'kicker', type: 'body', x: MX, y: 0.32, w: 12.1, h: 0.32, fontFace: BODY, fontSize: 12, bold: true,
        color: PINE, charSpacing: 2, margin: 0, valign: 'middle' }, text: '' } },
      { placeholder: { options: { name: 'title', type: 'title', x: MX, y: 0.66, w: 12.1, h: 0.78, fontFace: HEAD, fontSize: 30, bold: true,
        color: INK, margin: 0, valign: 'top', align: 'left' }, text: '' } },
      footer,
    ],
    slideNumber: { x: 12.15, y: 7.0, w: 0.6, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, align: 'right' },
  });
  pres.defineSlideMaster({
    title: 'DARK', background: { color: INK },
    objects: [
      { placeholder: { options: { name: 'kicker', type: 'body', x: MX, y: 1.55, w: 12.1, h: 0.35, fontFace: BODY, fontSize: 13, bold: true,
        color: '8FD1AE', charSpacing: 2, margin: 0 }, text: '' } },
      { placeholder: { options: { name: 'title', type: 'title', x: MX, y: 2.0, w: 11.9, h: 1.95, fontFace: HEAD, fontSize: 38, bold: true,
        color: 'FFFFFF', margin: 0, valign: 'top', align: 'left' }, text: '' } },
    ],
  });

  const IC = {
    wheat: await icon(gi.GiWheat), sheep: await icon(gi.GiSheep), olive: await icon(gi.GiOlive), tree: await icon(gi.GiPineTree),
    pollen: await icon(gi.GiPollenDust, '#8FD1AE'), check: await icon(md.MdCheckCircle, '#2B6A4E'), warn: await icon(md.MdWarningAmber),
    stats: await icon(md.MdQueryStats), time: await icon(md.MdTimeline), map: await icon(md.MdMap), thermo: await icon(md.MdOutlineThermostat),
    hour: await icon(gi.GiHourglass), globe: await icon(md.MdPublic), data: await icon(md.MdDataset), fact: await icon(md.MdFactCheck),
    drop: await icon(md.MdWaterDrop), history: await icon(md.MdHistory), micro: await icon(gi.GiMicroscope),
  };
  const circleIcon = (slide, ic, x, y, d = 0.62, fill = PINE, name = 'icon') => {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + ' circle' });
    slide.addImage({ data: ic, x: x + d * 0.19, y: y + d * 0.19, w: d * 0.62, h: d * 0.62, altText: name, objectName: name });
  };
  const content = (kicker, title) => {
    const s = pres.addSlide({ masterName: 'CONTENT' });
    s.addText(kicker.toUpperCase(), { placeholder: 'kicker' });
    s.addText(title, { placeholder: 'title' });
    return s;
  };
  const stat = (s, x, y, w, big, label, color = PINE, bigSize = 36) => {
    s.addText([{ text: big, options: { fontFace: HEAD, fontSize: bigSize, bold: true, color, breakLine: true } },
               { text: label, options: { fontFace: BODY, fontSize: 14, color: INK } }],
      { x, y, w, h: 1.25, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 2 });
  };
  const note = (s, speaker, mins, text) => s.addNotes(`[Suggested speaker: ${speaker} · about ${mins} min]\n\n${text}`);
  const R = D.regions, EMN = 'E. Mediterranean & Anatolia';

  // 1 ---------------- title
  let s = pres.addSlide({ masterName: 'DARK' });
  s.addText('EVST COURSE PROJECT 18 · TEAM 2 · FINAL EVALUATION', { placeholder: 'kicker' });
  s.addText('Environmental change before and after the First Pandemic', { placeholder: 'title' });
  s.addText('Fossil-pollen evidence for land use in Europe and the Mediterranean, 250–900 CE',
    { x: MX, y: 4.0, w: 10.5, h: 0.5, fontFace: BODY, fontSize: 20, color: LIGHT, margin: 0, isTextBox: true });
  s.addText('Jetty Jithendra Sai Ram · N Pavaneswar · Shaik Babu · Dr Shashang',
    { x: MX, y: 4.85, w: 11, h: 0.4, fontFace: BODY, fontSize: 17, color: 'FFFFFF', margin: 0, isTextBox: true });
  s.addText('IIIT Hyderabad · Monsoon 2026', { x: MX, y: 5.3, w: 8, h: 0.35, fontFace: BODY, fontSize: 14, color: 'A9BDB3', margin: 0, isTextBox: true });
  s.addImage({ data: IC.pollen, x: 11.2, y: 5.1, w: 1.5, h: 1.5, altText: 'pollen grain icon', transparency: 30 });
  note(s, 'N Pavaneswar', 0.5, 'Good morning. We are Team 2 and our project is number 18: environmental change before and after the First Pandemic. We used fossil pollen from about a thousand European and Mediterranean sites to ask whether the plague of 541 changed how people used the land.');

  // 2 ---------------- question
  s = content('The question', 'Two shocks hit the late Roman world at the same time');
  const t0 = 450, t1 = 800, ax0 = 0.9, ax1 = 12.4, X = (yr) => ax0 + ((yr - t0) / (t1 - t0)) * (ax1 - ax0);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X(536), y: 1.75, w: X(660) - X(536), h: 0.55, fill: { color: LALIA }, line: { color: LALIA }, rectRadius: 0.06, objectName: 'LALIA bar' });
  s.addText('Late Antique Little Ice Age, 536–660', { x: X(536) + 0.12, y: 1.75, w: X(660) - X(536) - 0.2, h: 0.55, fontFace: BODY, fontSize: 15, bold: true, color: INK, margin: 0, valign: 'middle', isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X(541), y: 2.45, w: X(750) - X(541), h: 0.55, fill: { color: RED }, line: { color: RED }, rectRadius: 0.06, objectName: 'plague bar' });
  s.addText('First Pandemic of plague, 541–750', { x: X(541) + 0.12, y: 2.45, w: X(750) - X(541) - 0.2, h: 0.55, fontFace: BODY, fontSize: 15, bold: true, color: 'FFFFFF', margin: 0, valign: 'middle', isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: ax0, y: 3.25, w: ax1 - ax0, h: 0, line: { color: MUTED, width: 1.5 }, objectName: 'time axis' });
  for (const yr of [500, 600, 700, 800]) {
    s.addShape(pres.shapes.LINE, { x: X(yr), y: 3.18, w: 0, h: 0.14, line: { color: MUTED, width: 1.5 } });
    s.addText(yr === 500 ? '500 CE' : String(yr), { x: X(yr) - 0.6, y: 3.33, w: 1.2, h: 0.3, fontFace: BODY, fontSize: 13, color: MUTED, align: 'center', margin: 0, isTextBox: true });
  }
  s.addText('If plague mortality emptied the countryside, farming pollen should fall and tree pollen rise after 541. But the cold arrived in the same years.',
    { x: MX, y: 3.8, w: 12.1, h: 0.5, fontFace: BODY, fontSize: 16, italic: true, color: INK, margin: 0, isTextBox: true });
  const Q = ['Did land use change after 541?', 'Can a change be separated from the LALIA cooling?', 'Does the HYDE 3.2 land-use model agree with the pollen?'];
  Q.forEach((q, i) => {
    const x = MX + i * 4.12;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.6, w: 3.86, h: 1.75, fill: { color: MIST }, line: { color: MIST }, rectRadius: 0.08, objectName: `question ${i + 1} card` });
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 4.85, w: 0.55, h: 0.55, fill: { color: RED }, line: { color: RED } });
    s.addText(String(i + 1), { x: x + 0.25, y: 4.85, w: 0.55, h: 0.55, fontFace: HEAD, fontSize: 20, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    s.addText(q, { x: x + 0.95, y: 4.8, w: 2.75, h: 1.35, fontFace: BODY, fontSize: 17, bold: true, color: INK, margin: 0, valign: 'top', isTextBox: true });
  });
  note(s, 'N Pavaneswar', 1.25, 'The First Pandemic of plague reached Egypt in 541 and Constantinople in 542, and came back in waves until about 750. In exactly the same years, volcanic eruptions in 536, 540 and 547 started the Late Antique Little Ice Age, the coldest decades of the Common Era. So any change in land use after 541 could be plague, could be cold, or could be neither. We ask three questions: did land use change, can we separate that from the cooling, and does the standard land-use reconstruction, HYDE 3.2, agree with what the pollen shows.');

  // 3 ---------------- indicators
  s = content('Method · the proxy', 'Fossil pollen shows how the land around a lake was used');
  const cards = [
    [IC.wheat, GOLD, 'Cereal', 'Cerealia-type, Secale, Triticum, Hordeum, Avena', 'Arable fields'],
    [IC.sheep, '7570B3', 'Pastoral', 'Plantago lanceolata, Rumex acetosa/acetosella, Rumex', 'Grazed meadows'],
    [IC.olive, RED, 'Cultivated trees', 'Olea, Juglans, Castanea, Vitis (OJCV)', 'Olive, walnut, chestnut and vine groves'],
    [IC.tree, PINE, 'Natural trees', 'All tree and shrub pollen except OJCV', 'How much woodland remained'],
  ];
  cards.forEach(([ic, col, name, taxa, means], i) => {
    const x = MX + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.75, w: 2.85, h: 3.6, fill: { color: MIST }, line: { color: MIST }, rectRadius: 0.08, objectName: `${name} card` });
    circleIcon(s, ic, x + 0.3, 2.05, 0.85, col, name);
    s.addText(name, { x: x + 0.3, y: 3.05, w: 2.4, h: 0.5, fontFace: HEAD, fontSize: 19, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(taxa, { x: x + 0.3, y: 3.55, w: 2.4, h: 0.9, fontFace: BODY, fontSize: 14, italic: true, color: MUTED, margin: 0, valign: 'top', isTextBox: true });
    s.addText(means, { x: x + 0.3, y: 4.45, w: 2.4, h: 0.75, fontFace: BODY, fontSize: 15, bold: true, color: col, margin: 0, valign: 'top', isTextBox: true });
  });
  s.addText([
    { text: 'All indicators are % of the terrestrial pollen sum. ', options: { bold: true } },
    { text: '“All anthropogenic” = cereal + pastoral + cultivated trees. We also measure rarefied taxon richness, E(S100). If plague emptied the fields: farming indicators fall, natural trees rise.' }],
    { x: MX, y: 5.6, w: 12.1, h: 0.9, fontFace: BODY, fontSize: 15, color: INK, margin: 0, valign: 'top', isTextBox: true });
  note(s, 'N Pavaneswar', 1.25, 'Lakes and bogs trap pollen every year, so a sediment core is a record of the vegetation around the site. We use the standard human-impact indicators: cereal pollen for arable fields, ribwort plantain and sorrel for grazing, olive, walnut, chestnut and vine for tree crops, and the remaining tree and shrub pollen for woodland. Everything is a percentage of the land pollen. The prediction is simple: if the plague killed enough farmers, fields go out of use, farming pollen falls and tree pollen rises within decades, which is what happened in parts of Europe after the Black Death.');

  // 4 ---------------- data
  s = content('Data', `1,099 Neotoma datasets, ${D.n_core} core sites`);
  await fit(s, CH('slide_map.png'), MX, 1.6, 6.9, 5.3, `Map of the ${D.n_core} core pollen sites coloured by region`, 'left');
  stat(s, 7.9, 1.65, 4.8, D.n_samples, 'pollen samples dated 0–1200 CE');
  stat(s, 7.9, 2.85, 4.8, `${D.n_sites} sites`, `from ${D.n_records} records; ${D.n_dup} duplicate records removed, cores from one lake pooled`);
  stat(s, 7.9, 4.2, 4.8, String(D.n_core), 'core sites: ≥ 2 samples both before (400–540) and after (541–750 CE)');
  stat(s, 7.9, 5.45, 4.8, String(R[EMN]), 'core sites in the Eastern Mediterranean & Anatolia (13 at mid-term)', RED);
  note(s, 'N Pavaneswar', 1.25, `We queried the Neotoma Paleoecology Database for every pollen record between 10 degrees west and 50 degrees east whose dating covers 400 to 750 CE: 1,099 datasets. After keeping samples with at least 100 grains, we have ${D.n_samples} samples from ${D.n_records} records at ${D.n_sites} sites. Two cleaning steps matter: Neotoma stores some cores twice, so we removed ${D.n_dup} duplicate records, and many lakes have several cores, so we pooled them so that each lake counts once. A core site needs at least two samples before and two after 541: there are ${D.n_core}, most of them in western and central Europe.`);

  // 5 ---------------- design
  s = content('Method · the tests', 'Compare before and after 541, and against what came before');
  const b0 = 250, b1 = 900, bx0 = MX, bx1 = MX + 12.1, BX = (yr) => bx0 + ((yr - b0) / (b1 - b0)) * (bx1 - bx0);
  [[250, 400, 'Earlier change\n250–399', 'C9D1CC', INK], [400, 541, 'Before\n400–540', LIGHT, INK], [541, 751, 'After: plague period\n541–750', RED, 'FFFFFF'], [751, 901, 'Following\n751–900', 'E3E8E5', INK]]
    .forEach(([a, b, lab, fill, col]) => {
      s.addShape(pres.shapes.RECTANGLE, { x: BX(a) + 0.03, y: 1.7, w: BX(Math.min(b, 900)) - BX(a) - 0.06, h: 0.95, fill: { color: fill }, line: { color: fill }, objectName: `window ${lab.replace('\n', ' ')}` });
      s.addText(lab, { x: BX(a) + 0.1, y: 1.7, w: BX(Math.min(b, 900)) - BX(a) - 0.2, h: 0.95, fontFace: BODY, fontSize: 15, bold: true, color: col, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    });
  const tests = [
    [IC.stats, 'Before vs after', 'Change in each indicator at each site; paired Wilcoxon test, bootstrap 95% CI'],
    [IC.history, 'Placebo', 'Is the rate of change across 541 faster than in 250–399 → 400–540?'],
    [IC.time, 'Window sensitivity', 'Narrower windows, boundary ±50 yr, first 60 years only, following period'],
    [IC.thermo, 'Regression', 'Site fixed effects: land use ~ temperature + plague period + trend, 300–900 CE'],
    [IC.hour, 'Dating uncertainty', '1,000 Monte Carlo realisations of every age model'],
    [IC.globe, 'HYDE 3.2', 'The model’s cropland and grazing around the same sites, same windows'],
  ];
  tests.forEach(([ic, h, t], i) => {
    const x = MX + (i % 3) * 4.12, y = 3.05 + Math.floor(i / 3) * 1.85;
    circleIcon(s, ic, x, y + 0.05, 0.62, PINE, h);
    s.addText([{ text: h, options: { bold: true, fontSize: 17, color: INK, breakLine: true } }, { text: t, options: { fontSize: 14, color: MUTED } }],
      { x: x + 0.8, y, w: 3.1, h: 1.6, fontFace: BODY, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 3 });
  });
  note(s, 'Shaik Babu', 1.75, 'The core design is a before-and-after comparison. For every site we average each indicator in 400 to 540 and in 541 to 750 and take the difference, then test across sites with a paired Wilcoxon test. Because farming was already changing before the plague, we use a placebo: is the change across 541 faster than the change between 250–399 and 400–540? We compare rates per century, because the windows are not equally far apart. We move the windows around, we fit a regression that separates temperature from the plague period, we perturb every age within its dating error a thousand times, and we compare the result with the HYDE land-use model.');

  // 6 ---------------- result 1
  s = content('Result 1 · Europe-wide', 'Farming grew after 541; it did not collapse');
  await fit(s, CH('slide_composite.png'), MX, 1.6, 8.6, 5.2, 'Composite curves of farming and natural tree pollen, 200–1000 CE', 'left');
  stat(s, 9.55, 1.75, 3.2, `${D.anthro} pp`, `all farming indicators, 541–750 vs 400–540 (${D.anthro_p})`, INK, 34);
  stat(s, 9.55, 3.35, 3.2, `${D.nat} pp`, `natural tree & shrub pollen (${D.nat_p})`, PINE, 34);
  stat(s, 9.55, 4.95, 3.2, `${D.cereal_up}% vs ${D.cereal_down}%`, 'of sites where cereal pollen rose vs fell', GOLD, 30);
  note(s, 'Shaik Babu', 1.5, `This is the main result. Each line is the average of site z-scores in 25-year bins with a 95% interval. Farming indicators, in black, are flat in the 4th century, start rising around 475, dip around 575 to 600, and rise steadily after 650. Natural tree pollen, in green, declines from the mid-7th century. Across the ${D.n_core} sites, farming indicators rose by ${D.anthro} percentage points after 541, natural trees fell by ${D.nat.replace('−', '')}, and cereal rose at ${D.cereal_up}% of sites against ${D.cereal_down}% that fell. These are small numbers because cereal pollen travels poorly, but the direction is consistent, and it is the opposite of abandonment.`);

  // 7 ---------------- robustness
  s = content('Result 1 · robustness', 'The rise holds for every window except the first 60 years');
  const hdr = ['Test', 'Windows (CE)', 'Sites', 'All farming (pp)', 'p'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: PINE } } }));
  const rows = [hdr].concat(D.sens.map((r) => [r.test, r.win, String(r.n), r.anthro, r.p].map((t, j) => ({ text: t, options: {
    color: r.sig ? INK : RED, bold: !r.sig || j === 0, fill: { color: r.sig ? 'FFFFFF' : 'FBEDEB' } } }))));
  s.addTable(rows, { x: MX, y: 1.7, w: 8.2, colW: [2.75, 2.15, 0.8, 1.6, 0.9], fontFace: BODY, fontSize: 15, color: INK, border: { type: 'solid', pt: 0.75, color: RULE }, rowH: 0.5, valign: 'middle' });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.2, y: 1.7, w: 3.5, h: 3.55, fill: { color: MIST }, line: { color: MIST }, rectRadius: 0.08, objectName: 'placebo card' });
  s.addText([{ text: 'Placebo', options: { fontFace: HEAD, fontSize: 20, bold: true, color: INK, breakLine: true } },
             { text: `${D.placebo_rate} vs ${D.placebo_rate_before}`, options: { fontFace: HEAD, fontSize: 30, bold: true, color: PINE, breakLine: true } },
             { text: `pp per century, across 541 vs the period before (${D.placebo_n} sites, ${D.placebo_p})`, options: { fontSize: 14, color: INK } }],
    { x: 9.45, y: 1.9, w: 3.05, h: 3.2, fontFace: BODY, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 6 });
  s.addText(`In the first 60 years of plague alone (${D.early_n} sites with enough samples) nothing changes significantly, in either direction.`,
    { x: MX, y: 5.45, w: 12.1, h: 0.75, fontFace: BODY, fontSize: 16, italic: true, color: INK, margin: 0, isTextBox: true });
  note(s, 'Shaik Babu', 1.0, `We checked that this does not depend on where we draw the line. Narrower windows, moving the boundary 50 years either way, and comparing with the period after 750 all give a significant rise. The placebo test says the rise across 541 is faster than the change in the period before: ${D.placebo_rate} against ${D.placebo_rate_before} points per century. The one test that does not show the rise is the first 60 years of plague on their own, 541 to 600, with only ${D.early_n} sites. We report that honestly: in the first plague decades we see neither a fall nor a rise.`);

  // 8 ---------------- regional
  s = content('Result 2 · regions', 'Western and central Europe carries the signal');
  const rh = ['Region', 'Sites', 'All farming (pp)', 'p', 'Dating test*'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: PINE } } }));
  const rr = [rh].concat(D.regional.map((r) => [r.region, String(r.n), r.anthro, r.p, `${r.mc}%`].map((t, j) => ({ text: t, options: {
    color: j === 3 && r.sig ? RED : INK, bold: (j === 3 && r.sig) || (j === 4 && +r.mc >= 90) } }))));
  s.addTable(rr, { x: MX, y: 1.7, w: 7.0, colW: [2.65, 0.75, 1.6, 0.9, 1.3], fontFace: BODY, fontSize: 15, color: INK, border: { type: 'solid', pt: 0.75, color: RULE }, rowH: 0.52, valign: 'middle' });
  s.addText('* share of 1,000 age-model realisations in which the change stays significant. Red p: < 0.05.',
    { x: MX, y: 5.0, w: 7.2, h: 0.4, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
  s.addText([{ text: 'Eastern Europe ', options: { bold: true } }, { text: 'also rises, matching Slavic settlement, but the result does not survive dating uncertainty.', options: { breakLine: true } },
             { text: 'Eastern Mediterranean: ', options: { bold: true } }, { text: 'the only region leaning downward; not significant.' }],
    { x: MX, y: 5.5, w: 7.2, h: 1.2, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 4 });
  await fit(s, CH('slide_change_map.png'), 8.0, 1.6, 4.75, 5.2, 'Map of the change in farming indicators at each site');
  note(s, 'Shaik Babu', 1.25, `By region, the Europe-wide result comes from western and central Europe, ${R['W. & Central Europe']} sites, where the rise is highly significant and survives every dating test. Eastern Europe also rises, at the time of the Slavic expansion, but that result is fragile. The British Isles and the western Mediterranean show no significant change. The Eastern Mediterranean is the only region that leans downward, and it is not significant. The map shows the same thing: blue increases dominate north of the Alps; the strongest red decreases are in the Levant, Crete and the southern Balkans.`);

  // 9 ---------------- climate
  s = content('Result 3 · regional climate', 'Europe cooled only slightly; the East was not one climate');
  await fit(s, CH('slide_climate.png'), MX, 1.55, 12.1, 4.5, 'Summer temperature in Europe and moisture at two Eastern Mediterranean caves');
  s.addText(`European mean cooled ${D.cool_cps}–${D.cool_bhm} °C (Alpine series ${D.cool_alps} °C) from 400–535 to 536–660 CE; the reconstruction’s 95% range is about ±${D.bhm_hw} °C. Kocain dried; Soreq did not, but has only ${D.soreq_n541} measurements in 541–660.`,
    { x: MX, y: 6.15, w: 12.1, h: 0.6, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true });
  note(s, 'Jetty Jithendra Sai Ram', 1.25, `On the left, summer temperature. The Alpine tree rings, in blue, show the famous LALIA plunge of ${D.alps_fall} degrees in the 31-year mean between ${D.alps_from} and ${D.alps_to}. But the European mean from PAGES 2k, in black, cooled only about a quarter to a third of a degree, and the 4th century was just as cool. On the right, moisture from two caves. Kocain in south-west Turkey dries from the late 4th century and is driest around 600. Soreq in Israel does not show this, although it has very few measurements in the 6th century. So the Eastern Mediterranean was not one climate region.`);

  // 10 ---------------- regression
  s = content('Result 4 · regression', 'No temperature effect; a short pause in 550–650');
  await fit(s, CH('slide_regression.png'), MX, 1.55, 9.0, 4.6, 'Regression coefficients for temperature and the two halves of the plague period', 'left');
  stat(s, 9.85, 1.6, 2.9, `${D.T} SD`, `effect of +1 SD (${D.T_sd} °C) warmer summers (${D.T_p})`, '2166AC', 30);
  stat(s, 9.85, 3.05, 2.9, `${D.m2a} SD`, `farming in 550–650 vs trend (${D.m2a_p}); W. & Central Europe ${D.m2_wce}\u00A0SD`, '762A83', 30);
  stat(s, 9.85, 4.5, 2.9, `${D.m2b} SD`, `in 650–750, back on trend (${D.m2b_p})`, 'E08214', 30);
  s.addText(`With a curved (quadratic) trend the pause disappears (${D.m5} SD, ${D.m5_p}): a modest slowdown, not a collapse.`,
    { x: MX, y: 6.2, w: 12.1, h: 0.6, fontFace: BODY, fontSize: 15, italic: true, color: INK, margin: 0, isTextBox: true });
  note(s, 'Jetty Jithendra Sai Ram', 1.75, `To separate plague from climate we fitted a regression on 25-year bins from 300 to 900 CE with a fixed effect per site, European summer temperature, a plague-period dummy and a long-term trend. Temperature has no detectable effect: one standard deviation of warmer summers changes farming by ${D.T} standard deviations (${D.T_p}), and it stays insignificant in every variant. When we split the plague period, the first century, 550 to 650, sits ${D.m2a.replace('−', '')} standard deviations below trend; the second century is back on trend. The pause is significant only in western and central Europe. Two caveats: it disappears if the trend is allowed to curve, and it is a small p-value among many coefficients. Our reading is a short pause in an expansion that was already under way.`);

  // 11 ---------------- E Med sample
  s = content('Result 5 · Eastern Mediterranean', 'A bigger sample, still no significant decline');
  await fit(s, CH('slide_emed_map.png'), MX, 1.6, 6.0, 4.4, 'Map of Eastern Mediterranean pollen sites', 'left');
  const eh = ['Sample', 'Cultivated trees (pp)', 'All farming (pp)'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: PINE } } }));
  const er = [eh].concat(D.em.map((r) => [r.sample, `${r.arbor} (p = ${r.arbor_p})`, `${r.anthro} (p = ${r.anthro_p})`].map((t) => ({ text: t }))));
  s.addTable(er, { x: 7.0, y: 1.7, w: 5.7, colW: [2.1, 1.8, 1.8], fontFace: BODY, fontSize: 14, color: INK, border: { type: 'solid', pt: 0.75, color: RULE }, rowH: 0.6, valign: 'middle' });
  s.addText([{ text: 'What changed since mid-term: ', options: { bold: true } },
             { text: `polygon-stored and calendar-dated records recovered, ${D.emc} core sites (13 before). The mid-term arboriculture decline shrinks from −0.42 to ${D.em[1].arbor} points and is driven by Dead Sea, Kournas (Crete) and Lerna.` }],
    { x: 7.0, y: 4.35, w: 5.7, h: 1.6, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: 'top', isTextBox: true });
  s.addText('Region here = south of 43°N, east of 19°E: Greece, S. Bulgaria, Turkey, Levant, Georgia, NW Iran.',
    { x: MX, y: 6.25, w: 12.1, h: 0.4, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
  note(s, 'Jetty Jithendra Sai Ram', 1.25, `At mid-term, the Eastern Mediterranean was our most interesting region: tree crops seemed to decline after 541 at 13 sites. We fixed two pipeline problems: records stored as lake outlines were skipped, and records with calendar or varve chronologies were excluded. Now we have ${D.emc} core sites, and ${D.emr} under a relaxed rule. With the bigger sample, the cultivated-tree decline shrinks from 0.42 to ${D.em[1].arbor.replace('−', '')} of a point and is not significant in any version. The large declines come from three sites with intensive olive cultivation: the Dead Sea, Lake Kournas on Crete and Lake Lerna.`);

  // 12 ---------------- E Med timing
  s = content('Result 5 · timing', 'Tree crops in the East were already lower before the plague');
  await fit(s, CH('slide_emed_timing.png'), MX, 1.55, 8.4, 5.2, 'Eastern Mediterranean composites of cultivated trees and farming with Kocain Cave moisture', 'left');
  const ET = TX.emed_timing, binTxt = (b) => `${b - 12.5}–${b + 12.5}`;
  [[`Peak ${binTxt(ET.arbor_peak_bin_300_540)} CE`, 'cultivated-tree composite, then lower for the rest of the 5th and 6th centuries'],
   [`Kocain wettest ${binTxt(ET.kocain_moisture_peak_bin)} CE`, `then drier: below its mean by ${binTxt(ET.kocain_first_bin_below_mean_after_peak)} CE, driest ${binTxt(ET.kocain_driest_bin_400_800)} CE`],
   ['No statistical link', 'no correlation after detrending, no moisture effect in the regression: drying is possible, not demonstrated']]
    .forEach(([h, t], i) => {
      s.addText([{ text: h, options: { bold: true, fontSize: 17, color: i === 2 ? RED : INK, breakLine: true } }, { text: t, options: { fontSize: 14, color: MUTED } }],
        { x: 9.2, y: 1.7 + i * 1.65, w: 3.55, h: 1.5, fontFace: BODY, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 3 });
    });
  note(s, 'Jetty Jithendra Sai Ram', 1.25, `Timing tells us more than the totals. The red line is the cultivated-tree composite for the Eastern Mediterranean. It peaks around 400 to 425 CE and is lower for the rest of the 5th and 6th centuries, more than a century before the plague. The dashed brown line is moisture at Kocain Cave: it falls from its 4th-century peak and is driest around 600. The two fall in the same period, but statistically they are not linked, so we say a climatic cause is possible, not demonstrated. Archaeobotany from the Negev points to market contraction in the 6th century, which pollen alone cannot test.`);

  // 13 ---------------- HYDE
  s = content('Result 6 · HYDE 3.2', 'HYDE 3.2 cropland moves the wrong way');
  await fit(s, CH('slide_hyde.png'), MX, 1.55, 6.3, 4.7, 'HYDE cropland and population around the sites compared with the pollen farming composite', 'left');
  const short = (r) => r.replace('E. Mediterranean & Anatolia', 'E. Mediterranean');
  s.addChart(pres.charts.BAR, [
    { name: 'HYDE cropland falls', labels: D.hyde_bars.map((b) => short(b.region)), values: D.hyde_bars.map((b) => b.crop_down) },
    { name: 'Cereal pollen falls', labels: D.hyde_bars.map((b) => short(b.region)), values: D.hyde_bars.map((b) => b.cereal_down) }],
    { x: 7.15, y: 1.55, w: 5.6, h: 4.7, barDir: 'bar', barGrouping: 'clustered', chartColors: ['8C510A', PINE], catAxisOrientation: 'maxMin',
      valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25, valAxisLabelFormatCode: '0"%"', showValue: true, dataLabelFormatCode: '0"%"',
      dataLabelPosition: 'outEnd', dataLabelFontSize: 11, dataLabelColor: INK, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11,
      catAxisLabelColor: INK, valAxisLabelColor: MUTED, valGridLine: { color: 'E3E8E5', size: 0.75 }, catGridLine: { style: 'none' },
      showLegend: true, legendPos: 't', legendFontSize: 13, legendColor: INK, showTitle: true, title: '% of sites where each falls, 541–750 vs 400–540',
      titleFontSize: 13, titleColor: INK, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY, legendFontFace: BODY, titleFontFace: BODY, barGapWidthPct: 60 });
  s.addText(`HYDE derives land use from population estimates, which dip to ${D.hyde_600}% of the 500 CE level in 600 CE. HYDE grazing, in contrast, rises at ${D.hyde_graz_up}% of sites, like pastoral pollen. Spatial match with cereal pollen: ρ = ${D.hyde_rho}.`,
    { x: MX, y: 6.3, w: 12.1, h: 0.6, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true });
  note(s, 'Jetty Jithendra Sai Ram', 1.5, `HYDE 3.2 is the land-use history used in climate and carbon-cycle models. It derives cropland from historical population estimates, and those estimates have a Late Antique decline bottoming out at 600 CE. Around our sites, HYDE has cropland falling after 541 at ${D.hyde_crop_down}% of sites; cereal pollen fell at only ${D.hyde_cereal_down}%. Its map also matches the pollen only weakly. One fair point for HYDE: its grazing land rises after 600, like our pastoral pollen. Our conclusion is that for the first millennium, HYDE cropland is a hypothesis built from population numbers, not an observation.`);

  // 14 ---------------- Monte Carlo
  s = content('Result 7 · dating uncertainty', '1,000 age-model runs: Europe holds, the regions do not');
  const mh = [{ text: '', options: { fill: { color: 'FFFFFF' } } }].concat(D.mc_names.map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: PINE }, align: 'center' } })));
  const shadeHex = (v) => { const g = Math.round(245 - (v / 100) * 170).toString(16).padStart(2, '0'); return g + g + g; };
  const mr = [mh].concat(D.mc_rows.map((r) => [{ text: r.scope, options: { bold: true } }].concat(r.cells.map((c, j) => ({ text: c, options: {
    align: 'center', bold: r.vals[j] >= 90, color: r.vals[j] >= 60 ? 'FFFFFF' : INK, fill: { color: shadeHex(r.vals[j]) } } })))));
  s.addTable(mr, { x: MX, y: 1.7, w: 12.1, colW: [2.9, 1.5, 1.5, 1.6, 1.6, 1.5, 1.5], fontFace: BODY, fontSize: 15, color: INK,
    border: { type: 'solid', pt: 1, color: 'FFFFFF' }, rowH: 0.56, valign: 'middle' });
  s.addText(`Cells: share of realisations in which the change across 541 is significant (p < 0.05); arrow = direction. Ages moved within their reported errors (median σ ${Math.round(TX.mc.sigma_median_yr)} yr where none is reported), errors correlated along each core.`,
    { x: MX, y: 5.85, w: 12.1, h: 0.7, fontFace: BODY, fontSize: 13, color: MUTED, margin: 0, isTextBox: true });
  note(s, 'Dr Shashang', 1.25, `Age models carry errors of about plus or minus ${D.med_unc} years, as long as our windows. So we moved every sample's age within its error a thousand times and redid the test each time. Cereal and all farming indicators rise significantly in ${Math.round(D.mc_rows[0].vals[3])} to ${Math.round(D.mc_rows[0].vals[0])} percent of runs Europe-wide; natural trees fall in ${Math.round(D.mc_rows[0].vals[4])} percent. Cultivated trees do not survive, and neither do the regional results outside western and central Europe: the eastern European rise survives in only ${Math.round(D.mc_rows[3].vals[3])} percent of runs, and no Eastern Mediterranean change survives in most runs. So the robust result is the Europe-wide one.`);

  // 15 ---------------- answers
  s = content('Answers', 'What the pollen says');
  const ans = [
    ['1 · Change after 541?', 'Yes: farming grew', 'Cereal, pastoral and all farming pollen rose at most sites and woodland fell, faster than before. No abandonment.', PINE],
    ['2 · Separate from the LALIA?', 'Partly', 'Temperature explains none of it. One modest pause, 550–650, overlaps both shocks and depends on how the trend is modelled.', GOLD],
    ['3 · Does HYDE agree?', 'No (cropland)', 'HYDE’s population-driven cropland decline to 600 CE is not in the pollen; its map matches weakly. Its grazing rise does match.', RED],
  ];
  ans.forEach(([q, a, t, col], i) => {
    const x = MX + i * 4.12;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.75, w: 3.86, h: 3.9, fill: { color: MIST }, line: { color: MIST }, rectRadius: 0.08, objectName: `answer ${i + 1} card` });
    s.addText(q.toUpperCase(), { x: x + 0.3, y: 2.0, w: 3.3, h: 0.4, fontFace: BODY, fontSize: 13, bold: true, color: col, charSpacing: 1, margin: 0, isTextBox: true });
    s.addText(a, { x: x + 0.3, y: 2.45, w: 3.3, h: 0.7, fontFace: HEAD, fontSize: 26, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.3, y: 3.3, w: 3.3, h: 2.8, fontFace: BODY, fontSize: 16, color: INK, margin: 0, valign: 'top', isTextBox: true });
  });
  note(s, 'Dr Shashang', 1.0, 'To answer our three questions. One: yes, land use changed after 541, but farming grew; there was no abandonment. Two: partly. Reconstructed temperature explains none of the variation, and the one pause we find overlaps both shocks. Three: no, HYDE cropland moves the wrong way, although its grazing land agrees with the pollen.');

  // 16 ---------------- since mid-term
  s = content('Since the mid-term', 'Everything planned is done, and one conclusion changed');
  const done = ['HYDE 3.2 compared with the pollen at every site', 'Regional climate: PAGES 2k Euro-Med, Kocain and Soreq caves', 'Fixed-effects regression: temperature vs plague period',
    `Eastern Mediterranean sample: 13 → ${D.emc} core sites`, '1,000-run Monte Carlo on dating errors', `${D.n_dup} duplicate records removed; cores of one lake pooled`];
  done.forEach((t, i) => {
    s.addImage({ data: IC.check, x: MX, y: 1.78 + i * 0.66, w: 0.4, h: 0.4, altText: 'done' });
    s.addText(t, { x: MX + 0.55, y: 1.73 + i * 0.66, w: 6.2, h: 0.5, fontFace: BODY, fontSize: 16, color: INK, margin: 0, valign: 'middle', isTextBox: true });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.55, y: 1.7, w: 5.15, h: 4.4, fill: { color: 'FBEDEB' }, line: { color: 'FBEDEB' }, rectRadius: 0.08, objectName: 'revised conclusion card' });
  s.addText([{ text: 'Revised', options: { fontFace: HEAD, fontSize: 22, bold: true, color: RED, breakLine: true } },
             { text: 'Mid-term: “a regional, not continental, mark, strongest in the eastern Mediterranean tree-crop economy.”', options: { italic: true, breakLine: true } },
             { text: `Now: that decline is not significant with ${D.emc} sites, began around 425 CE and does not survive dating errors. We no longer support the regional claim.`, options: { bold: true, breakLine: true } },
             { text: `Europe-wide rise: ${D.mid_anthro} → ${D.anthro} pp, now with a fair placebo test.` }],
    { x: 7.85, y: 1.9, w: 4.6, h: 4.0, fontFace: BODY, fontSize: 15, color: INK, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 8 });
  note(s, 'Dr Shashang', 1.0, 'Everything on our mid-term plan is done: HYDE, regional climate, the regression, the larger Eastern Mediterranean sample and the Monte Carlo. We also removed duplicate records and pooled cores from the same lake, which we had promised. And we want to be clear about one change: at mid-term we said the plague left a regional mark in the eastern Mediterranean tree-crop economy. With more sites and the dating test, that signal is not significant and began before the plague, so we have withdrawn it.');

  // 17 ---------------- limitations
  s = content('Limitations', 'What this study cannot show');
  const lim = [
    [IC.micro, 'Pollen is relative and patchy', 'Percentages, not areas; cereal pollen travels poorly; pollen records land use, not deaths.'],
    [IC.hour, 'Dating is coarse', `Median error ±${D.med_unc} years, as long as the windows; single plague waves cannot be resolved.`],
    [IC.history, 'The plague period holds other events', 'Lombard invasion, Avar and Slavic migrations, Persian–Byzantine war, Arab conquests.'],
    [IC.thermo, 'Climate records are thin', `No regional temperature series for the 6th-century Mediterranean; European mean ±${D.bhm_hw} °C; the two caves disagree.`],
    [IC.map, 'Unequal coverage', `${R['W. & Central Europe']} of ${D.n_core} sites in W. & Central Europe; no open archaeological dataset covers the whole area.`],
  ];
  lim.forEach(([ic, h, t], i) => {
    const y = 1.7 + i * 1.0;
    circleIcon(s, ic, MX, y + 0.05, 0.6, i % 2 ? GOLD : PINE, h);
    s.addText([{ text: h + '  ', options: { bold: true, color: INK } }, { text: t, options: { color: MUTED } }],
      { x: MX + 0.8, y, w: 11.3, h: 0.75, fontFace: BODY, fontSize: 16, margin: 0, valign: 'middle', isTextBox: true });
  });
  note(s, 'Dr Shashang', 1.0, 'Our limits: pollen percentages are relative and cereal pollen is under-represented; pollen tells us about land use, not about how many people died. Dating errors are as long as our windows, so individual plague waves cannot be resolved. The plague period also contains wars and migrations. Temperature records for the Mediterranean in the 6th century do not exist, and the two cave records disagree. And most of our sites are in western and central Europe; we found no open archaeological dataset covering the whole study area.');

  // 18 ---------------- conclusion
  s = pres.addSlide({ masterName: 'DARK' });
  s.addText('CONCLUSION', { placeholder: 'kicker' });
  s.addText('The First Pandemic left no continental footprint of farmland abandonment in the pollen record', { placeholder: 'title' });
  s.addText([{ text: 'Farming kept expanding through the 6th–8th centuries, with a modest pause in 550–650 CE that temperature does not explain.', options: { breakLine: true } },
             { text: 'In the Eastern Mediterranean, tree crops were already lower a century before the plague.', options: { breakLine: true } },
             { text: 'HYDE 3.2 cropland, built on population estimates, moves opposite to the pollen.' }],
    { x: MX, y: 4.3, w: 11.6, h: 1.7, fontFace: BODY, fontSize: 18, color: LIGHT, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 8 });
  s.addText('Thank you · questions welcome', { x: MX, y: 6.3, w: 8, h: 0.45, fontFace: HEAD, fontSize: 20, italic: true, color: '8FD1AE', margin: 0, isTextBox: true });
  note(s, 'Dr Shashang', 0.5, 'To conclude: the First Pandemic may have been demographically severe, but it left no continental footprint of farmland abandonment in the pollen record. Thank you; we are happy to take questions.');

  // 19 ---------------- sources
  s = content('Sources and reproducibility', 'Data, references and code');
  s.addText([{ text: 'Data', options: { fontFace: HEAD, fontSize: 18, bold: true, color: PINE, breakLine: true } },
             { text: 'Neotoma Paleoecology Database (Williams et al. 2018): 1,099 pollen datasets', options: { bullet: true, breakLine: true } },
             { text: 'HYDE 3.2.1 (Klein Goldewijk et al. 2017), doi:10.17026/dans-25g-gez3', options: { bullet: true, breakLine: true } },
             { text: 'PAGES 2k Euro-Med (Luterbacher et al. 2016); Alpine tree rings (Büntgen et al. 2011)', options: { bullet: true, breakLine: true } },
             { text: 'Kocain Cave (Jacobson et al. 2021); Soreq Cave (Orland et al. 2009), via NOAA', options: { bullet: true } }],
    { x: MX, y: 1.65, w: 5.9, h: 3.4, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 6 });
  s.addText([{ text: 'Key references', options: { fontFace: HEAD, fontSize: 18, bold: true, color: PINE, breakLine: true } },
             { text: 'Mordechai et al. 2019, PNAS: the Justinianic Plague, an inconsequential pandemic?', options: { bullet: true, breakLine: true } },
             { text: 'Büntgen et al. 2016, Nature Geoscience: the Late Antique Little Ice Age', options: { bullet: true, breakLine: true } },
             { text: 'Izdebski et al. 2022, Nature Ecology & Evolution: Black Death land use', options: { bullet: true, breakLine: true } },
             { text: 'Kaplan et al. 2017, Land: historical land-use scenarios vs pollen', options: { bullet: true, breakLine: true } },
             { text: 'Fuks et al. 2020, PNAS: Late Antique Negev viticulture', options: { bullet: true } }],
    { x: 6.85, y: 1.65, w: 5.9, h: 3.4, fontFace: BODY, fontSize: 14, color: INK, margin: 0, valign: 'top', isTextBox: true, paraSpaceAfter: 6 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 5.35, w: 12.1, h: 1.1, fill: { color: MIST }, line: { color: MIST }, rectRadius: 0.08, objectName: 'code card' });
  circleIcon(s, IC.data, MX + 0.3, 5.6, 0.6, PINE, 'code');
  s.addText([{ text: 'github.com/RiyasShaik/evst-project18-team2', options: { bold: true, breakLine: true } },
             { text: './run.sh regenerates every number, table and figure in the report and on these slides (about 2 minutes, offline).' }],
    { x: MX + 1.1, y: 5.45, w: 10.8, h: 0.9, fontFace: BODY, fontSize: 15, color: INK, margin: 0, valign: 'middle', isTextBox: true });
  note(s, 'Dr Shashang', 0.25, 'All data are open, and the repository reproduces every number in the report and on these slides with one command.');

  await pres.writeFile({ fileName: OUT });
  console.log('written', OUT);
})();
