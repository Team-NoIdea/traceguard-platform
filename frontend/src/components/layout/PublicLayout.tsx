import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { firebaseAuth } from "@/lib/firebase";

// AuthGate waits for persisted identity before this route mounts.
export function PublicLayout() {
  const { pathname } = useLocation();
  const [alreadySignedIn] = useState(() => Boolean(firebaseAuth?.currentUser));
  const [signedIn, setSignedIn] = useState(alreadySignedIn);
  useEffect(() => {
    if (!firebaseAuth) return;
    return onAuthStateChanged(firebaseAuth, user => setSignedIn(Boolean(user)));
  }, []);
  // A new sign-in stays on Login until profile synchronization completes.
  const redirect = pathname === "/" ? signedIn : alreadySignedIn;
  return redirect ? <Navigate to="/dashboard" replace /> : <Outlet />;
}
