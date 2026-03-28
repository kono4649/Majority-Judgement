import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Navbar from './components/Navbar/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home/Home'
import Login from './pages/Login/Login'
import Register from './pages/Register/Register'
import Dashboard from './pages/Dashboard/Dashboard'
import CreatePoll from './pages/CreatePoll/CreatePoll'
import EditPoll from './pages/EditPoll/EditPoll'
import Results from './pages/Results/Results'
import VotePage from './pages/VotePage/VotePage'
import ThanksPage from './pages/ThanksPage/ThanksPage'

function AppRoutes() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-center" style={{ minHeight: '100vh' }}>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Home />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login"    element={<Login />} />
        <Route
          path="/dashboard"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
        />
        <Route
          path="/polls/create"
          element={<ProtectedRoute><CreatePoll /></ProtectedRoute>}
        />
        <Route
          path="/polls/:id/edit"
          element={<ProtectedRoute><EditPoll /></ProtectedRoute>}
        />
        <Route
          path="/polls/:id/results"
          element={<ProtectedRoute><Results /></ProtectedRoute>}
        />
        <Route path="/vote/:publicId"        element={<VotePage />} />
        <Route path="/vote/:publicId/thanks" element={<ThanksPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <footer>
        <div className="container">投票アプリ &copy; {new Date().getFullYear()}</div>
      </footer>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
