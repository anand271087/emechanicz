import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { supabase } from "../lib/supabase";
import { MODULES } from "../modules/registry";

export default function Layout() {
  const { email, isAdmin } = useAuth();
  const modules = MODULES.filter((m) => !m.adminOnly || isAdmin);

  return (
    <div className="min-h-dvh md:flex">
      <aside className="hidden w-60 shrink-0 flex-col bg-navy-deep text-white md:sticky md:top-0 md:flex md:h-dvh">
        <div className="flex items-center gap-3 px-5 py-5">
          <img src="/logo.png" alt="" className="size-10 rounded-full bg-white p-0.5" />
          <div className="leading-tight">
            <p className="font-bold tracking-wide">EMechanicz</p>
            <p className="text-sm text-fixture">Sales portal</p>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 px-3" aria-label="Modules">
          {modules.map((m) => (
            <NavLink key={m.path} to={m.path}
              className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2.5 font-medium
                transition-colors ${isActive ? "bg-white/12 text-white shadow-[inset_3px_0_0_var(--color-fixture)]"
                  : "text-white/70 hover:bg-white/6 hover:text-white"}`}>
              {m.icon}{m.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 px-5 py-4 text-sm">
          <p className="truncate text-white/80" title={email}>{email}</p>
          <button onClick={() => supabase.auth.signOut()} className="mt-1 text-fixture hover:text-white">
            Sign out
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between bg-navy-deep px-4 py-2.5
        text-white md:hidden" style={{ paddingTop: "max(0.625rem, env(safe-area-inset-top))" }}>
        <div className="flex items-center gap-2.5">
          <img src="/logo.png" alt="" className="size-8 rounded-full bg-white p-0.5" />
          <span className="font-bold tracking-wide">EMechanicz</span>
        </div>
        <button onClick={() => supabase.auth.signOut()} className="text-sm text-fixture">Sign out</button>
      </header>

      <main className="min-w-0 flex-1 px-4 pb-28 pt-5 md:px-8 md:pb-10 md:pt-8">
        <div className="mx-auto max-w-6xl"><Outlet /></div>
      </main>

      <nav aria-label="Modules" className="fixed inset-x-0 bottom-0 z-30 grid border-t border-line bg-white
        md:hidden" style={{ gridTemplateColumns: `repeat(${modules.length}, 1fr)`,
        paddingBottom: "env(safe-area-inset-bottom)" }}>
        {modules.map((m) => (
          <NavLink key={m.path} to={m.path}
            className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-xs font-medium
              ${isActive ? "text-navy" : "text-muted"}`}>
            {m.icon}{m.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
