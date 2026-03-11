import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderOpen,
  Bot,
  Briefcase,
  Compass,
  Search,
  MessageSquare,
  Building2,
  Settings,
  Boxes,
  ChevronDown,
  LogOut,
  BarChart3,
} from 'lucide-react'
import { useAuthStore } from '../store/auth'

const navItems: { to: string; label: string; icon: React.ElementType }[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/ask', label: 'Ask', icon: MessageSquare },
  { to: '/explorer', label: 'Knowledge', icon: Compass },
  { to: '/sources', label: 'Sources', icon: FolderOpen },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/dashboards', label: 'Dashboards', icon: BarChart3 },
  { to: '/workspaces', label: 'Workspaces', icon: Building2 },
  { to: '/models', label: 'Models', icon: Boxes },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Layout() {
  const { user, clearAuth, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  if (!isAuthenticated()) return null

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased">
      <header className="border-b border-slate-800/80 sticky top-0 z-40 bg-slate-950/90 backdrop-blur-sm">
        <div className="flex items-center justify-between px-5 py-3.5 max-w-[1680px] mx-auto w-full">
          <div className="flex items-center gap-10">
            <NavLink
              to="/"
              className="font-semibold text-lg tracking-tight text-slate-100 hover:text-white transition-colors shrink-0"
            >
              MeshMind
            </NavLink>
            <nav className="flex items-center gap-0.5 overflow-x-auto scrollbar-thin pb-1 -mb-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" aria-hidden />
                  <span className="hidden sm:inline whitespace-nowrap">{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 text-slate-300 text-sm">
              <span>{user?.username ?? 'User'}</span>
              <ChevronDown className="w-4 h-4 opacity-70" aria-hidden />
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
              title="Log out"
              aria-label="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 px-6 py-8 max-w-[1680px] mx-auto w-full">
        <Outlet />
      </main>
    </div>
  )
}
