import { BrowserRouter, Routes, Route, NavLink, Outlet } from 'react-router-dom'

function Layout() {
  const navItems = [
    { to: '/', label: 'Dashboard' },
    { to: '/ask', label: 'Ask' },
    { to: '/search', label: 'Search' },
    { to: '/sources', label: 'Sources' },
    { to: '/jobs', label: 'Jobs' },
    { to: '/admin', label: 'Admin' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <nav className="border-b border-slate-700 px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-lg">MeshMind v2</span>
          <ul className="flex gap-4">
            {navItems.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `px-3 py-1 rounded ${isActive ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}`
                  }
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{title}</h1>
      <p className="text-slate-400">Placeholder — coming soon</p>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Placeholder title="Dashboard" />} />
          <Route path="ask" element={<Placeholder title="Ask" />} />
          <Route path="search" element={<Placeholder title="Search" />} />
          <Route path="sources" element={<Placeholder title="Sources" />} />
          <Route path="jobs" element={<Placeholder title="Jobs" />} />
          <Route path="admin" element={<Placeholder title="Admin" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
