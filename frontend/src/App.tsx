import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { Spinner, ToastProvider } from "./components/ui";
import { AuthProvider, useAuth } from "./lib/auth";
import Customers from "./modules/customers/Customers";
import QuoteBuilder from "./modules/quotations/QuoteBuilder";
import QuoteList from "./modules/quotations/QuoteList";
import QuotePreview from "./modules/quotations/QuotePreview";
import Settings from "./modules/settings/Settings";
import Login from "./pages/Login";

function RequireAuth({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) return <Spinner />;
  return session ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<RequireAuth><Layout /></RequireAuth>}>
              <Route index element={<Navigate to="/quotes" replace />} />
              <Route path="/quotes" element={<QuoteList />} />
              <Route path="/quotes/new" element={<QuoteBuilder />} />
              <Route path="/quotes/:id" element={<QuotePreview />} />
              <Route path="/quotes/:id/edit" element={<QuoteBuilder />} />
              <Route path="/customers" element={<Customers />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/quotes" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
