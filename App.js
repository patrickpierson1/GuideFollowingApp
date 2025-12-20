import 'react-native-gesture-handler';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Button, DevSettings, Text, View } from 'react-native';
import { useCameraPermissions } from 'expo-camera';
import {
  GestureHandlerRootView,
  Gesture,
  GestureDetector,
} from 'react-native-gesture-handler';

import { API_HOST, API_PORT, buildApiBase } from './src/config/api';
import { CameraStage } from './src/components/CameraStage';
import { DetectionOverlays } from './src/components/DetectionOverlays';
import { Controls } from './src/components/Controls';
import { SettingsModal } from './src/components/SettingsModal';
import { styles } from './src/styles/appStyles';
import { useHoldSelect } from './src/hooks/useHoldSelect';
import { clamp } from './src/utils/clamp';

export default function App() {
  // -------------------------
  // Hooks (never conditional)
  // -------------------------
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);

  const [facing, setFacing] = useState('back'); // 'front' | 'back'
  const [zoom, setZoom] = useState(0); // [0..1]
  const zoomRef = useRef(0);
  const [flashMode, setFlashMode] = useState(false); // false | true
  const [status, setStatus] = useState('Searching.');
  const [boxes, setBoxes] = useState([]);

  const [previewLayout, setPreviewLayout] = useState({ width: 0, height: 0 });

  // backend-processed dimensions (img_w/img_h)
  const [frameSize, setFrameSize] = useState({ w: 0, h: 0 });

  const [streaming, setStreaming] = useState(false);
  const intervalRef = useRef(null);
  const captureInProgress = useRef(false);
  const [modelSize, setModelSize] = useState('n'); // 'n' | 'm' | 'x'
  const [apiHost, setApiHost] = useState(API_HOST);
  const [showSettings, setShowSettings] = useState(false);
  const [showLabels, setShowLabels] = useState(false);

  const apiBase = useMemo(
    () => buildApiBase(apiHost.trim() || API_HOST, API_PORT),
    [apiHost]
  );

  // state machine
  const [mode, setMode] = useState('searching'); // 'searching' | 'following'
  const [selectedId, setSelectedId] = useState(null);

  const modeRef = useRef(mode);
  const selectedIdRef = useRef(selectedId);

  const [missingFrames, setMissingFrames] = useState(0);
  const MAX_MISSING_FRAMES = 12;

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);

  // request permission when permission object exists
  useEffect(() => {
    if (!permission) return;
    if (!permission.granted) requestPermission();
  }, [permission, requestPermission]);

  // start streaming once granted
  useEffect(() => {
    if (permission?.granted) {
      setStreaming(true);
      setMode('searching');
      setSelectedId(null);
      setMissingFrames(0);
      setStatus('Searching.');
    }
  }, [permission?.granted]);

  // lost target -> searching
  useEffect(() => {
    if (mode === 'following' && missingFrames > MAX_MISSING_FRAMES) {
      setMode('searching');
      setSelectedId(null);
      setMissingFrames(0);
      setStatus('Lost person — back to searching');
    }
  }, [missingFrames, mode]);

  // -------------------------
  // Hold-to-select hook
  // -------------------------
  const { startHoldSelect, cancelHoldSelect } = useHoldSelect({
    enabled: modeRef.current === 'searching',
    holdMs: 1000,
    onSelect: (id) => {
      setSelectedId(id);
      setMode('following');
      setMissingFrames(0);
      setStatus(`Following ID ${id}`);
    },
  });

  // -------------------------
  // Pinch (new Gesture API)
  // -------------------------
  const pinchStartZoomRef = useRef(0);

  const pinchGesture = Gesture.Pinch()
    .onBegin(() => {
      pinchStartZoomRef.current = zoomRef.current;
    })
    .onUpdate((e) => {
      const nextZoom = clamp(
        pinchStartZoomRef.current + (e.scale - 1) * 0.25,
        0,
        1
      );
      setZoom(nextZoom);
    });

  // -------------------------
  // Actions
  // -------------------------

  const toggleStreaming = () => {
    setStreaming((prev) => {
      const next = !prev;
      if (!next) {
        cancelHoldSelect();
        setMode('searching');
        setSelectedId(null);
        setMissingFrames(0);
        setStatus('Detection paused');
      } else {
        setStatus(
          modeRef.current === 'following'
            ? `Following ID ${selectedIdRef.current}`
            : 'Searching.'
        );
      }
      return next;
    });
  };

  const toggleFacing = () => {
    cancelHoldSelect();
    setFacing((prev) => (prev === 'front' ? 'back' : 'front'));
    setFlashMode(false);
    setMode('searching');
    setSelectedId(null);
    setMissingFrames(0);
    setStatus('Searching.');
  };

  const toggleFlash = () => {
    setFlashMode((prev) => (prev === false ? true : false));
  };

  const toggleSettings = () => {
    setShowSettings((prev) => !prev);
  };

  const clearBackendIds = async () => {
    try {
      const res = await fetch(`${apiBase}/reset-tracker`, { method: 'POST' });
      if (!res.ok) {
        const txt = await res.text();
        console.log('Clear tracker error:', txt);
        setStatus(`Backend error: ${res.status}`);
        return;
      }
      setStatus('Backend IDs cleared');
    } catch (err) {
      console.log('Clear tracker error:', err);
      setStatus(`Error: ${err.message}`);
    }
  };

  const stopFollowing = async () => {
    setMode('searching');
    setSelectedId(null);
    setMissingFrames(0);
    setStatus('Searching.');
    try {
      await clearBackendIds();
    } catch {
      // clearBackendIds already sets status on error
    }
  };
  
  const restartApp = () => {
    if (DevSettings && typeof DevSettings.reload === 'function') {
      DevSettings.reload();
    }
  };

  // -------------------------
  // Detect loop
  // -------------------------
  const captureAndDetect = async () => {
    if (!cameraRef.current) return;
    if (captureInProgress.current) return;
    if (!streaming) return;
    if (!permission?.granted) return;
    const REQUEST_TIMEOUT_MS = 4000;

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

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      const res = await fetch(`${apiBase}/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: photo.base64, model: modelSize }),
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId));

      if (!res.ok) {
        const text = await res.text();
        console.log('Backend error body:', text);
        setStatus(`Backend error: ${res.status}`);
        return;
      }

      const data = await res.json();
      const newBoxes = Array.isArray(data.boxes) ? data.boxes : [];
      setBoxes(newBoxes);

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
      if (err.name === 'AbortError') {
        setStatus('Network timeout; check IP');
      } else {
        setStatus(`Network error: ${err.message}`);
      }
    } finally {
      captureInProgress.current = false;
    }
  };

  useEffect(() => {
    const intervalMs = modelSize === 'm' ? 200 : modelSize === 'x' ? 500 : 50;

    if (!streaming || !permission?.granted) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      captureAndDetect();
    }, intervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [streaming, permission?.granted, modelSize, apiBase]);

  const isReadyToDraw =
    streaming &&
    permission?.granted &&
    previewLayout.width > 0 &&
    previewLayout.height > 0 &&
    frameSize.w > 0 &&
    frameSize.h > 0;

  // -------------------------
  // Render without early returns
  // -------------------------
  let content = null;

  if (!permission) {
    content = (
      <View style={styles.container}>
        <Text style={styles.text}>Loading camera.</Text>
      </View>
    );
  } else if (!permission.granted) {
    content = (
      <View style={styles.container}>
        <Text style={styles.text}>Camera access is needed to show the preview.</Text>
        <Button title="Grant permission" onPress={requestPermission} />
      </View>
    );
  } else {
    content = (
      <View style={styles.container}>
        <GestureDetector gesture={pinchGesture}>
          <View style={{ flex: 1 }}>
            <CameraStage
              cameraRef={cameraRef}
              facing={facing}
              zoom={zoom}
              onLayout={(e) => setPreviewLayout(e.nativeEvent.layout)}
              flashMode={flashMode}
            >
              <DetectionOverlays
                isReadyToDraw={isReadyToDraw}
                boxes={boxes}
                mode={mode}
                selectedId={selectedId}
                facing={facing}
                previewLayout={previewLayout}
                frameSize={frameSize}
                onPressInBox={startHoldSelect}
                onPressOutBox={cancelHoldSelect}
                showLabels={showLabels}
              />

              <Controls
                mode={mode}
                status={status}
                streaming={streaming}
                onToggleFacing={toggleFacing}
                onToggleFlash={toggleFlash}
                showFlash={facing === 'back'}
                flashMode={flashMode}
                onStopFollowing={stopFollowing}
                onToggleStreaming={toggleStreaming}
                onToggleSettings={toggleSettings}
              />
            </CameraStage>
          </View>
        </GestureDetector>
        <SettingsModal
          visible={showSettings}
          model={modelSize}
          onSelectModel={(m) => setModelSize(m)}
          apiHost={apiHost}
          onChangeApiHost={setApiHost}
          showLabels={showLabels}
          onToggleLabels={() => setShowLabels((prev) => !prev)}
          onClearIds={clearBackendIds}
          onRestartApp={restartApp}
          onClose={toggleSettings}
        />
      </View>
    );
  }

  return <GestureHandlerRootView style={{ flex: 1 }}>{content}</GestureHandlerRootView>;
}
