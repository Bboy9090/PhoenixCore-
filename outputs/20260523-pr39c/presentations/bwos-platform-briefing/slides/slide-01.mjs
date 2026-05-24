import { COLORS, paintBackground, card, textBox, kicker, titleBlock, pill, cardHeader, bulletLine, smallCaps } from './common.mjs';

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  paintBackground(slide, ctx, COLORS.bg);
  card(slide, ctx, 48, 42, 1184, 636, COLORS.panel, COLORS.line, 'outer-frame');

  kicker(slide, ctx, 74, 58, 'BWOS / Blue Phoenix OS');
  titleBlock(
    slide,
    ctx,
    74,
    82,
    710,
    'Five editions. One platform.',
    'Home is the only active edition with a visually confirmed desktop. The rest stay blocked until their own boot evidence exists.'
  );

  card(slide, ctx, 824, 58, 360, 284, COLORS.panel2, COLORS.line, 'truth-card');
  cardHeader(slide, ctx, 824, 58, 360, 'Current truth', COLORS.blue);
  bulletLine(slide, ctx, 846, 108, 'Home', 'BOOT_PASS_DESKTOP / desktop confirmed', COLORS.green);
  bulletLine(slide, ctx, 846, 148, 'Thunder God', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold);
  bulletLine(slide, ctx, 846, 188, 'Aurelia', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold);
  bulletLine(slide, ctx, 846, 228, 'ARCWYRE', 'BOOT_PASS_BOOTLOADER_ONLY', COLORS.gold);
  bulletLine(slide, ctx, 846, 268, 'Native', 'research-only / not boot-matrix tracked', COLORS.muted);

  card(slide, ctx, 74, 288, 1144, 316, COLORS.panel2, COLORS.line, 'status-card');
  cardHeader(slide, ctx, 74, 288, 1144, 'Release posture and source of truth', COLORS.gold);
  smallCaps(slide, ctx, 98, 342, 'Observed state');
  textBox(slide, ctx, {
    x: 98,
    y: 368,
    width: 510,
    height: 110,
    text: 'Home has reached the live Plasma desktop in QEMU x86_64 UEFI.\nKernel, initramfs, and display manager are all observed. Clean shutdown is still unverified.',
    size: 20,
    color: COLORS.text,
    typeface: 'Roboto',
    name: 'observed-state',
  });
  smallCaps(slide, ctx, 678, 342, 'Next gates');
  textBox(slide, ctx, {
    x: 678,
    y: 368,
    width: 480,
    height: 128,
    text: '1. Verify clean shutdown on Home.\n2. Build Thunder God for arm64.\n3. Move PR40 app launch validation into the active matrix.\n4. Keep PR41 blocked until telemetry, boot, and app evidence agree.',
    size: 18,
    color: COLORS.text,
    typeface: 'Roboto',
    name: 'next-gates',
  });
  pill(slide, ctx, 98, 500, 154, 'release_blocked', COLORS.red, COLORS.white);
  pill(slide, ctx, 266, 500, 162, 'desktop_passed', COLORS.green, COLORS.white);
  pill(slide, ctx, 442, 500, 148, 'shutdown_pending', COLORS.panel3, COLORS.text);
  pill(slide, ctx, 604, 500, 152, 'telemetry_recorded', COLORS.blue, COLORS.white);
  pill(slide, ctx, 770, 500, 162, 'retired archived', COLORS.panel3, COLORS.muted, COLORS.line);
  textBox(slide, ctx, {
    x: 98,
    y: 556,
    width: 1020,
    height: 30,
    text: 'Source of truth: iso/BOOT_MATRIX.md • iso/ARTIFACTS.md • iso/outputs/manifest.json • iso/outputs/vm-boot-matrix.json',
    size: 14,
    color: COLORS.muted,
    typeface: 'Roboto Mono',
    name: 'footer-source',
  });

  return slide;
}
