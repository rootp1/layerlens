import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Box from '@mui/material/Box';
import { lintPost } from '../api/client';
import MButton from '../components/Buttons/GlowButton';
import CountUp from '../components/CountUp';

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
const SEVERITY_STYLE = {
  critical: 'text-pink-300 border-pink-500/40 bg-pink-500/10',
  high: 'text-orange-300 border-orange-500/40 bg-orange-500/10',
  medium: 'text-yellow-200 border-yellow-500/40 bg-yellow-500/10',
  low: 'text-slate-300 border-slate-500/40 bg-slate-500/10',
};

const DEFAULT_DOCKERFILE = `FROM node:20

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

CMD ["npm", "start"]`;

function scoreColor(score) {
  if (score >= 80) return 'text-neon-green';
  if (score >= 50) return 'text-yellow-300';
  return 'text-neon-pink';
}

function Lint() {
  const [dockerFile, setDockerFile] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleScan = async () => {
    if (!dockerFile.trim()) {
      setErrorMsg('Paste a Dockerfile first.');
      return;
    }
    setErrorMsg(null);
    setIsLoading(true);
    setResult(null);
    const response = await lintPost(dockerFile);
    if (response?.error) {
      setErrorMsg(response.error);
    } else {
      setResult(response);
    }
    setIsLoading(false);
  };

  const findings = result ? [...result.findings].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
  ) : [];

  return (
    <Box className="px-4 sm:px-8 py-10 flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-3xl"
      >
        <div className="mb-6 text-center">
          <span className="inline-block font-mono-code text-xs tracking-[0.3em] uppercase text-neon-green border border-neon-green/40 rounded-full px-3 py-1 mb-4">
            instant · no docker required
          </span>
          <h1 className="font-display font-bold text-3xl sm:text-4xl gradient-text">Dockerfile Lint</h1>
          <p className="text-slate-400 text-sm mt-2 max-w-lg mx-auto">
            The same static rule engine that powers <code className="font-mono-code text-neon-cyan">layerlens-lint</code> —
            paste a Dockerfile and get a score plus fixes in milliseconds, no image build or Docker daemon needed.
          </p>
        </div>

        <div className="gradient-border rounded-2xl shadow-neon overflow-hidden">
          <div className="flex items-center gap-2 bg-[#15151f] px-4 py-3 border-b border-neon-violet/20">
            <span className="w-3 h-3 rounded-full bg-neon-pink/70" />
            <span className="w-3 h-3 rounded-full bg-neon-cyan/70" />
            <span className="w-3 h-3 rounded-full bg-neon-green/70" />
            <span className="ml-3 font-mono-code text-xs text-slate-400">
              layerlens-lint<span className="text-neon-cyan">@</span>scan
              <span className="animate-blink text-neon-violet">▍</span>
            </span>
          </div>

          <div className="p-5 sm:p-8 space-y-6 bg-[#0d0d16]/80">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block font-mono-code text-xs uppercase tracking-widest text-neon-violet">
                  $ dockerfile
                </label>
                <button
                  type="button"
                  onClick={() => setDockerFile(DEFAULT_DOCKERFILE)}
                  className="text-xs text-slate-400 hover:text-neon-cyan transition-colors font-mono-code"
                >
                  insert example
                </button>
              </div>
              <textarea
                value={dockerFile}
                onChange={(e) => setDockerFile(e.target.value)}
                rows={14}
                placeholder={'FROM node:20\n\nWORKDIR /app\n...'}
                className="w-full bg-black/40 border border-neon-violet/30 focus:border-neon-cyan focus:shadow-glow rounded-lg px-4 py-3 text-slate-100 font-mono-code text-sm outline-none transition-shadow resize-y placeholder:text-slate-500"
              />
            </div>

            {errorMsg && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-pink-300 bg-pink-500/10 border border-pink-500/30 rounded-lg px-4 py-2 font-mono-code"
              >
                ⚠ {errorMsg}
              </motion.div>
            )}

            <div className="flex justify-end">
              <MButton text={isLoading ? 'Scanning…' : 'Scan Dockerfile ▸'} onClick={handleScan} />
            </div>

            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.4 }}
                  className="overflow-hidden"
                >
                  <div className="border-t border-neon-violet/20 pt-6 mt-2">
                    <div className="flex items-center gap-6 mb-6">
                      <div className={`text-5xl font-display font-bold ${scoreColor(result.score)}`}>
                        <CountUp value={result.score} />
                      </div>
                      <div>
                        <div className="text-sm text-slate-300 font-semibold">/ 100</div>
                        <div className="text-xs text-slate-500">
                          {findings.length === 0
                            ? 'No issues found.'
                            : `${findings.length} finding${findings.length === 1 ? '' : 's'}`}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {findings.map((f, i) => (
                        <motion.div
                          key={f.rule_id}
                          initial={{ opacity: 0, x: -12 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: i * 0.05 }}
                          className={`rounded-lg border px-4 py-3 ${SEVERITY_STYLE[f.severity] || SEVERITY_STYLE.low}`}
                        >
                          <div className="flex items-center gap-2 text-xs font-mono-code uppercase tracking-wider mb-1">
                            <span className="font-bold">{f.severity}</span>
                            <span className="text-slate-500">·</span>
                            <span className="text-slate-500">{f.rule_id}</span>
                          </div>
                          <div className="text-sm text-slate-100">{f.message}</div>
                          <div className="text-xs text-slate-400 mt-1">→ {f.suggestion}</div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </Box>
  );
}

export default Lint;
