// src/hooks/usePinchZoom.js
import { useRef } from 'react';
import { State } from 'react-native-gesture-handler';
import { clamp } from '../utils/clamp';

export function usePinchZoom({ zoom, setZoom, zoomRef }) {
  const pinchStartZoomRef = useRef(0);

  const onPinchStateChange = (e) => {
    const st = e.nativeEvent.state;
    if (st === State.BEGAN) {
      pinchStartZoomRef.current = zoomRef.current;
    }
  };

  const onPinchGestureEvent = (e) => {
    const scale = e.nativeEvent.scale; // ~1 at rest
    const nextZoom = clamp(pinchStartZoomRef.current + (scale - 1) * 0.25, 0, 1);
    setZoom(nextZoom);
  };

  return { onPinchGestureEvent, onPinchStateChange };
}
