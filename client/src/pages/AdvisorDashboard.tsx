import { User } from '../App'

interface Props {
  user: User
  onLogout: () => void
}

export default function AdvisorDashboard({ user, onLogout }: Props) {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <header className="bg-gray-900 px-6 py-4 flex justify-between items-center border-b border-gray-800">
        <h1 className="text-xl font-bold text-purple-400">AuraWealth — Advisor</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-300">{user.name}</span>
          <button onClick={onLogout} className="text-gray-400 hover:text-white text-sm">
            Sign out
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">
        <h2 className="text-2xl font-semibold mb-4">Command Center</h2>
        <p className="text-gray-400">Advisor dashboard — client list and risk analysis coming soon.</p>
      </main>
    </div>
  )
}
