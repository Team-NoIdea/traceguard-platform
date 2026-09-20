import { useState } from "react";
import type { FormEvent } from "react";
import { signOut, updateProfile } from "firebase/auth";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { LogOut, ShieldCheck } from "lucide-react";
import { firebaseAuth } from "@/lib/firebase";
import { apiClient } from "@/lib/api";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";

export function Profile() {
  const user = firebaseAuth!.currentUser!;
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [name, setName] = useState(user.displayName || "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      await updateProfile(user, { displayName: name.trim() });
      await user.getIdToken(true);
      await apiClient.get("/auth/me");
      setMessage("Profile saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save your profile."); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError("");
    try {
      await signOut(firebaseAuth!);
      cache.clear();
      navigate("/", { replace: true });
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to log out."); setBusy(false); }
  }
  return <PageContainer title="Your profile">
    <div className="mx-auto max-w-2xl space-y-6">
      <section className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-accent-soft text-xl text-accent">
            {user.photoURL ? <img src={user.photoURL} alt="" referrerPolicy="no-referrer" className="h-full w-full object-cover" /> : (user.displayName || user.email || "U").slice(0,1).toUpperCase()}
          </div>
          <div><h2 className="text-xl text-text-primary">{user.displayName || "Your account"}</h2><p className="mt-1 text-sm text-text-secondary">Manage your TraceGuard profile.</p></div>
        </div>
        <form onSubmit={save} className="space-y-5">
          <label className="block text-sm text-text-secondary">Display name
            <input value={name} onChange={e => setName(e.target.value)} maxLength={100} required autoComplete="name" className="mt-2 block w-full rounded-lg border border-border bg-canvas px-3 py-3 text-text-primary focus:outline-accent" />
          </label>
          <div><p className="text-sm text-text-secondary">Email</p><p className="mt-2 break-all text-text-primary">{user.email || "No email provided"}</p><p className="mt-1 text-xs text-text-tertiary">{user.emailVerified ? "Email verified" : "Email not verified"}</p></div>
          <div><p className="text-sm text-text-secondary">Sign-in method</p><p className="mt-2 text-text-primary">{user.providerData.map(p => ({"google.com":"Google","github.com":"GitHub",password:"Email and password"}[p.providerId] || p.providerId)).join(", ") || "Firebase"}</p></div>
          <Button type="submit" disabled={busy}>{busy ? "Please wait..." : "Save profile"}</Button>
        </form>
        {message && <p role="status" className="mt-4 text-sm text-success">{message}</p>}
        {error && <p role="alert" className="mt-4 text-sm text-critical">{error}</p>}
      </section>
      <section className="rounded-xl border border-border bg-surface p-6">
        <h2 className="flex items-center gap-2 text-text-primary"><ShieldCheck size={18} /> Your session</h2>
        <p className="mt-3 mb-5 text-sm text-text-secondary">You stay signed in on this browser between visits. Log out when you are finished on a shared device.</p>
        <Button variant="danger" icon={<LogOut size={16} />} disabled={busy} onClick={() => void logout()}>Log out</Button>
      </section>
    </div>
  </PageContainer>;
}
