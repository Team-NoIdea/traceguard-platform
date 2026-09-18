import { Navigate, Outlet, useLocation } from "react-router-dom";
import { onAuthStateChanged } from "firebase/auth";
import { useEffect, useState } from "react";

import { firebaseAuth, firebaseConfigured } from "@/lib/firebase";

export function ProtectedLayout() {
  const location = useLocation();
  const [ready, setReady] = useState(!firebaseConfigured);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    if (!firebaseAuth) return;
    return onAuthStateChanged(firebaseAuth, (user) => {
      setSignedIn(Boolean(user));
      setReady(true);
    });
  }, []);

  if (!firebaseConfigured) return <div role="alert" className="min-h-screen bg-black p-8 text-white">Sign-in is unavailable. Configure Firebase to access TraceGuard.</div>;
  if (!ready) return <div className="min-h-screen bg-black" />;
  if (!signedIn)
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
