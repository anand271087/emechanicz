import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { Button, ErrorNote, Field, Input } from "../components/ui";
import { useAuth } from "../lib/auth";
import { supabase } from "../lib/supabase";

export default function Login() {
  const { session } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (session) return <Navigate to="/quotes" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    setBusy(false);
    if (error) {
      setError(error.message === "Invalid login credentials"
        ? "That email and password don't match. Check them and try again." : error.message);
    }
  }

  return (
    <div className="grid min-h-dvh place-items-center bg-navy-deep px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-3 text-white">
          <img src="/logo.png" alt="" className="size-14 rounded-full bg-white p-1" />
          <div>
            <p className="text-xl font-bold tracking-wide">EMechanicz</p>
            <p className="text-fixture">Test Solutions sales portal</p>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4 rounded-lg bg-white p-6 shadow-2xl">
          <h1 className="text-xl font-bold text-navy">Sign in</h1>
          <Field label="Email">
            {(id) => <Input id={id} type="email" autoComplete="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} />}
          </Field>
          <Field label="Password">
            {(id) => <Input id={id} type="password" autoComplete="current-password" required value={password}
              onChange={(e) => setPassword(e.target.value)} />}
          </Field>
          {error && <ErrorNote message={error} />}
          <Button type="submit" busy={busy} className="w-full">Sign in</Button>
          <p className="text-center text-sm text-muted">Need an account? Ask your admin to add you.</p>
        </form>
      </div>
    </div>
  );
}
