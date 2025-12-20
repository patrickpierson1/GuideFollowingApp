// src/styles/appStyles.js
import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },

  cameraWrapper: {
    flex: 1,
    overflow: 'hidden',
  },

  text: {
    color: '#ffffffff',
    textAlign: 'center',
    alignSelf: 'center',
  },

  settingsButton: {
    position: 'absolute',
    bottom: 24,
    left: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(56, 135, 201, 0.48)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  switchButton: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(56, 135, 201, 0.48)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  startDetect: {
    position: 'absolute',
    bottom: 24,
    alignSelf: 'center',
    width: 200,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'rgba(56, 135, 201, 0.48)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },

  stopFollow: {
    position: 'absolute',
    bottom: 104,
    alignSelf: 'center',
    width: 200,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(77, 163, 255, 0.35)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  detectText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },

  switchIcon: {
    width: 28,
    height: 28,
    tintColor: '#fff',
  },

  settingsIcon: {
    width: 28,
    height: 28,
    tintColor: '#fff',
  },

  box: {
    position: 'absolute',
    borderWidth: 3,
    borderRadius: 4,
  },

  confidenceText: {
    position: 'absolute',
    fontSize: 14,
    fontWeight: 'bold',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
});
