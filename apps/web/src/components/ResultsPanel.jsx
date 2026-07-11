import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MarkdownLite from './MarkdownLite';
import WasteChart from './WasteChart';
import CountUp from './CountUp';
import MButton from './Buttons/GlowButton';

function StatTile({ label, value, decimals = 0, suffix = '', accent }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-panel rounded-2xl p-5 flex-1 min-w-[150px] shadow-neon-sm"
    >
      <div className={`text-3xl font-display font-bold ${accent}`}>
        <CountUp value={value} decimals={decimals} suffix={suffix} />
      </div>
      <div className="text-xs uppercase tracking-widest text-slate-400 mt-1">{label}</div>
    </motion.div>
  );
}

export default function RecipeReviewCard({ expandedText, stats, onReset }) {
  const [expanded, setExpanded] = React.useState(false);

  const efficiency = stats?.efficiency ?? 0;
  const userWasted = stats?.userWastedPercent;
  const wastedBytes = stats?.wastedBytes ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-3xl"
    >
      <div className="mb-6 text-center">
        <span className="inline-block font-mono-code text-xs tracking-[0.3em] uppercase text-neon-green border border-neon-green/40 rounded-full px-3 py-1 mb-4">
          scan complete
        </span>
        <h1 className="font-display font-bold text-3xl sm:text-4xl gradient-text">Analysis Report</h1>
      </div>

      <div className="flex flex-wrap gap-4 mb-6">
        <StatTile label="Efficiency" value={efficiency} decimals={1} suffix="%" accent="text-neon-green" />
        <StatTile
          label="User Wasted"
          value={Number.isFinite(userWasted) ? userWasted : 0}
          decimals={1}
          suffix="%"
          accent="text-neon-pink"
        />
        <StatTile label="Wasted Bytes" value={wastedBytes} decimals={0} accent="text-neon-cyan" />
      </div>

      <div className="gradient-border rounded-2xl shadow-neon overflow-hidden">
        <div className="p-5 sm:p-8 bg-[#0d0d16]/80">
          <WasteChart data={wastedBytes} />

          <div className="flex flex-wrap gap-3 justify-center mt-6">
            <MButton
              text={expanded ? 'Hide Full Analysis' : 'View Full Analysis'}
              variant="ghost"
              onClick={() => setExpanded((v) => !v)}
            />
            {onReset && <MButton text="New Scan ↻" onClick={onReset} />}
          </div>

          <AnimatePresence initial={false}>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <div className="mt-6 rounded-xl border border-neon-violet/25 bg-black/30 p-5 sm:p-6">
                  <div className="flex items-center gap-2 mb-4 text-xs font-mono-code text-slate-400 uppercase tracking-widest">
                    <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse-glow" />
                    AI analysis output
                  </div>
                  <MarkdownLite text={expandedText} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
