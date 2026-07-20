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
