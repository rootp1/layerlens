import * as React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Box from '@mui/material/Box';
import MButton from '../components/Buttons/GlowButton';

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};
const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

const FEATURES = [
  {
    title: 'Layer-Level Insight',
    desc: 'Runs Dive against your image to surface efficiency, wasted bytes, and layer bloat instantly.',
    glyph: '▤',
    color: 'from-violet-600 to-fuchsia-500',
  },
  {
    title: 'AI-Written Fixes',
    desc: 'A language model reads the report plus your Dockerfile and writes plain-English optimizations.',
    glyph: '✦',
    color: 'from-cyan-500 to-blue-600',
  },
  {
    title: 'Ready-to-Paste Dockerfile',
    desc: 'Get back a concrete, improved Dockerfile example — not just abstract advice.',
    glyph: '⌁',
    color: 'from-pink-500 to-violet-600',
  },
];

const STATS = [
  { label: 'Analysis engine', value: 'Dive' },
  { label: 'Response time', value: '~20s' },
  { label: 'Setup required', value: 'Zero' },
];

function GlowOrb() {
  return (
    <div className="relative flex items-center justify-center h-64 w-64 sm:h-80 sm:w-80 mx-auto">
      <motion.div
        className="absolute inset-0 rounded-full bg-gradient-to-tr from-neon-violet via-neon-cyan to-neon-pink blur-2xl opacity-40"
        animate={{ scale: [1, 1.08, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute h-full w-full rounded-full border border-neon-violet/40"
        animate={{ rotate: 360 }}
        transition={{ duration: 14, repeat: Infinity, ease: 'linear' }}
      >
        <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 h-3 w-3 rounded-full bg-neon-cyan shadow-neon-sm" />
      </motion.div>
      <motion.div
        className="absolute h-[85%] w-[85%] rounded-full border border-dashed border-neon-cyan/30"
        animate={{ rotate: -360 }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
      />
      <div className="relative z-10 h-40 w-40 sm:h-52 sm:w-52 rounded-3xl glass-panel shadow-neon flex items-center justify-center animate-float">
        <span className="font-display text-6xl sm:text-7xl gradient-text select-none">🐳</span>
      </div>
    </div>
  );
}

function Home() {
  return (
    <Box className="px-4 sm:px-8 pb-24">
      {/* Hero */}
      <motion.section
        variants={container}
        initial="hidden"
        animate="show"
        className="max-w-6xl mx-auto pt-10 sm:pt-16 grid grid-cols-1 md:grid-cols-2 gap-10 items-center"
      >
        <div>
          <motion.span
            variants={item}
            className="inline-block font-mono-code text-xs tracking-[0.3em] uppercase text-neon-cyan border border-neon-cyan/40 rounded-full px-3 py-1 mb-6"
          >
            AI-powered · Dive-backed
          </motion.span>

          <motion.h1
            variants={item}
            className="font-display font-bold text-4xl sm:text-6xl leading-tight gradient-text mb-4"
          >
            Docker images,<br /> decoded instantly.
          </motion.h1>

          <motion.p variants={item} className="text-slate-300 text-lg max-w-lg mb-8">
            Paste an image name and its Dockerfile. LayerLens runs a real layer analysis and hands
            it to an AI model that writes you a concrete, optimized rebuild — bloat, caches,
            and all, explained in plain English.
          </motion.p>

          <motion.div variants={item} className="flex flex-wrap gap-4 mb-10">
            <Link to="/console">
              <MButton text="Launch Optimizer →" />
            </Link>
            <Link to="/docs">
              <MButton text="Read the Docs" variant="ghost" />
            </Link>
          </motion.div>

          <motion.div variants={item} className="flex flex-wrap gap-6">
            {STATS.map((s) => (
              <div key={s.label}>
                <div className="font-display font-bold text-2xl text-white">{s.value}</div>
                <div className="text-xs uppercase tracking-wider text-slate-400">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>

        <motion.div variants={item}>
          <GlowOrb />
        </motion.div>
      </motion.section>

      {/* Feature grid */}
      <section className="max-w-6xl mx-auto mt-24 sm:mt-32">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.5 }}
          className="font-display font-bold text-2xl sm:text-3xl text-center text-white mb-12"
        >
          What actually happens under the hood
        </motion.h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.5, delay: i * 0.12 }}
              whileHover={{ y: -6 }}
              className="glass-panel rounded-2xl p-6 shadow-neon-sm hover:shadow-neon transition-shadow"
            >
              <div
                className={`h-12 w-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center text-2xl text-white mb-4 shadow-neon-sm`}
              >
                {f.glyph}
              </div>
              <h3 className="font-display font-semibold text-lg text-white mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA banner */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl mx-auto mt-24 sm:mt-32"
      >
        <div className="gradient-border rounded-3xl p-10 sm:p-14 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-grid-pattern bg-[length:32px_32px] opacity-10 animate-grid-pan" />
          <h2 className="font-display font-bold text-2xl sm:text-3xl gradient-text mb-3 relative">
            Stop guessing why your image is 1.2GB.
          </h2>
          <p className="text-slate-300 mb-8 relative">
            Drop in an image and Dockerfile — get an efficiency score and a rewrite in under a minute.
          </p>
          <Link to="/console" className="relative inline-block">
            <MButton text="Start Analyzing" />
          </Link>
        </div>
      </motion.section>
    </Box>
  );
}

export default Home;
