import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard/Dashboard'
import { FindingDetails } from '@/pages/FindingDetails/FindingDetails'
import { Findings } from '@/pages/Findings/Findings'
import { NewScan } from '@/pages/NewScan/NewScan'
import { ScanDetails } from '@/pages/Scan/ScanDetails'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'scans/new', element: <NewScan /> },
      { path: 'scans/:scanId', element: <ScanDetails /> },
      { path: 'findings', element: <Findings /> },
      { path: 'findings/:findingId', element: <FindingDetails /> },
    ],
  },
])
