// src/styles/appStyles.js
import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },

  cameraWrapper: {
    flex: 1,
    overflow: 'hidden',
  },

  text: {
    color: '#fff',
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

  flashButton: {
    position: 'absolute',
    bottom: 96,
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
    height: 56,
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
    backgroundColor: 'rgba(56, 135, 201, 0.48)',
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

  flashIcon: {
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

  settingsBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.65)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },

  settingsCard: {
    width: '90%',
    maxWidth: 420,
    backgroundColor: '#0c1424',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },

  settingsTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },

  settingsLabel: {
    color: '#cbd5e1',
    fontSize: 14,
    marginTop: 8,
    marginBottom: 6,
  },

  modelOption: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
    backgroundColor: 'rgba(255,255,255,0.04)',
    marginBottom: 8,
  },

  modelOptionActive: {
    borderColor: '#4da3ff',
    backgroundColor: 'rgba(77, 163, 255, 0.12)',
  },

  modelOptionText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },

  modelOptionSub: {
    color: '#90a4ae',
    fontSize: 12,
    marginTop: 2,
  },

  input: {
    height: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
    paddingHorizontal: 12,
    color: '#fff',
    backgroundColor: 'rgba(255,255,255,0.05)',
  },

  actionButton: {
    marginTop: 12,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'rgba(77, 163, 255, 0.35)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  closeButton: {
    marginTop: 14,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'rgba(77, 163, 255, 0.35)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
