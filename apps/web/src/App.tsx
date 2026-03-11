import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Login } from './pages/Login'
import { Overview } from './pages/Overview'
import { SearchPage } from './pages/Search'
import { AskPage } from './pages/Ask'
import { KnowledgeExplorerPage } from './pages/KnowledgeExplorer'
import { SourcesPage } from './pages/Sources'
import { SourceDetailPage } from './pages/SourceDetail'
import { AddSourcePage } from './pages/AddSource'
import { AgentsPage } from './pages/Agents'
import { AgentDetailPage } from './pages/AgentDetail'
import { JobsPage } from './pages/Jobs'
import { JobDetailPage } from './pages/JobDetail'
import { WorkspacesPage } from './pages/Workspaces'
import { ModelsPage } from './pages/Models'
import { SettingsPage } from './pages/Settings'
import { DashboardsPage } from './pages/Dashboards'
import { DashboardDetailPage } from './pages/DashboardDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="ask" element={<AskPage />} />
          <Route path="explorer" element={<KnowledgeExplorerPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="sources/add" element={<AddSourcePage />} />
          <Route path="sources/:id" element={<SourceDetailPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="agents/:id" element={<AgentDetailPage />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="jobs/:id" element={<JobDetailPage />} />
          <Route path="workspaces" element={<WorkspacesPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="dashboards" element={<DashboardsPage />} />
          <Route path="dashboards/:id" element={<DashboardDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
