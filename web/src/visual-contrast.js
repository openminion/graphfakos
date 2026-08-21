const colorsByKind = {
  artifact: "#ffa47d",
  cluster: "#8fdaff",
  document: "#ffe08a",
  memory: "#b0ee78",
  provider: "#6fe8ee",
  warning: "#ff7c8b",
};

export function nodeColorForKind(kind) {
  return colorsByKind[kind] || "#a8c5f2";
}

function relativeLuminance(color) {
  const channels = color.match(/[0-9a-f]{2}/gi).map((value) => Number.parseInt(value, 16) / 255);
  const [red, green, blue] = channels.map((value) => (
    value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  ));
  return red * 0.2126 + green * 0.7152 + blue * 0.0722;
}

export function contrastRatio(foreground, background) {
  const brighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (brighter + 0.05) / (darker + 0.05);
}
