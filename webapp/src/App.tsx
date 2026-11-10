import React, { useState, useEffect } from "react";
import { Page as FlashFilePage } from "./components/template/FlashFilePage";
import { CaseStudiesPage } from "./components/case-studies/CaseStudiesPage";

export const App: React.FC = () => {
  const [view, setView] = useState<"case-studies" | "portal">(() => {
    const p = window.location.pathname.toLowerCase();
    const h = window.location.hash.toLowerCase();
    const s = window.location.search.toLowerCase();
    if (p.includes("portal") || h.includes("portal") || s.includes("portal")) {
      return "portal";
    }
    return "case-studies";
  });

  useEffect(() => {
    const handleLocation = () => {
      const p = window.location.pathname.toLowerCase();
      const h = window.location.hash.toLowerCase();
      const s = window.location.search.toLowerCase();
      if (p.includes("portal") || h.includes("portal") || s.includes("portal")) {
        setView("portal");
      } else {
        setView("case-studies");
      }
    };
    window.addEventListener("popstate", handleLocation);
    window.addEventListener("hashchange", handleLocation);
    return () => {
      window.removeEventListener("popstate", handleLocation);
      window.removeEventListener("hashchange", handleLocation);
    };
  }, []);

  return (
    <div>
      {view === "case-studies" ? <CaseStudiesPage /> : <FlashFilePage />}
    </div>
  );
};

export default App;
