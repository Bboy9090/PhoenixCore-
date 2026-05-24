import { COLORS, paintBackground, card, textBox, kicker, titleBlock, cardHeader, pill, bar, dot } from './common.mjs';

const SCREEN = '/Users/bj90-m1/PhoenixCore-/iso/outputs/vm-boot-evidence/home/20260523T150945Z/desktop.png';

function matrixRow(slide, ctx, x, y, edition, status, color, detail) {
  dot(slide, ctx, x, y + 8, 8, color, `${edition}-dot`);
  textBox(slide, ctx, {
    x: x + 16,
    y,
    width: 160,
    height: 22,
    text: edition,
    size: 16,
    color: COLORS.text,
    bold: true,
    typeface: 'Roboto',
  });
  pill(slide, ctx, x + 174, y - 2, 186, status, color, COLORS.white, color);
  textBox(slide, ctx, {
    x: x + 372,
    y,
    width: 200,
    height: 40,
    text: detail,
    size: 13,
    color: COLORS.muted,
    typeface: 'Roboto',
  });
}

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  paintBackground(slide, ctx, COLORS.bg);
  kicker(slide, ctx, 74, 56, 'VM boot validation');
  titleBlock(slide, ctx, 74, 80, 980, 'Home reaches the desktop; the blocker is clean shutdown.', 'The desktop was visually confirmed in QEMU x86_64 UEFI. The other active editions still stop at bootloader-only states.');

  card(slide, ctx, 74, 190, 598, 448, COLORS.panel2, COLORS.line, 'screenshot-card');
  cardHeader(slide, ctx, 74, 190, 598, 'Observed evidence', COLORS.blue);
  card(slide, ctx, 96, 240, 554, 320, '#08101A', COLORS.line, 'screenshot-frame');
  ctx.addImage(slide, {
    path: SCREEN,
    x: 108,
    y: 252,
    width: 530,
    height: 296,
    fit: 'cover',
    alt: 'Home desktop evidence screenshot',
    name: 'desktop-screenshot',
  });
  textBox(slide, ctx, {
    x: 110,
    y: 556,
    width: 530,
    height: 28,
    text: 'Evidence: desktop.png / serial.log / console.log',
    size: 14,
    color: COLORS.muted,
    typeface: 'Roboto Mono',
    name: 'evidence-note',
  });

  card(slide, ctx, 696, 190, 510, 448, COLORS.panel2, COLORS.line, 'matrix-card');
  cardHeader(slide, ctx, 696, 190, 510, 'Active edition boot matrix', COLORS.gold);
  matrixRow(slide, ctx, 720, 246, 'Home', 'BOOT_PASS_DESKTOP', COLORS.green, 'menu, kernel, initramfs, display manager, desktop all reached');
  bar(slide, ctx, 720, 292, 462, 1, COLORS.line, 'row-divider-1');
  matrixRow(slide, ctx, 720, 310, 'Thunder God', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold, 'GRUB reached; kernel not observed');
  bar(slide, ctx, 720, 356, 462, 1, COLORS.line, 'row-divider-2');
  matrixRow(slide, ctx, 720, 374, 'Aurelia', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold, 'GRUB reached; kernel not observed');
  bar(slide, ctx, 720, 420, 462, 1, COLORS.line, 'row-divider-3');
  matrixRow(slide, ctx, 720, 438, 'ARCWYRE', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold, 'GRUB reached; kernel not observed');
  bar(slide, ctx, 720, 484, 462, 1, COLORS.line, 'row-divider-4');
  matrixRow(slide, ctx, 720, 502, 'Native', 'NOT_TESTED', COLORS.faint, 'research-only; no VM target yet');

  card(slide, ctx, 74, 650 - 46, 1132, 46, COLORS.panel3, COLORS.line, 'footer-callout');
  textBox(slide, ctx, {
    x: 98,
    y: 662 - 46,
    width: 1084,
    height: 28,
    text: 'Current classification: BOOT_PASS_DESKTOP. failure_point: shutdown. clean_shutdown_verified: false.',
    size: 16,
    color: COLORS.text,
    bold: true,
    typeface: 'Roboto Mono',
    name: 'classification',
  });

  return slide;
}
