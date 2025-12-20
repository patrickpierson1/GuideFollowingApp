// src/hooks/useHoldSelect.js
import { useEffect, useRef } from 'react';

export function useHoldSelect({ enabled, onSelect, holdMs = 1000 }) {
  const holdTimerRef = useRef(null);
  const holdTargetIdRef = useRef(null);

  const startHoldSelect = (id) => {
    if (!enabled) return;
    if (id == null) return;

    holdTargetIdRef.current = id;

    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }

    holdTimerRef.current = setTimeout(() => {
      if (holdTargetIdRef.current === id) {
        onSelect?.(id);
      }
    }, holdMs);
  };

  const cancelHoldSelect = () => {
    holdTargetIdRef.current = null;
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (holdTimerRef.current) {
        clearTimeout(holdTimerRef.current);
        holdTimerRef.current = null;
      }
    };
  }, []);

  return { startHoldSelect, cancelHoldSelect };
}
