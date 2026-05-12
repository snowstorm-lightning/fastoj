import {
  layoutWithLines,
  measureLineStats,
  measureNaturalWidth,
  prepareWithSegments,
} from "@chenglou/pretext";

export type TextLayoutResult = {
  width: number;
  height: number;
  lineCount: number;
  lines: string[];
  usedFallback: boolean;
};

export function measureTrainingText(
  text: string,
  maxWidth = 220,
  font = "14px Inter, system-ui, sans-serif",
  lineHeight = 20,
): TextLayoutResult {
  try {
    const prepared = prepareWithSegments(text, font, { whiteSpace: "normal" });
    const naturalWidth = measureNaturalWidth(prepared);
    const stats = measureLineStats(prepared, maxWidth);
    const result = layoutWithLines(prepared, maxWidth, lineHeight);
    return {
      width: Math.ceil(Math.min(maxWidth, Math.max(80, stats.maxLineWidth || naturalWidth))),
      height: Math.ceil(result.height),
      lineCount: result.lineCount,
      lines: result.lines.map((line) => line.text),
      usedFallback: false,
    };
  } catch {
    const approxLines = Math.max(1, Math.ceil(text.length / 28));
    return {
      width: Math.min(maxWidth, Math.max(80, text.length * 7)),
      height: approxLines * lineHeight,
      lineCount: approxLines,
      lines: text.match(/.{1,28}/g) ?? [text],
      usedFallback: true,
    };
  }
}
