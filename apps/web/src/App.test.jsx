import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the LayerLens nav logo', () => {
  render(<App />);
  const logoElement = screen.getByText(/LayerLens/i);
  expect(logoElement).toBeInTheDocument();
});
