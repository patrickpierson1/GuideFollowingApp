import { useEffect, useRef, useState } from 'react';
import {
  Button,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

// Replace with your machine's IP if needed.
const API_BASE = 'http://10.0.0.145:8000';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);

  const [facing, setFacing] = useState('front');
  const [zoom, setZoom] = useState(0);
  const [status, setStatus] = useState('');

  // detection boxes from backend
  const [boxes, setBoxes] = useState([]);
  // dimensions of the camera preview for scaling boxes
  const [previewLayout, setPreviewLayout] = useState({
    width: 0,
    height: 0,
  });

  // continuous detection control
  const [streaming, setStreaming] = useState(false);
  const intervalRef = useRef(null);
  const captureInProgress = useRef(false);

  // ask for permission once
  useEffect(() => {
    if (!permission) return;
    if (!permission.granted) {
      requestPermission();
    }
  }, [permission]);

  // start detection automatically once permission is granted
  useEffect(() => {
    if (permission?.granted) {
      setStreaming(true);
    }
  }, [permission?.granted]);

  // main loop: run capture+detect every N ms when streaming
  useEffect(() => {
    if (!streaming) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setStatus('Detection paused');
      return;
    }

    setStatus('Detecting people...');
    intervalRef.current = setInterval(() => {
      captureAndDetect();
    }, 500); // 0.5s between frames

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [streaming]);

  if (!permission) {
    return (
      <View style={styles.container}>
        <Text style={styles.text}>Loading camera...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.text}>
          Camera access is needed to show the preview.
        </Text>
        <Button title="Grant permission" onPress={requestPermission} />
      </View>
    );
  }

  const captureAndDetect = async () => {
    if (!cameraRef.current) return;
    if (captureInProgress.current) return; // avoid overlapping calls
    if (!streaming) return;

    try {
      captureInProgress.current = true;

      const photo = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 1,
        skipProcessing: true,
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

      setBoxes(Array.isArray(data.boxes) ? data.boxes : []);
      setStatus(`People detected: ${data.count || 0}`);
    } catch (err) {
      console.log('Detect error:', err);
      setStatus(`Error: ${err.message}`);
    } finally {
      captureInProgress.current = false;
    }
  };

  const toggleStreaming = () => {
    setStreaming((prev) => !prev);
  };

  const toggleFacing = () => {
    setFacing((prev) => (prev === 'front' ? 'back' : 'front'));
  };

  return (
    <View style={styles.container}>
      {/* Camera area with overlays */}
      <View
        style={styles.cameraWrapper}
        onLayout={(e) => setPreviewLayout(e.nativeEvent.layout)}
      >
        <CameraView
          key={facing} // force remount when switching cameras
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          facing={facing}
          zoom={zoom}
        />

        {/* Draw detection boxes + confidence labels over the camera preview */}
        {streaming &&
          previewLayout.width > 0 &&
          previewLayout.height > 0 &&
          boxes.map((b, idx) => {
            const left = b.x1 * previewLayout.width;
            const top = b.y1 * previewLayout.height;
            const width = (b.x2 - b.x1) * previewLayout.width;
            const height = (b.y2 - b.y1) * previewLayout.height;
            const conf = typeof b.conf === 'number' ? b.conf : null;

            return (
              <View key={idx}>
                {conf !== null && (
                  <Text
                    style={[
                      styles.confidenceText,
                      {
                        left,
                        top: Math.max(top - 20, 0), // above box, but not off-screen
                      },
                    ]}
                  >
                    {(conf * 100).toFixed(1)}%
                  </Text>
                )}

                <View
                  style={[
                    styles.box,
                    {
                      left,
                      top,
                      width,
                      height,
                    },
                  ]}
                />
              </View>
            );
          })}

        {/* Floating round camera switch button in bottom-right */}
        <TouchableOpacity style={styles.switchButton} onPress={toggleFacing}>
          <Image
            source={require('./assets/icons8-flip-50.png')}
            style={styles.switchIcon}
          />
        </TouchableOpacity>  

        {/* Floating round camera switch button in bottom-right */}
        <TouchableOpacity style={styles.settingsButton} >
          <Image
            source={require('./assets/icons8-setting-50.png')}
            style={styles.settingsIcon}
          />
        </TouchableOpacity>

        {/* Bottom-center controls for detection + status */}
        <TouchableOpacity style={styles.startDetect} onPress={toggleStreaming}>
          <Text style={styles.text}>{status}</Text>
          <Text style={styles.detectText}>
            {streaming ? 'Stop Detection' : 'Start Detection'}
          </Text>
        </TouchableOpacity>
      </View>      
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },

  cameraWrapper: {
    flex: 1,
    overflow: 'hidden',
  },

  controls: {
    position: 'absolute',
    bottom: 40,
    alignSelf: 'center',
    alignItems: 'center',
    gap: 8,
  },

  text: {
    color: '#ffffffff',
    textAlign: 'center',
    alignSelf: 'center',
  },

  // Floating round settings button
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

  // Floating round camera-switch button
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

  // Floating round start / stop detection button
  startDetect: {
    position: 'absolute',
    bottom: 24,
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

  settingsIcon: {
    width: 28,
    height: 28,
    tintColor: '#fff',
  },

  box: {
    position: 'absolute',
    borderWidth: 3,
    borderColor: '#00ff00',
    borderRadius: 4,
  },

  confidenceText: {
    position: 'absolute',
    color: '#00ff00',
    fontSize: 14,
    fontWeight: 'bold',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
});
