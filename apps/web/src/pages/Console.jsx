import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { analyzePost } from '../api/client';
import Box from '@mui/material/Box';
import MButton from '../components/Buttons/GlowButton';
import ScanningScreen from '../components/ScanningScreen';
import ResultsPanel from '../components/ResultsPanel';

const DEFAULT_DOCKERFILE = `FROM node:20

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

CMD ["npm", "start"]`;

function Optimizer() {
  const [imageName, setImageName] = useState('');
  const [dockerFile, setDockerFile] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiFeedback, setApiFeedback] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleOptimize = async () => {
    if (imageName.trim() && dockerFile.trim()) {
      setErrorMsg(null);
      setIsLoading(true);
      try {
        const response = await analyzePost(imageName, dockerFile);
        if (response?.error) {
          setErrorMsg(response.error);
        } else {
          setApiFeedback(response);
        }
      } catch (error) {
        console.error('There was an error sending the data to the API', error);
        setErrorMsg("Couldn't reach the analysis API. Please try again later.");
      }
      setIsLoading(false);
    } else {
      setErrorMsg('Both the image name and Dockerfile fields are required.');
    }
  };

  if (isLoading) {
    return <ScanningScreen message="Pulling layers, running Dive, and consulting the AI model. This can take up to a minute..." />;
  }

  if (apiFeedback) {
    return (
      <Box className="px-4 sm:px-8 py-10 flex flex-col items-center">
        <ResultsPanel expandedText={apiFeedback.analysis} stats={apiFeedback.stats} onReset={() => setApiFeedback(null)} />
      </Box>
    );
  }

  return (
    <Box className="px-4 sm:px-8 py-10 flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-3xl"
      >
        <div className="mb-6 text-center">
          <span className="inline-block font-mono-code text-xs tracking-[0.3em] uppercase text-neon-cyan border border-neon-cyan/40 rounded-full px-3 py-1 mb-4">
            new scan
          </span>
          <h1 className="font-display font-bold text-3xl sm:text-4xl gradient-text">Image Optimizer</h1>
        </div>

        <div className="gradient-border rounded-2xl shadow-neon overflow-hidden">
          {/* terminal chrome header */}
          <div className="flex items-center gap-2 bg-[#15151f] px-4 py-3 border-b border-neon-violet/20">
            <span className="w-3 h-3 rounded-full bg-neon-pink/70" />
            <span className="w-3 h-3 rounded-full bg-neon-cyan/70" />
            <span className="w-3 h-3 rounded-full bg-neon-green/70" />
            <span className="ml-3 font-mono-code text-xs text-slate-400">
              dia<span className="text-neon-cyan">@</span>optimizer
              <span className="animate-blink text-neon-violet">▍</span>
            </span>
          </div>

          <div className="p-5 sm:p-8 space-y-6 bg-[#0d0d16]/80">
            <div>
              <label className="block font-mono-code text-xs uppercase tracking-widest text-neon-violet mb-2">
                $ image_name
              </label>
              <input
                value={imageName}
                onChange={(e) => setImageName(e.target.value)}
                placeholder="e.g. node:20 or myrepo/myapp:latest"
                className="w-full bg-black/40 border border-neon-violet/30 focus:border-neon-cyan focus:shadow-glow rounded-lg px-4 py-3 text-slate-100 font-mono-code text-sm outline-none transition-shadow placeholder:text-slate-500"
              />
            </div>

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
                rows={12}
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
              <MButton text="Run Analysis ▸" onClick={handleOptimize} />
            </div>
          </div>
        </div>
      </motion.div>
    </Box>
  );
}

export default Optimizer;
