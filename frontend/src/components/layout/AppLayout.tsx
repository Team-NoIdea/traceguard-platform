import { Outlet } from 'react-router-dom'

import { Sidebar } from './Sidebar'

export function AppLayout() {
  return (
    <div className="flex h-screen bg-canvas">
      <Sidebar />
      <Outlet />
    </div>
  )
}
