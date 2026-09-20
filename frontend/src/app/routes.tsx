import { PublicLayout } from "@/components/layout/PublicLayout";
import { Profile } from "@/pages/Profile/Profile";
import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard/Dashboard";
import { FindingDetails } from "@/pages/FindingDetails/FindingDetails";
import { Findings } from "@/pages/Findings/Findings";
import { NewScan } from "@/pages/NewScan/NewScan";
import { ScanDetails } from "@/pages/Scan/ScanDetails";
import Login from "@/pages/Login/Login";
import Landing from "@/pages/Landing/Landing";
import { ProtectedLayout } from "@/components/layout/ProtectedLayout";

export const router = createBrowserRouter([
  { element: <PublicLayout />, children: [
    { path: "/", element: <Landing /> },
    { path: "/login", element: <Login /> },
  ] },
  {
    element: <ProtectedLayout />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/dashboard", element: <Dashboard /> },
          { path: "/profile", element: <Profile /> },
          { path: "/scans/new", element: <NewScan /> },
          { path: "/scans/:scanId", element: <ScanDetails /> },
          { path: "/findings", element: <Findings /> },
          { path: "/findings/:findingId", element: <FindingDetails /> },
        ],
      },
    ],
  },
]);
