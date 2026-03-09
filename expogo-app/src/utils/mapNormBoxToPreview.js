// src/utils/mapNormBoxToPreview.js

// Map normalized box [0..1] from processed image space to preview space,
// accounting for "cover" scaling + center-crop.
export function mapNormBoxToPreview(b, previewW, previewH, imgW, imgH) {
  if (!previewW || !previewH || !imgW || !imgH) {
    return { left: 0, top: 0, width: 0, height: 0 };
  }

  // "cover" scale
  const scale = Math.max(previewW / imgW, previewH / imgH);
  const dispW = imgW * scale;
  const dispH = imgH * scale;

  const offX = (previewW - dispW) / 2;
  const offY = (previewH - dispH) / 2;

  const left = b.x1 * dispW + offX;
  const top = b.y1 * dispH + offY;
  const width = (b.x2 - b.x1) * dispW;
  const height = (b.y2 - b.y1) * dispH;

  return { left, top, width, height };
}
