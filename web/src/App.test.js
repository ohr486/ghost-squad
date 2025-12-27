import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Ghost Squad heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/Ghost Squad/i);
  expect(headingElement).toBeInTheDocument();
});

test('renders platform description', () => {
  render(<App />);
  const descriptionElement = screen.getByText(/AI-Driven Task Management Platform/i);
  expect(descriptionElement).toBeInTheDocument();
});
