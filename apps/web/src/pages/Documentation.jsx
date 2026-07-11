import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import Box from '@mui/material/Box';

const SECTIONS = [
  { id: 'getting-started', title: 'Getting Started' },
  { id: 'providing-details', title: 'Providing Your Image & Dockerfile' },
  { id: 'analysis', title: 'Analysis & Recommendations' },
  { id: 'understanding', title: 'Understanding the Optimized Dockerfile' },
  { id: 'applying', title: 'Applying Optimizations' },
];

function Section({ id, title, refEl, children }) {
  return (
    <motion.div
      id={id}
      ref={refEl}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5 }}
      className="glass-panel rounded-2xl p-6 sm:p-8 mb-6 scroll-mt-28"
    >
      <h2 className="font-display font-bold text-xl sm:text-2xl gradient-text mb-4">{title}</h2>
      <div className="text-slate-300 leading-relaxed space-y-3">{children}</div>
    </motion.div>
  );
}

function Docs() {
  const refs = {
    'getting-started': useRef(null),
    'providing-details': useRef(null),
    analysis: useRef(null),
    understanding: useRef(null),
    applying: useRef(null),
  };

  const scrollTo = (id) => (event) => {
    event.preventDefault();
    refs[id].current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <Box className="px-4 sm:px-8 py-10 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-[220px_1fr] gap-8">
      {/* Sidebar TOC */}
      <motion.nav
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="glass-panel rounded-2xl p-5 h-fit md:sticky md:top-28"
      >
        <h3 className="font-display font-semibold text-sm uppercase tracking-widest text-neon-cyan mb-4">
          Contents
        </h3>
        <ul className="space-y-1">
          {SECTIONS.map((s, i) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                onClick={scrollTo(s.id)}
                className="block text-sm text-slate-400 hover:text-white hover:bg-white/5 rounded-lg px-3 py-2 transition-colors no-underline"
              >
                <span className="text-neon-violet font-mono-code mr-2">{i + 1}.</span>
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </motion.nav>

      {/* Content */}
      <div>
        <motion.h1
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="font-display font-bold text-3xl sm:text-4xl gradient-text mb-8"
        >
          Documentation
        </motion.h1>

        <Section id="getting-started" title="Getting Started" refEl={refs['getting-started']}>
          <p>Before diving into LayerLens's functionalities, make sure you have the following:</p>
          <ol className="list-decimal list-inside space-y-1 pl-2">
            <li>A public Docker image hosted on a registry (e.g., Docker Hub).</li>
            <li>The associated Dockerfile for that image.</li>
            <li>Access to the internet to reach LayerLens's backend.</li>
          </ol>
        </Section>

        <Section id="providing-details" title="Providing Your Image & Dockerfile" refEl={refs['providing-details']}>
          <p>To begin the analysis, provide LayerLens with your image name and Dockerfile:</p>
          <ol className="list-decimal list-inside space-y-2 pl-2">
            <li>
              Navigate to the <b className="text-neon-cyan">Optimizer</b> page from the top navigation.
            </li>
            <li>
              Enter the full image reference in the format{' '}
              <code className="font-mono-code text-neon-cyan">repository/name:tag</code>, e.g.{' '}
              <code className="font-mono-code text-neon-cyan">username/myapp:latest</code>.
            </li>
            <li>Paste the contents of your Dockerfile into the Dockerfile field.</li>
          </ol>
        </Section>

        <Section id="analysis" title="Analysis & Recommendations" refEl={refs.analysis}>
          <p>Once both fields are filled in:</p>
          <ol className="list-decimal list-inside space-y-2 pl-2">
            <li>
              Click <b className="text-neon-cyan">Run Analysis</b> to start the scan.
            </li>
            <li>
              LayerLens runs <span className="font-mono-code text-neon-violet">dive</span> against the image to
              measure layer efficiency and wasted space, then hands that report — together with your
              Dockerfile — to an AI model.
            </li>
            <li>You'll get back an efficiency score, a wasted-bytes breakdown, and a written analysis.</li>
          </ol>
        </Section>

        <Section id="understanding" title="Understanding the Optimized Dockerfile" refEl={refs.understanding}>
          <p>The AI's response typically calls out:</p>
          <ul className="space-y-1 pl-2">
            <li>
              <b className="text-neon-cyan">Base image choice</b> — suggesting a smaller/slimmer base where
              applicable.
            </li>
            <li>
              <b className="text-neon-cyan">Layer reduction</b> — consolidating commands to cut down on
              layers.
            </li>
            <li>
              <b className="text-neon-cyan">Caching</b> — using Docker's build cache and multi-stage builds
              effectively.
            </li>
          </ul>
        </Section>

        <Section id="applying" title="Applying Optimizations" refEl={refs.applying}>
          <p>You can act on the suggestions by:</p>
          <ol className="list-decimal list-inside space-y-1 pl-2">
            <li>Reviewing each change against your project's actual requirements.</li>
            <li>Manually editing your existing Dockerfile.</li>
            <li>Copying the provided example Dockerfile directly into your project.</li>
          </ol>
        </Section>
      </div>
    </Box>
  );
}

export default Docs;
