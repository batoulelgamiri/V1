import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { AnalysisDetailPage } from './pages/AnalysisDetailPage'
import { AnalysisHistoryPage } from './pages/AnalysisHistoryPage'
import { DashboardPage } from './pages/DashboardPage'
import { ManualAnalysisPage } from './pages/ManualAnalysisPage'
import { SettingsPage } from './pages/SettingsPage'
import { WazuhDetectionsPage } from './pages/WazuhDetectionsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="analyze" element={<ManualAnalysisPage />} />
        <Route path="wazuh" element={<WazuhDetectionsPage />} />
        <Route path="history" element={<AnalysisHistoryPage />} />
        <Route path="analyses/:analysisId" element={<AnalysisDetailPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

