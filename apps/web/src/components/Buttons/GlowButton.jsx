import React from 'react';
import { motion } from 'framer-motion';

// variant: 'primary' (filled neon gradient) | 'ghost' (outlined glass)
const MButton = ({ text, onClick, type = 'button', variant = 'primary', icon = null, className = '' }) => {
  const base =
    'relative overflow-hidden px-6 py-2.5 rounded-xl font-display font-semibold tracking-wide transition-shadow flex items-center gap-2 justify-center';

  const styles =
    variant === 'primary'
      ? 'text-white bg-gradient-to-r from-violet-600 via-fuchsia-500 to-cyan-500 bg-[length:200%_auto] animate-gradient-x shadow-neon-sm hover:shadow-neon'
      : 'text-slate-200 border border-neon-violet/40 bg-white/5 backdrop-blur hover:border-neon-cyan/60 hover:text-white';

  return (
    <motion.button
      type={type}
      onClick={onClick}
      whileHover={{ scale: 1.045 }}
      whileTap={{ scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 400, damping: 18 }}
      className={`${base} ${styles} ${className}`}
    >
      {icon}
      <span className="relative z-10">{text}</span>
    </motion.button>
  );
};

export default MButton;
