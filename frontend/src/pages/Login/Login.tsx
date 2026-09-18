import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { Eye, EyeOff, ArrowUpRight, ShieldCheck, Code2, Globe2 } from "lucide-react";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, updateProfile } from "firebase/auth";
import { firebaseAuth, firebaseConfigured, googleProvider, githubProvider } from "@/lib/firebase";
import { apiClient } from "@/lib/api";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [signup, setSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function authenticate(action: () => Promise<unknown>) {
    if (busy) return;
    setError("");
    if (!firebaseAuth || !firebaseConfigured) { setError("Sign-in is temporarily unavailable."); return; }
    setBusy(true);
    try {
      await action();
      await apiClient.get("/auth/me");
      const from = location.state?.from;
      navigate(typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && from !== "/login" ? from : "/dashboard", { replace:true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in. Please try again.");
    } finally { setBusy(false); }
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    void authenticate(async () => {
      if (signup) {
        const credential = await createUserWithEmailAndPassword(firebaseAuth!, email, password);
        await updateProfile(credential.user, { displayName:name.trim() });
      } else await signInWithEmailAndPassword(firebaseAuth!, email, password);
    });
  }
  const inputClass = "h-12 w-full rounded-xl border border-white/10 bg-white/5 px-4 text-white outline-none placeholder:text-white/25 focus:border-[#d0c2f6] focus:ring-2 focus:ring-[#d0c2f6]/15";
  return <main className="min-h-screen bg-[#090a0b] p-3 text-white lg:grid lg:grid-cols-2 lg:p-5" style={{fontFamily:"'DM Sans', sans-serif"}}>
    <aside className="relative hidden min-h-[calc(100vh-40px)] overflow-hidden rounded-[28px] bg-[#f0eefa] text-[#080909] lg:flex lg:flex-col lg:justify-between lg:p-12">
      <Link to="/" className="relative z-10 flex w-fit items-center gap-2 text-xl"><ShieldCheck size={24}/> TraceGuard</Link>
      <video className="absolute inset-0 h-full w-full object-cover" src="/footer-scrub.mp4" muted playsInline preload="auto" aria-hidden="true" />
      <div className="relative z-10 mt-12 mb-auto"><span className="rounded-full bg-white px-3 py-2 text-xs">Evidence before confidence.</span><h1 className="mt-6 text-5xl leading-[1.08] tracking-tight" style={{fontFamily:"Epilogue, sans-serif",fontWeight:900}}>A clearer view.<br/>A safer build.</h1></div>
      <div className="relative z-10 flex justify-between text-xs"><span>Scan / Correlate / Verify</span><span>Built for your code.</span></div>
    </aside>
    <section className="mx-auto flex min-h-[calc(100vh-24px)] w-full max-w-xl flex-col justify-center px-5 py-12 sm:px-12 lg:px-16">
      <Link to="/" className="mb-12 flex items-center gap-2 text-sm text-white/60"><ShieldCheck size={18}/> TraceGuard <ArrowUpRight size={14}/></Link>
      <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.35}}>
        <p className="mb-3 text-xs uppercase tracking-[.2em] text-[#c8b8eb]">Your security workspace</p>
        <h2 className="text-4xl font-medium tracking-tight">{signup ? "Make yourself at home." : "Welcome back."}</h2>
        <p className="mt-3 mb-8 text-sm leading-6 text-white/45">{signup ? "Create an account to turn scanner output into actionable evidence." : "Sign in to your scans, findings, and verified fixes."}</p>
        <div className="grid grid-cols-2 gap-3">
          <button disabled={busy} onClick={() => void authenticate(() => signInWithPopup(firebaseAuth!,googleProvider))} className="flex h-12 items-center justify-center gap-2 rounded-xl border border-white/15 text-sm hover:bg-white/5 disabled:opacity-50"><Globe2 size={17}/> Google</button>
          <button disabled={busy} onClick={() => void authenticate(() => signInWithPopup(firebaseAuth!,githubProvider))} className="flex h-12 items-center justify-center gap-2 rounded-xl border border-white/15 text-sm hover:bg-white/5 disabled:opacity-50"><Code2 size={17}/> GitHub</button>
        </div>
        <div className="my-7 flex items-center gap-4 text-xs text-white/30"><span className="h-px flex-1 bg-white/10"/>or continue with email<span className="h-px flex-1 bg-white/10"/></div>
        <form onSubmit={submit} className="space-y-5">
          {signup && <label className="block space-y-2 text-sm"><span>Full name</span><input required autoComplete="name" value={name} onChange={e=>setName(e.target.value)} placeholder="Your name" className={inputClass}/></label>}
          <label className="block space-y-2 text-sm"><span>Email</span><input required type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" className={inputClass}/></label>
          <label className="block space-y-2 text-sm"><span>Password</span><span className="relative block"><input required minLength={signup?8:undefined} type={visible?"text":"password"} autoComplete={signup?"new-password":"current-password"} value={password} onChange={e=>setPassword(e.target.value)} placeholder={signup?"At least 8 characters":"Your password"} className={inputClass+" pr-12"}/><button type="button" aria-label={visible?"Hide password":"Show password"} onClick={()=>setVisible(!visible)} className="absolute right-4 top-4 text-white/40">{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button></span></label>
          {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
          <button disabled={busy || !firebaseConfigured} type="submit" className="flex h-13 w-full items-center justify-between rounded-xl bg-[#ded3f5] px-5 text-sm font-semibold text-[#17131e] hover:bg-[#ebe3fa] disabled:opacity-50"><span>{busy?"Connecting?":signup?"Create account":"Sign in"}</span><ArrowUpRight size={19}/></button>
        </form>
        <p className="mt-7 text-center text-sm text-white/40">{signup?"Already have an account?":"New to TraceGuard?"} <button disabled={busy} onClick={()=>{setSignup(!signup);setError("");}} className="text-white underline underline-offset-4">{signup?"Sign in":"Create account"}</button></p>
      </motion.div>
    </section>
  </main>;
}
