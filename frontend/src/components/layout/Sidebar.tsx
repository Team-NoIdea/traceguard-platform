import {
  ExternalLink,
  LayoutGrid,
  Radar,
  UserRound,
  ShieldAlert,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

const PRIMARY_NAV = [
  { to: "/dashboard", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/scans/new", label: "Scans", icon: Radar },
  { to: "/findings", label: "Findings", icon: ShieldAlert },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <svg
          viewBox="0 0 32 32"
          className="h-5 w-5"
          fill="none"
          aria-hidden="true">
          <path
            d="M16 3l11 4v8c0 7-4.6 11.8-11 14-6.4-2.2-11-7-11-14V7l11-4z"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M10 16.5l3.4 3.6L22 11"
            stroke="var(--color-accent)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="font-display text-[15px] font-semibold tracking-tight text-text-primary">
          TraceGuard
        </span>
      </div>

      <nav className="flex flex-1 flex-col justify-between overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {PRIMARY_NAV.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors",
                    isActive
                      ? "bg-accent-soft text-accent"
                      : "text-text-secondary hover:bg-surface-raised hover:text-text-primary",
                  )
                }>
                <Icon size={16} strokeWidth={2} />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>

        <ul className="space-y-1 border-t border-border pt-3">
          <li>
            <NavLink
              to="/profile"
              className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-[13px] font-medium text-text-secondary transition-colors hover:bg-surface-raised hover:text-text-primary">
              <UserRound size={16} strokeWidth={2} />
              Profile
            </NavLink>
          </li>
          <li>
            <a
              href="https://github.com/Team-NoIdea/traceguard-platform"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium text-text-secondary transition-colors hover:bg-surface-raised hover:text-text-primary">
              <ExternalLink size={16} strokeWidth={2} />
              GitHub
            </a>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
