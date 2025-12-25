import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import HomePage from "./pages/HomePage";
import InquiriesPage from "./pages/InquiriesPage";
import TasksPage from "./pages/TasksPage";
import "./App.css";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/inquiries" element={<InquiriesPage />} />
        <Route path="/tasks" element={<TasksPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
