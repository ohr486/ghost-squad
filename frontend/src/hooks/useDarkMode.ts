import { useState, useEffect } from "react";

export const useDarkMode = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // Check localStorage first, then system preference
    const saved = localStorage.getItem("darkMode");
    if (saved !== null) {
      return JSON.parse(saved);
    }
    // Default to dark mode as requested
    return true;
  });

  useEffect(() => {
    const root = window.document.documentElement;

    if (isDarkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }

    // Save preference to localStorage
    localStorage.setItem("darkMode", JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return { isDarkMode, toggleDarkMode };
};
