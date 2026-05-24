import { COLORS, paintBackground, card, textBox, kicker, titleBlock, cardHeader, pill, dot, bar } from './common.mjs';

function milestone(slide, ctx, x, y, w, h, accent, title, status, detail) {
  card(slide, ctx, x, y, w, h, COLORS.panel2, accent, title);
  dot(slide, ctx, x + 18, y + 20, 12, accent, 'milestone-dot');
  textBox(slide, ctx, {
    x: x + 38,
    y: y + 8,
    width: w - 52,
    height: 34,
    text: title,
    size: 18,
    color: COLORS.text,
    bold: true,
    typeface: 'Montserrat',
  });
  pill(slide, ctx, x + 18, y + 48, Math.min(156, w - 36), status, accent, COLORS.white, accent);
  textBox(slide, ctx, {
    x: x + 18,
    y: y + 90,
    width: w - 36,
    height: h - 102,
    text: detail,
    size: 14,
    color: COLORS.muted,
    typeface: 'Roboto',
  });
}

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  paintBackground(slide, ctx, COLORS.bg);
  kicker(slide, ctx, 74, 56, 'Roadmap');
  titleBlock(slide, ctx, 74, 80, 930, 'PR39C is done. PR40 and PR41 are the next gates.', 'No new edition work until the boot path is stable and the app launch matrix has real evidence behind it.');

  card(slide, ctx, 74, 190, 720, 430, COLORS.panel2, COLORS.line, 'roadmap-card');
  cardHeader(slide, ctx, 74, 190, 720, 'Milestones', COLORS.blue);
  milestone(slide, ctx, 98, 244, 200, 150, COLORS.green, 'PR39B', 'done', 'GRUB handoff debug pass. Proved the issue was observability and timeout behavior, not missing payloads.');
  milestone(slide, ctx, 316, 244, 200, 150, COLORS.green, 'PR39C', 'done', 'Unattended GRUB handoff, kernel/initramfs reachability, and live desktop confirmation in QEMU.');
  milestone(slide, ctx, 534, 244, 232, 150, COLORS.purple, 'Thunder God ARM64', 'next', 'Build the flagship ARM artifact and record it in the registry and VM matrix.');
  milestone(slide, ctx, 98, 418, 200, 150, COLORS.gold, 'PR40', 'pending', 'App launch matrix: record actual launch behavior for the active app set.');
  milestone(slide, ctx, 316, 418, 450, 150, COLORS.red, 'PR41', 'blocked', 'Release candidate gate. No promotion until registry, boot, telemetry, app launch, and safety evidence agree.');

  card(slide, ctx, 818, 190, 388, 430, COLORS.panel2, COLORS.line, 'gate-card');
  cardHeader(slide, ctx, 818, 190, 388, 'Release gate', COLORS.gold);
  textBox(slide, ctx, {
    x: 842,
    y: 246,
    width: 322,
    height: 44,
    text: 'Artifact provenance',
    size: 20,
    color: COLORS.text,
    bold: true,
    typeface: 'Roboto',
  });
  pill(slide, ctx, 1020, 244, 118, 'pass', COLORS.green, COLORS.white, COLORS.green);
  textBox(slide, ctx, { x: 842, y: 300, width: 322, height: 44, text: 'VM boot matrix', size: 20, color: COLORS.text, bold: true, typeface: 'Roboto' });
  pill(slide, ctx, 1020, 298, 118, 'partial', COLORS.gold, COLORS.white, COLORS.gold);
  textBox(slide, ctx, { x: 842, y: 354, width: 322, height: 44, text: 'App launch matrix', size: 20, color: COLORS.text, bold: true, typeface: 'Roboto' });
  pill(slide, ctx, 1008, 352, 130, 'pending', COLORS.panel3, COLORS.text, COLORS.line);
  textBox(slide, ctx, { x: 842, y: 408, width: 322, height: 44, text: 'Safety validation', size: 20, color: COLORS.text, bold: true, typeface: 'Roboto' });
  pill(slide, ctx, 1008, 406, 130, 'pending', COLORS.panel3, COLORS.text, COLORS.line);
  textBox(slide, ctx, { x: 842, y: 462, width: 322, height: 44, text: 'Release candidate', size: 20, color: COLORS.text, bold: true, typeface: 'Roboto' });
  pill(slide, ctx, 1000, 460, 138, 'blocked', COLORS.red, COLORS.white, COLORS.red);
  bar(slide, ctx, 842, 520, 324, 1, COLORS.line, 'gate-divider');
  textBox(slide, ctx, {
    x: 842,
    y: 538,
    width: 320,
    height: 60,
    text: 'The rule is simple: no boot success claim without observed stage evidence and a specific artifact hash.',
    size: 15,
    color: COLORS.muted,
    typeface: 'Roboto',
  });

  return slide;
}
