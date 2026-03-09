// src/components/CameraStage.js
import React from 'react';
import { StyleSheet, View } from 'react-native';
import { CameraView } from 'expo-camera';
import { styles } from '../styles/appStyles';

export function CameraStage({
  cameraRef,
  facing,
  zoom,
  onLayout,
  children,
  flashMode,
}) {
  return (
    <View style={styles.cameraWrapper} onLayout={onLayout}>
      <CameraView
        key={facing}
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing={facing}
        zoom={zoom}
        enableTorch={flashMode}
      />
      {children}
    </View>
  );
}
