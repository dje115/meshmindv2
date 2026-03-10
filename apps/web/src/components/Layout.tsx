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
} from 'lucide-react'
import { useAuthStore } from '../store/auth'

const navItems: { to: string; label: string; icon: React.ElementType; roles?: string[] }[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/ask', label: 'Ask', icon: MessageSquare },
  { to: '/explorer', label: 'Knowledge Explorer', icon: Compass },
  { to: '/sources', label: 'Sources', icon: FolderOpen },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/workspaces', label: 'Workspaces & Permissions', icon: Building2 },
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
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <header className="border-b border-slate-700/50 sticky top-0 z-40 bg-slate-950/95 backdrop-blur">
        <div className="flex items-center justify-between px-4 py-3 max-w-[1600px] mx-auto w-full">
          <div className="flex items-center gap-8">
            <NavLink to="/" className="font-semibold text-lg tracking-tight text-slate-100 hover:text-white">
              MeshMind v2
            </NavLink>
            <nav className="flex items-center gap-1 overflow-x-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent pb-1 -mb-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                      isActive ? 'bg-slate-700/80 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" aria-hidden />
                  <span className="hidden sm:inline">{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800/50 text-slate-300 text-sm">
              <span>{user?.username ?? 'User'}</span>
              <ChevronDown className="w-4 h-4" />
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
              title="Log out"
              aria-label="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 p-6 max-w-[1600px] mx-auto w-full">
        <Outlet />
      </main>
    </div>
  )
}
