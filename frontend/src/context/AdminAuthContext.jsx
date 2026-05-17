import { createContext, useContext, useMemo, useState } from "react";
import { adminApi, clearAdminKey, getAdminKey } from "../services/adminApi";

const AdminAuthContext = createContext(null);

export function AdminAuthProvider({ children }) {
  const [key, setKeyState] = useState(() => getAdminKey());

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(key),
      login: async (username, password) => {
        const data = await adminApi.login(username, password);
        setKeyState(data.token);
        return data;
      },
      logout: () => {
        clearAdminKey();
        setKeyState("");
      },
    }),
    [key]
  );

  return <AdminAuthContext.Provider value={value}>{children}</AdminAuthContext.Provider>;
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) throw new Error("useAdminAuth hors AdminAuthProvider");
  return ctx;
}
