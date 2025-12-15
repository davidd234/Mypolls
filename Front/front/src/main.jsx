import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import EuropeMapSVG from "./components/map/EuropeMapSVG";
import CountryPage from "./pages/CountryPage";

import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* HARTA */}
        <Route path="/" element={<EuropeMapSVG />} />

        {/* PAGINA DE ȚARĂ */}
        <Route path="/country/:code" element={<CountryPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
