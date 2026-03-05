import React from "react";
import { FiSearch, FiBell, FiSettings, FiHelpCircle, FiLogOut } from "react-icons/fi";
import { useAuth } from "../contexts/AuthContext";

function Header({ showScores, toggleScores }) {
  const { user, logout } = useAuth();
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 py-4 px-6 flex justify-between items-center shadow-md flex-shrink-0">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleScores}
          aria-pressed={showScores}
          className="flex items-center text-white font-bold text-xl hover:bg-blue-500 px-4 py-2 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 shadow-sm"
          title={showScores ? "Hide search scores" : "Show search scores"}
        >
          <span>WinSupply</span>
          <span
            className={
              "ml-3 inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm " +
              (showScores
                ? "bg-green-400 text-green-900"
                : "bg-blue-500 text-blue-100")
            }
            aria-hidden="true"
          >
            {showScores ? "Scores ON" : ""}
          </span>
        </button>
      </div>

      <div className="flex items-center gap-3">
        <button
          disabled
          className="p-2.5 rounded-lg opacity-40 cursor-not-allowed"
          aria-label="Notifications"
          title="Notifications (Coming Soon)"
        >
          <FiBell className="w-5 h-5 text-white" />
        </button>

        <button
          disabled
          className="p-2.5 rounded-lg opacity-40 cursor-not-allowed"
          aria-label="Settings"
          title="Settings (Coming Soon)"
        >
          <FiSettings className="w-5 h-5 text-white" />
        </button>

        <button
          disabled
          className="p-2.5 rounded-lg opacity-40 cursor-not-allowed"
          aria-label="Help"
          title="Help (Coming Soon)"
        >
          <FiHelpCircle className="w-5 h-5 text-white" />
        </button>

        <div className="flex items-center gap-3 ml-2 pl-3 border-l border-blue-500">
          {user && (
            <>
              <div className="text-white text-xs font-medium">
                {user.display_name}
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg hover:bg-blue-500 hover:bg-opacity-30 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 transition-all duration-200"
                aria-label="Logout"
                title="Sign out"
              >
                <FiLogOut className="w-5 h-5 text-white" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
