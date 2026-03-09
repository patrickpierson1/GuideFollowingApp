// src/components/DetectionOverlays.js
import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { mapNormBoxToPreview } from '../utils/mapNormBoxToPreview';
import { styles } from '../styles/appStyles';

export function DetectionOverlays({
  isReadyToDraw,
  boxes,
  mode,
  selectedId,
  facing,
  previewLayout,
  frameSize,
  onPressInBox,
  onPressOutBox,
  showLabels = false,
}) {
  if (!isReadyToDraw) return null;

  return (
    <>
      {boxes
        .filter((b) =>
          mode === 'following' && selectedId != null ? b?.id === selectedId : true
        )
        .map((rawB, idx) => {
          if (!rawB) return null;

          // Optional mirror for front preview
          let b = rawB;
          if (facing === 'front') {
            b = {
              ...rawB,
              x1: 1 - rawB.x2,
              x2: 1 - rawB.x1,
            };
          }

          const { left, top, width, height } = mapNormBoxToPreview(
            b,
            previewLayout.width,
            previewLayout.height,
            frameSize.w,
            frameSize.h
          );

          const conf = typeof b.conf === 'number' ? b.conf : null;
          const isSelected = mode === 'following' && b?.id === selectedId;

          const borderColor = isSelected ? '#4da3ff' : '#00ff00';
          const labelColor = isSelected ? '#4da3ff' : '#00ff00';

          const key = b?.id ?? idx;

          return (
            <View key={key}>
              {showLabels && conf !== null && (
                <Text
                  style={[
                    styles.confidenceText,
                    {
                      left: Math.max(left, 0),
                      top: Math.max(top - 20, 0),
                      color: labelColor,
                    },
                  ]}
                >
                  {`ID ${b?.id ?? '?'}  ${(conf * 100).toFixed(1)}%`}
                </Text>
              )}

              {mode === 'searching' ? (
                <Pressable
                  onPressIn={() => onPressInBox?.(b?.id)}
                  onPressOut={onPressOutBox}
                  style={[styles.box, { left, top, width, height, borderColor }]}
                />
              ) : (
                <View style={[styles.box, { left, top, width, height, borderColor }]} />
              )}
            </View>
          );
        })}
    </>
  );
}
