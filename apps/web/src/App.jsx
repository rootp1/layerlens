import * as React from 'react';
import { Routes, Route, useLocation, BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { AnimatePresence, motion } from 'framer-motion';

import theme from './theme';
import Landing from './pages/Landing';
import Documentation from './pages/Documentation';
import Console from './pages/Console';
import Lint from './pages/Lint';
import TopNav from './components/TopNav';
import AuroraField from './components/AuroraField';
import Footer from './components/Footer';

const pageVariants = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -24 },
};

function PageTransition({ children }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function AppShell() {
  const location = useLocation();
  return (
    <>
      <AuroraField />
      <TopNav />
      <Toolbar sx={{ minHeight: { xs: 88, sm: 96 } }} />
      <Box
        component="main"
        sx={{
          position: 'relative',
          zIndex: 1,
          minHeight: 'calc(100vh - 96px)',
          width: '100%',
          maxWidth: '100%',
          overflowX: 'hidden',
        }}
      >
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<PageTransition><Landing /></PageTransition>} />
            <Route path="/home" element={<PageTransition><Landing /></PageTransition>} />
            <Route path="/docs" element={<PageTransition><Documentation /></PageTransition>} />
            <Route path="/console" element={<PageTransition><Console /></PageTransition>} />
            <Route path="/lint" element={<PageTransition><Lint /></PageTransition>} />
          </Routes>
        </AnimatePresence>
        <Footer />
      </Box>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppShell />
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
