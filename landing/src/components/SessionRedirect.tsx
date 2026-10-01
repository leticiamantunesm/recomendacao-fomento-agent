"use client";

import { useEffect } from "react";

/**
 * Usuários com token de sessão vão direto ao painel.
 * Visitantes anônimos permanecem na landing.
 */
export function SessionRedirect() {
  useEffect(() => {
    try {
      const token = localStorage.getItem("rf_access_token");
      const company = localStorage.getItem("rf_company_id");
      const employee = localStorage.getItem("rf_employee_id");
      if (token && company && employee) {
        window.location.replace("/dashboard.html");
      }
    } catch {
      /* ignore */
    }
  }, []);

  return null;
}
