// src/components/Controls.js
import React from 'react';
import { Image, Text, TouchableOpacity } from 'react-native';
import { styles } from '../styles/appStyles';

export function Controls({
  mode,
  status,
  streaming,
  onToggleFacing,
  onStopFollowing,
  onToggleStreaming,
  onToggleSettings,
  onToggleFlash,
  showFlash = false,
  flashMode = 'off',
}) {
  const flashIcon =
    flashMode === true
      ? require('../../assets/icons8-flash-on-50.png')
      : require('../../assets/icons8-flash-off-50.png');

  return (
    <>
      {/* camera switch button */}
      <TouchableOpacity style={styles.switchButton} onPress={onToggleFacing}>
        <Image
          source={require('../../assets/icons8-flip-50.png')}
          style={styles.switchIcon}
        />
      </TouchableOpacity>

      {/* flash button */}
      {showFlash && (
        <TouchableOpacity style={styles.flashButton} onPress={onToggleFlash}>
          <Image source={flashIcon} style={styles.flashIcon} />
        </TouchableOpacity>
      )}

      {/* settings button (no-op like before) */}
      <TouchableOpacity style={styles.settingsButton} onPress={onToggleSettings}>
        <Image
          source={require('../../assets/icons8-setting-50.png')}
          style={styles.settingsIcon}
        />
      </TouchableOpacity>

      {/* Stop Following */}
      {mode === 'following' && (
        <TouchableOpacity style={styles.stopFollow} onPress={onStopFollowing}>
          <Text style={styles.detectText}>Stop Following</Text>
        </TouchableOpacity>
      )}

      {/* Start/Stop Detection */}
      <TouchableOpacity style={styles.startDetect} onPress={onToggleStreaming}>
        <Text style={styles.text}>{status}</Text>
        <Text style={styles.detectText}>
          {streaming ? 'Stop Detection' : 'Start Detection'}
        </Text>
      </TouchableOpacity>
    </>
  );
}
