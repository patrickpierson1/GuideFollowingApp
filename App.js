import 'react-native-gesture-handler';

import { useEffect, useRef, useState } from 'react';
import {
  Button,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import {
  GestureHandlerRootView,
  PinchGestureHandler,
  State,
} from 'react-native-gesture-handler';

// Replace with your backend IP
const API_BASE = 'http://192.168.68.62:8000';

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// Map normalized box [0..1] from processed image space to preview space,
// accounting for "cover" scaling + center-crop.
function mapNormBoxToPreview(b, previewW, previewH, imgW, imgH) {
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

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);

  const [facing, setFacing] = useState('front'); // 'front' | 'back'
  const [zoom, setZoom] = useState(0); // [0..1]
  const zoomRef = useRef(0);

  const [status, setStatus] = useState('Searching...');
  const [boxes, setBoxes] = useState([]);

  const [previewLayout, setPreviewLayout] = useState({ width: 0, height: 0 });

  // IMPORTANT: comes from backend (img_w/img_h), not photo.width/height
  const [frameSize, setFrameSize] = useState({ w: 0, h: 0 });

  const [streaming, setStreaming] = useState(false);
  const intervalRef = useRef(null);
  const captureInProgress = useRef(false);

  // -------------------------
  // State machine: searching / following
  // -------------------------
  const [mode, setMode] = useState('searching'); // 'searching' | 'following'
  const [selectedId, setSelectedId] = useState(null);

  const modeRef = useRef(mode);
  const selectedIdRef = useRef(selectedId);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);
  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  // press-and-hold selection (1s)
  const holdTimerRef = useRef(null);
  const holdTargetIdRef = useRef(null);

  // follow-loss handling
  const [missingFrames, setMissingFrames] = useState(0);
  const MAX_MISSING_FRAMES = 12;

  // pinch zoom
  const pinchStartZoomRef = useRef(0);

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  // Request permission once
  useEffect(() => {
    if (!permission) return;
    if (!permission.granted) requestPermission();
  }, [permission]);

  // Auto-start streaming after permission
  useEffect(() => {
    if (permission?.granted) {
      setStreaming(true);
      setMode('searching');
      setSelectedId(null);
      setMissingFrames(0);
      setStatus('Searching...');
    }
  }, [permission?.granted]);

  // main detection loop
  useEffect(() => {
    if (!streaming) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setStatus('Detection paused');
      return;
    }

    intervalRef.current = setInterval(() => {
      captureAndDetect();
    }, 100);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streaming]);

  // back to searching if target is lost too long
  useEffect(() => {
    if (mode === 'following' && missingFrames > MAX_MISSING_FRAMES) {
      setMode('searching');
      setSelectedId(null);
      setMissingFrames(0);
      setStatus('Lost person — back to searching');
    }
  }, [missingFrames, mode]);

  // cleanup any hold timer
  useEffect(() => {
    return () => {
      if (holdTimerRef.current) {
        clearTimeout(holdTimerRef.current);
        holdTimerRef.current = null;
      }
    };
  }, []);

  if (!permission) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={styles.container}>
          <Text style={styles.text}>Loading camera...</Text>
        </View>
      </GestureHandlerRootView>
    );
  }

  if (!permission.granted) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={styles.container}>
          <Text style={styles.text}>Camera access is needed to show the preview.</Text>
          <Button title="Grant permission" onPress={requestPermission} />
        </View>
      </GestureHandlerRootView>
    );
  }

  const startHoldSelect = (id) => {
    if (modeRef.current !== 'searching') return;
    if (id == null) return;

    holdTargetIdRef.current = id;

    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }

    holdTimerRef.current = setTimeout(() => {
      if (holdTargetIdRef.current === id) {
        setSelectedId(id);
        setMode('following');
        setMissingFrames(0);
        setStatus(`Following ID ${id}`);
      }
    }, 1000);
  };

  const cancelHoldSelect = () => {
    holdTargetIdRef.current = null;
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  };

  const stopFollowing = () => {
    setMode('searching');
    setSelectedId(null);
    setMissingFrames(0);
    setStatus('Searching...');
  };

  const toggleStreaming = () => {
    setStreaming((prev) => {
      const next = !prev;
      if (!next) {
        cancelHoldSelect();
        setMode('searching');
        setSelectedId(null);
        setMissingFrames(0);
      } else {
        setStatus(
          modeRef.current === 'following'
            ? `Following ID ${selectedIdRef.current}`
            : 'Searching...'
        );
      }
      return next;
    });
  };

  const toggleFacing = () => {
    cancelHoldSelect();
    setFacing((prev) => (prev === 'front' ? 'back' : 'front'));
    setMode('searching');
    setSelectedId(null);
    setMissingFrames(0);
    setStatus('Searching...');
  };

  // Pinch handler
  const onPinchStateChange = (e) => {
    const st = e.nativeEvent.state;
    if (st === State.BEGAN) {
      pinchStartZoomRef.current = zoomRef.current;
    }
    if (st === State.END || st === State.CANCELLED || st === State.FAILED) {
      // nothing needed
    }
  };

  const onPinchGestureEvent = (e) => {
    const scale = e.nativeEvent.scale; // ~1 at rest
    const nextZoom = clamp(pinchStartZoomRef.current + (scale - 1) * 0.25, 0, 1);
    setZoom(nextZoom);
  };

  const captureAndDetect = async () => {
    if (!cameraRef.current) return;
    if (captureInProgress.current) return;
    if (!streaming) return;

    try {
      captureInProgress.current = true;

      const photo = await cameraRef.current.takePictureAsync({
        base64: true,
        exif: true,
        quality: 1,
        skipProcessing: false,
      });

      if (!photo?.base64) {
        setStatus('No image data captured');
        return;
      }

      const res = await fetch(`${API_BASE}/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: photo.base64 }),
      });

      if (!res.ok) {
        const text = await res.text();
        console.log('Backend error body:', text);
        setStatus(`Backend error: ${res.status}`);
        return;
      }

      const data = await res.json();
      const newBoxes = Array.isArray(data.boxes) ? data.boxes : [];
      setBoxes(newBoxes);

      // Use backend-processed dimensions (fixes landscape offsets)
      if (data.img_w && data.img_h) {
        setFrameSize({ w: data.img_w, h: data.img_h });
      }

      if (modeRef.current === 'following' && selectedIdRef.current != null) {
        const sid = selectedIdRef.current;
        const stillThere = newBoxes.some((b) => b?.id === sid);
        setMissingFrames((m) => (stillThere ? 0 : m + 1));
        setStatus(stillThere ? `Following ID ${sid}` : `Following ID ${sid} (lost)`);
      } else {
        setMissingFrames(0);
        setStatus(`People detected: ${data.count || 0}`);
      }
    } catch (err) {
      console.log('Detect error:', err);
      setStatus(`Error: ${err.message}`);
    } finally {
      captureInProgress.current = false;
    }
  };

  const isReadyToDraw =
    streaming &&
    previewLayout.width > 0 &&
    previewLayout.height > 0 &&
    frameSize.w > 0 &&
    frameSize.h > 0;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <View style={styles.container}>
        <PinchGestureHandler
          onGestureEvent={onPinchGestureEvent}
          onHandlerStateChange={onPinchStateChange}
        >
          <View
            style={styles.cameraWrapper}
            onLayout={(e) => setPreviewLayout(e.nativeEvent.layout)}
          >
            <CameraView
              key={facing}
              ref={cameraRef}
              style={StyleSheet.absoluteFill}
              facing={facing}
              zoom={zoom}
            />

            {/* Draw boxes */}
            {isReadyToDraw &&
              boxes
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
                      {conf !== null && (
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
                          onPressIn={() => startHoldSelect(b?.id)}
                          onPressOut={cancelHoldSelect}
                          style={[
                            styles.box,
                            { left, top, width, height, borderColor },
                          ]}
                        />
                      ) : (
                        <View style={[styles.box, { left, top, width, height, borderColor }]} />
                      )}
                    </View>
                  );
                })}

            {/* camera switch button */}
            <TouchableOpacity style={styles.switchButton} onPress={toggleFacing}>
              <Image
                source={require('./assets/icons8-flip-50.png')}
                style={styles.switchIcon}
              />
            </TouchableOpacity>

            {/* settings button */}
            <TouchableOpacity style={styles.settingsButton}>
              <Image
                source={require('./assets/icons8-setting-50.png')}
                style={styles.settingsIcon}
              />
            </TouchableOpacity>

            {/* Stop Following */}
            {mode === 'following' && (
              <TouchableOpacity style={styles.stopFollow} onPress={stopFollowing}>
                <Text style={styles.detectText}>Stop Following</Text>
              </TouchableOpacity>
            )}

            {/* Start/Stop Detection */}
            <TouchableOpacity style={styles.startDetect} onPress={toggleStreaming}>
              <Text style={styles.text}>{status}</Text>
              <Text style={styles.detectText}>
                {streaming ? 'Stop Detection' : 'Start Detection'}
              </Text>
            </TouchableOpacity>
          </View>
        </PinchGestureHandler>
      </View>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
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
