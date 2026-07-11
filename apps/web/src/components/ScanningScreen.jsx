import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import { motion, AnimatePresence } from 'framer-motion';

const STATUS_MESSAGES = [
  'Pulling image layers...',
  'Running Dive analysis...',
  'Measuring wasted bytes...',
  'Consulting the AI model...',
  'Drafting an optimized Dockerfile...',
  'Almost done...',
];

const ScanningScreen = ({ message }) => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setStep((s) => (s + 1) % STATUS_MESSAGES.length);
    }, 2400);
    return () => clearInterval(id);
  }, []);

  return (
    <Box className="min-h-[70vh] flex flex-col items-center justify-center px-4">
      <div className="relative h-40 w-40 flex items-center justify-center mb-10">
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-neon-violet/60 border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-3 rounded-full border-2 border-neon-cyan/60 border-b-transparent"
          animate={{ rotate: -360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-7 rounded-full border-2 border-dashed border-neon-pink/50"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        />
        <motion.span
          className="text-4xl select-none"
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        >
          🐳
        </motion.span>
      </div>

      <h2 className="font-display font-bold text-2xl gradient-text mb-3 text-center">
        Analyzing your image
      </h2>

      <div className="h-6 mb-6">
        <AnimatePresence mode="wait">
          <motion.p
            key={step}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
            className="font-mono-code text-sm text-slate-300 text-center"
          >
            {STATUS_MESSAGES[step]}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="w-full max-w-md h-1.5 rounded-full bg-white/5 overflow-hidden relative">
        <motion.div
          className="absolute inset-y-0 left-0 w-1/3 rounded-full bg-gradient-to-r from-violet-500 via-cyan-400 to-pink-400"
          animate={{ left: ['-33%', '100%'] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      {message && (
        <p className="text-slate-500 text-xs text-center max-w-md mt-6">{message}</p>
      )}
    </Box>
  );
};

export default ScanningScreen;
