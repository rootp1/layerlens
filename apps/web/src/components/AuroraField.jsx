import React from 'react';
import { motion } from 'framer-motion';

// Fixed, full-viewport ambient background: animated grid + drifting neon glow orbs.
// Pure CSS/SVG + framer-motion, no canvas / external deps.
export default function AuroraField() {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 -z-10 overflow-hidden bg-void"
    >
      {/* moving grid */}
      <div className="absolute inset-0 bg-grid-pattern bg-[length:48px_48px] animate-grid-pan opacity-40" />

      {/* radial vignette to keep edges dark */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#08080d_78%)]" />

      {/* glow orbs */}
      <motion.div
        className="absolute -top-32 -left-24 w-[32rem] h-[32rem] rounded-full bg-neon-violet/25 blur-[110px] animate-float"
      />
      <motion.div
        className="absolute top-1/3 -right-24 w-[28rem] h-[28rem] rounded-full bg-neon-cyan/20 blur-[110px] animate-float-slow"
      />
      <motion.div
        className="absolute bottom-[-10rem] left-1/3 w-[26rem] h-[26rem] rounded-full bg-neon-pink/15 blur-[110px] animate-float"
        style={{ animationDelay: '2s' }}
      />

      {/* scanline sheen */}
      <div className="absolute inset-0 opacity-[0.03] bg-[repeating-linear-gradient(0deg,#fff_0px,#fff_1px,transparent_1px,transparent_3px)]" />
    </div>
  );
}
