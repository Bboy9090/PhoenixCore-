import { COLORS, paintBackground, card, textBox, kicker, titleBlock, cardHeader, dot, bar, pill } from './common.mjs';

const phases = [
  ['preflight', COLORS.blue],
  ['manifest', COLORS.cyan],
  ['overlay', COLORS.gold],
  ['package', COLORS.purple],
  ['debootstrap', COLORS.blue],
  ['chroot', COLORS.cyan],
  ['initramfs', COLORS.gold],
  ['filesystem', COLORS.purple],
  ['artifact', COLORS.green],
  ['cleanup', COLORS.red],
];

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  paintBackground(slide, ctx, COLORS.bg);
  kicker(slide, ctx, 74, 56, 'Telemetry / build pipeline');
  titleBlock(slide, ctx, 74, 80, 840, 'Long builds are now measurable instead of mystical.', 'The telemetry model records phase timings, heartbeats, warnings, and artifact emission so the build can explain itself.');

  card(slide, ctx, 74, 188, 716, 428, COLORS.panel2, COLORS.line, 'pipeline-card');
  cardHeader(slide, ctx, 74, 188, 716, 'Canonical build phases', COLORS.blue);

  const left = 98;
  const top = 244;
  const rowGap = 60;
  const colGap = 164;
  phases.forEach(([phase, color], index) => {
    const row = index < 5 ? 0 : 1;
    const col = index < 5 ? index : index - 5;
    const x = left + col * colGap;
    const y = top + row * rowGap;
    dot(slide, ctx, x, y, 18, color, `${phase}-dot`);
    textBox(slide, ctx, {
      x: x + 28,
      y: y - 2,
      width: 116,
      height: 26,
      text: phase,
      size: 15,
      color: COLORS.text,
      bold: true,
      typeface: 'Roboto Mono',
      name: `${phase}-label`,
    });
  });

  bar(slide, ctx, 116, 292, 640, 2, COLORS.line, 'rule-top');
  bar(slide, ctx, 116, 352, 640, 2, COLORS.line, 'rule-bottom');
  pill(slide, ctx, 118, 414, 134, 'build aware', COLORS.panel3, COLORS.text, COLORS.line);
  pill(slide, ctx, 262, 414, 160, 'heartbeat visible', COLORS.panel3, COLORS.text, COLORS.line);
  pill(slide, ctx, 434, 414, 168, 'artifact registered', COLORS.panel3, COLORS.text, COLORS.line);
  pill(slide, ctx, 614, 414, 152, 'failures classified', COLORS.panel3, COLORS.text, COLORS.line);
  textBox(slide, ctx, {
    x: 118,
    y: 468,
    width: 620,
    height: 106,
    text: 'No fake ETA. No fake percentages. The watcher only reports the current phase, elapsed time, last successful phase, heartbeat count, and the latest real warning or failure class.',
    size: 18,
    color: COLORS.text,
    typeface: 'Roboto',
    name: 'telemetry-copy',
  });

  card(slide, ctx, 818, 188, 388, 428, COLORS.panel2, COLORS.line, 'summary-card');
  cardHeader(slide, ctx, 818, 188, 388, 'Home build summary', COLORS.gold);
  textBox(slide, ctx, {
    x: 842,
    y: 246,
    width: 320,
    height: 56,
    text: 'Elapsed: 3,243 s',
    size: 28,
    color: COLORS.text,
    bold: true,
    typeface: 'Montserrat',
    name: 'elapsed',
  });
  textBox(slide, ctx, {
    x: 842,
    y: 300,
    width: 320,
    height: 44,
    text: 'Warnings: 202',
    size: 22,
    color: COLORS.muted,
    typeface: 'Roboto',
    name: 'warnings',
  });
  textBox(slide, ctx, {
    x: 842,
    y: 342,
    width: 320,
    height: 56,
    text: 'Last successful phase: cleanup',
    size: 18,
    color: COLORS.text,
    typeface: 'Roboto',
    name: 'last-phase',
  });
  textBox(slide, ctx, {
    x: 842,
    y: 388,
    width: 320,
    height: 52,
    text: 'Telemetry status: recorded\nBuild status: completed',
    size: 16,
    color: COLORS.muted,
    typeface: 'Roboto Mono',
    name: 'build-status',
  });
  pill(slide, ctx, 842, 462, 150, 'release_blocked', COLORS.red, COLORS.white);
  pill(slide, ctx, 1002, 462, 176, 'desktop confirmed', COLORS.green, COLORS.white);
  textBox(slide, ctx, {
    x: 842,
    y: 522,
    width: 318,
    height: 72,
    text: 'Latest warning: Debian non-free-firmware repository component warnings. No hard failure. Build completed with a valid artifact hash.',
    size: 15,
    color: COLORS.muted,
    typeface: 'Roboto',
    name: 'latest-warning',
  });

  return slide;
}
