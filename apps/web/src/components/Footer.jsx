import React from 'react';
import { motion } from 'framer-motion';

export default function Footer() {
  return (
    <footer className="relative z-10 mt-16 px-4 sm:px-8 pb-8 pt-6 flex flex-col items-center gap-3 text-center">
      <motion.a
        href="https://featherless.ai"
        target="_blank"
        rel="noreferrer"
        whileHover={{ scale: 1.04 }}
        className="inline-flex items-center gap-2 no-underline glass-panel rounded-full px-4 py-2 shadow-neon-sm"
      >
        <motion.span
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-neon-cyan"
        >
          ⚡
        </motion.span>
        <span className="text-xs font-mono-code text-slate-300">
          Powered by <span className="gradient-text font-semibold">Featherless.ai</span>
        </span>
      </motion.a>
      <p className="text-[11px] text-slate-500 font-mono-code">
        Layer analysis via Dive · AI advice via Featherless.ai
      </p>
    </footer>
  );
}
