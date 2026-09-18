import { RouterProvider } from "react-router-dom";
import { onAuthStateChanged } from "firebase/auth";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { AppProviders } from "./providers";
import { router } from "./routes";
import { firebaseAuth, firebaseConfigured } from "@/lib/firebase";

function AuthGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(!firebaseConfigured);

  useEffect(() => {
    if (!firebaseAuth) return;
    return onAuthStateChanged(firebaseAuth, () => setReady(true));
  }, []);

  if (!ready) return <div className="min-h-screen bg-black" />;
  return <>{children}</>;
}

export function App() {
  return (
    <AppProviders>
      <AuthGate>
        <RouterProvider router={router} />
      </AuthGate>
    </AppProviders>
  );
}
