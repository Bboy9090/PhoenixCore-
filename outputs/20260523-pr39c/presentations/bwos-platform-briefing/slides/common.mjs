export const COLORS = {
  bg: '#071321',
  panel: '#0D1A2B',
  panel2: '#10243A',
  panel3: '#132B45',
  line: '#21374F',
  text: '#F4F7FB',
  muted: '#9DA9B7',
  faint: '#627185',
  blue: '#63A4FF',
  cyan: '#39D5E8',
  gold: '#D7A45C',
  purple: '#8A73FF',
  green: '#48C58E',
  red: '#E26F7A',
  white: '#FFFFFF',
};

export function paintBackground(slide, ctx, color = COLORS.bg) {
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: ctx.W,
    height: ctx.H,
    fill: color,
    line: ctx.line(color, 0),
    name: 'background',
  });
}

export function card(slide, ctx, x, y, width, height, fill = COLORS.panel, line = COLORS.line, name = 'card') {
  return ctx.addShape(slide, {
    x,
    y,
    width,
    height,
    fill,
    line: ctx.line(line, 1),
    name,
  });
}

export function bar(slide, ctx, x, y, width, height, fill, name = 'bar') {
  return ctx.addShape(slide, {
    x,
    y,
    width,
    height,
    fill,
    line: ctx.line(fill, 0),
    name,
  });
}

export function dot(slide, ctx, x, y, size, fill, name = 'dot') {
  return ctx.addShape(slide, {
    geometry: 'ellipse',
    x,
    y,
    width: size,
    height: size,
    fill,
    line: ctx.line(fill, 0),
    name,
  });
}

export function textBox(slide, ctx, { x, y, width, height, text, size = 24, color = COLORS.text, bold = false, typeface = 'Roboto', align = 'left', valign = 'top', fill = '#00000000', line = '#00000000', insets = { left: 0, right: 0, top: 0, bottom: 0 }, name }) {
  return ctx.addText(slide, {
    x,
    y,
    width,
    height,
    text,
    fontSize: size,
    color,
    bold,
    typeface,
    align,
    valign,
    fill,
    line: ctx.line(line, 0),
    insets,
    name,
  });
}

export function kicker(slide, ctx, x, y, text, color = COLORS.blue) {
  return textBox(slide, ctx, {
    x,
    y,
    width: 520,
    height: 24,
    text: text.toUpperCase(),
    size: 13,
    color,
    bold: true,
    typeface: 'Roboto Mono',
    name: 'kicker',
  });
}

export function titleBlock(slide, ctx, x, y, width, title, subtitle) {
  textBox(slide, ctx, {
    x,
    y,
    width,
    height: 110,
    text: title,
    size: 40,
    color: COLORS.text,
    bold: true,
    typeface: 'Montserrat',
    name: 'title',
  });
  if (subtitle) {
    textBox(slide, ctx, {
      x,
      y: y + 92,
      width,
      height: 84,
      text: subtitle,
      size: 18,
      color: COLORS.muted,
      typeface: 'Roboto',
      name: 'subtitle',
    });
  }
}

export function pill(slide, ctx, x, y, width, text, fill, color = COLORS.white, border = fill) {
  card(slide, ctx, x, y, width, 32, fill, border, 'pill');
  textBox(slide, ctx, {
    x: x + 10,
    y: y + 4,
    width: width - 20,
    height: 24,
    text,
    size: 14,
    color,
    bold: true,
    typeface: 'Roboto Mono',
    align: 'center',
    valign: 'middle',
    name: 'pill-text',
  });
}

export function cardHeader(slide, ctx, x, y, width, label, accent = COLORS.blue) {
  bar(slide, ctx, x, y, width, 5, accent, 'card-accent');
  textBox(slide, ctx, {
    x: x + 16,
    y: y + 14,
    width: width - 32,
    height: 22,
    text: label.toUpperCase(),
    size: 12,
    color: accent,
    bold: true,
    typeface: 'Roboto Mono',
    name: 'card-label',
  });
}

export function bulletLine(slide, ctx, x, y, label, value, color = COLORS.text) {
  dot(slide, ctx, x, y + 7, 8, color, 'bullet');
  textBox(slide, ctx, {
    x: x + 16,
    y,
    width: 460,
    height: 24,
    text: `${label}: ${value}`,
    size: 16,
    color,
    typeface: 'Roboto',
    name: 'bullet-line',
  });
}

export function smallCaps(slide, ctx, x, y, text, color = COLORS.muted) {
  return textBox(slide, ctx, {
    x,
    y,
    width: 400,
    height: 20,
    text: text.toUpperCase(),
    size: 12,
    color,
    bold: true,
    typeface: 'Roboto Mono',
    name: 'small-caps',
  });
}
