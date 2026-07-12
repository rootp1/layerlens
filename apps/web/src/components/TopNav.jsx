import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import useScrollTrigger from '@mui/material/useScrollTrigger';
import Slide from '@mui/material/Slide';

const LINKS = [
  { label: 'Home', to: '/home' },
  { label: 'Console', to: '/console' },
  { label: 'Lint', to: '/lint' },
  { label: 'Docs', to: '/docs' },
];

function HideOnScroll({ children }) {
  const trigger = useScrollTrigger();
  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

export default function TopNav() {
  const location = useLocation();
  const currentPath = '/' + (location.pathname.replace('/', '') || 'home');
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <HideOnScroll>
      <AppBar elevation={0} position="fixed" sx={{ background: 'transparent', boxShadow: 'none' }}>
        <div className="glass-panel mx-3 mt-3 rounded-2xl border border-neon-violet/25 shadow-neon-sm">
          <Toolbar className="!min-h-[64px] flex items-center justify-between px-2 sm:px-4">
            <Link to="/home" className="flex items-center gap-2 no-underline">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full rounded-full bg-neon-cyan opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-neon-cyan" />
              </span>
              <span className="font-display text-2xl sm:text-3xl font-bold gradient-text tracking-wide">
                LayerLens
              </span>
              <span className="hidden sm:inline-block text-[10px] uppercase tracking-[0.2em] text-slate-400 font-mono-code ml-1 border border-neon-violet/30 rounded px-1.5 py-0.5">
                beta
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-1 relative">
              {LINKS.map((link) => {
                const active = currentPath === link.to;
                return (
                  <Link key={link.to} to={link.to} className="relative no-underline px-4 py-2">
                    <span
                      className={`relative z-10 font-medium tracking-wide transition-colors ${
                        active ? 'text-white' : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      {link.label}
                    </span>
                    {active && (
                      <motion.span
                        layoutId="nav-pill"
                        className="absolute inset-0 rounded-lg bg-gradient-to-r from-violet-600/70 to-cyan-500/70 shadow-neon-sm"
                        transition={{ type: 'spring', duration: 0.5 }}
                      />
                    )}
                  </Link>
                );
              })}
            </div>

            <button
              className="md:hidden text-slate-200 p-2"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <div className="w-6 flex flex-col gap-1.5">
                <motion.span
                  animate={{ rotate: mobileOpen ? 45 : 0, y: mobileOpen ? 6 : 0 }}
                  className="h-0.5 w-full bg-current rounded"
                />
                <motion.span animate={{ opacity: mobileOpen ? 0 : 1 }} className="h-0.5 w-full bg-current rounded" />
                <motion.span
                  animate={{ rotate: mobileOpen ? -45 : 0, y: mobileOpen ? -6 : 0 }}
                  className="h-0.5 w-full bg-current rounded"
                />
              </div>
            </button>
          </Toolbar>

          <AnimatePresence>
            {mobileOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="md:hidden overflow-hidden"
              >
                <div className="flex flex-col gap-1 px-4 pb-4">
                  {LINKS.map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      onClick={() => setMobileOpen(false)}
                      className={`no-underline rounded-lg px-3 py-2 font-medium ${
                        currentPath === link.to
                          ? 'bg-gradient-to-r from-violet-600/70 to-cyan-500/70 text-white'
                          : 'text-slate-300'
                      }`}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </AppBar>
    </HideOnScroll>
  );
}
