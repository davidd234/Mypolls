import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import EuropeMapSVG from "./components/map/EuropeMapSVG";

function EuropeMap() {
  const navigate = useNavigate();

  return (
    <div className="app-root">
      {/* HEADER */}
      <header className="app-header">
        <h1>Europe Political Map</h1>
        <p>Experimental political data visualization</p>
      </header>

      {/* MAP */}
      <main className="app-map">
        <EuropeMapSVG />
      </main>

      {/* FOOTER */}
      <footer className="app-footer">
        Prototype interface for political analysis. Not an official source.
      </footer>
    </div>
  );
}

function CountryPage({ code }) {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Country: {code.toUpperCase()}</h1>
      </header>

      <main className="app-map">
        <p style={{ color: "#9ca3af" }}>
          Country dashboard coming next.
        </p>
      </main>
    </div>
  );
}

function CountryWrapper() {
  const code = window.location.pathname.split("/").pop();
  return <CountryPage code={code} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EuropeMap />} />
        <Route path="/country/:code" element={<CountryWrapper />} />
      </Routes>
    </BrowserRouter>
  );
}
