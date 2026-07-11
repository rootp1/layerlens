import React, { useEffect, useRef, useState } from 'react';
import { animate } from 'framer-motion';

// Animates a number count-up from 0 -> value whenever value changes.
export default function CountUp({ value, decimals = 0, suffix = '', prefix = '', duration = 1.4 }) {
  const [display, setDisplay] = useState(0);
  const target = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  const controlsRef = useRef(null);

  useEffect(() => {
    controlsRef.current?.stop();
    controlsRef.current = animate(0, target, {
      duration,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(v),
    });
    return () => controlsRef.current?.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  return (
    <span>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}
