import React, { useState, useEffect } from "react";
import { Page as FlashFilePage } from "./components/template/FlashFilePage";
import { CaseStudiesPage } from "./components/case-studies/CaseStudiesPage";
import { AuthLoginCard } from "./components/auth/AuthLoginCard";

export const App: React.FC = () => {
  const checkIsAdminRoute = () => {
    const p = window.location.pathname.toLowerCase();
    const h = window.location.hash.toLowerCase();
    const s = window.location.search.toLowerCase();
    return (
      p.includes("admin") ||
      p.includes("dashboard") ||
      p.includes("login") ||
      h.includes("admin") ||
      h.includes("dashboard") ||
      h.includes("login") ||
      s.includes("admin") ||
      s.includes("dashboard")
    );
  };

  const [isAdminRoute, setIsAdminRoute] = useState<boolean>(checkIsAdminRoute);

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return (
      localStorage.getItem("flashfile_admin_auth") === "true" ||
      sessionStorage.getItem("flashfile_admin_auth") === "true"
    );
  });

  useEffect(() => {
    const handleLocation = () => {
      setIsAdminRoute(checkIsAdminRoute());
    };
    window.addEventListener("popstate", handleLocation);
    window.addEventListener("hashchange", handleLocation);
    return () => {
      window.removeEventListener("popstate", handleLocation);
      window.removeEventListener("hashchange", handleLocation);
    };
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("flashfile_admin_auth");
    localStorage.removeItem("flashfile_admin_user");
    sessionStorage.removeItem("flashfile_admin_auth");
    sessionStorage.removeItem("flashfile_admin_user");
    setIsAuthenticated(false);
  };

  const handleBackToHome = () => {
    window.history.pushState({}, "", "/");
    setIsAdminRoute(false);
  };

  // Root endpoint: Main FlashFile Webapp
  if (!isAdminRoute) {
    return <FlashFilePage />;
  }

  // /admin endpoint: Login Screen if unauthenticated, otherwise Admin Portal (Apex CaseStudiesPage)
  if (!isAuthenticated) {
    return (
      <AuthLoginCard
        onSuccess={handleLoginSuccess}
        onBackToHome={handleBackToHome}
      />
    );
  }

  return (
    <CaseStudiesPage
      onLogout={handleLogout}
      onBackToHome={handleBackToHome}
    />
  );
};

export default App;
