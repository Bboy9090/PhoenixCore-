import { COLORS, paintBackground, card, textBox, kicker, titleBlock, cardHeader, pill } from './common.mjs';

function editionCard(slide, ctx, x, y, w, h, accent, title, role, status, detail, muted = false) {
  const fill = muted ? COLORS.panel : COLORS.panel2;
  const line = muted ? COLORS.line : accent;
  card(slide, ctx, x, y, w, h, fill, line, title);
  cardHeader(slide, ctx, x, y, w, title, accent);
  textBox(slide, ctx, {
    x: x + 18,
    y: y + 58,
    width: w - 36,
    height: 28,
    text: role,
    size: 20,
    color: COLORS.text,
    bold: true,
    typeface: 'Montserrat',
    name: 'role',
  });
  textBox(slide, ctx, {
    x: x + 18,
    y: y + 92,
    width: w - 36,
    height: 44,
    text: detail,
    size: 14,
    color: COLORS.muted,
    typeface: 'Roboto',
    name: 'detail',
  });
  pill(slide, ctx, x + 18, y + h - 44, Math.min(210, w - 36), status, muted ? COLORS.panel3 : accent, muted ? COLORS.muted : COLORS.white, muted ? COLORS.line : accent);
}

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  paintBackground(slide, ctx, COLORS.bg);
  kicker(slide, ctx, 74, 56, 'Active lineup');
  titleBlock(slide, ctx, 74, 80, 760, 'The active lineup is intentionally small.', 'Four shipping editions plus Native as research-only. That keeps the build, boot, telemetry, and release burden survivable.');

  editionCard(slide, ctx, 74, 184, 352, 170, COLORS.blue, 'Home', 'Mainstream stable desktop', 'desktop proven', 'The baseline: live desktop reached in QEMU x86_64 UEFI.', false);
  editionCard(slide, ctx, 464, 184, 352, 170, COLORS.purple, 'Thunder God', 'Flagship performance edition', 'arm64 next', 'The premium ARM target. Build and desktop proof still need to be earned.', false);
  editionCard(slide, ctx, 854, 184, 352, 170, COLORS.gold, 'Aurelia', 'Elegant creator edition', 'bootloader only', 'Cinematic and restrained. Still waiting on kernel reachability in VM.', false);
  editionCard(slide, ctx, 269, 388, 352, 170, COLORS.cyan, 'ARCWYRE', 'Recovery + technician environment', 'bootloader only', 'Operational tooling and recovery workflows, not a generic desktop clone.', false);
  editionCard(slide, ctx, 659, 388, 352, 170, COLORS.faint, 'Native', 'Research-only sovereign track', 'not shipping', 'Long-term platform research. It stays labeled research-only until it proves otherwise.', true);

  card(slide, ctx, 74, 590, 1132, 80, COLORS.panel2, COLORS.line, 'footer-card');
  textBox(slide, ctx, {
    x: 98,
    y: 614,
    width: 1040,
    height: 28,
    text: 'Retired concepts — Forge, Revival, Resilient — remain archived only and must never reappear in active build, registry, matrix, or release outputs.',
    size: 16,
    color: COLORS.muted,
    typeface: 'Roboto',
    name: 'archive-note',
  });

  return slide;
}
