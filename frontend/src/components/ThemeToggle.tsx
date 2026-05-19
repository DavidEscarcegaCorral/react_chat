import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function ThemeToggle() {
  const { isDark, toggleDark } = useTheme();

  return (
    <button
      onClick={toggleDark}
      className="fixed top-4 right-4 z-50 p-2 rounded-full bg-white/70 dark:bg-gray-800/70 backdrop-blur shadow-lg hover:scale-110 transition-transform"
      aria-label={isDark ? 'Activar modo claro' : 'Activar modo oscuro'}
    >
      {isDark ? (
        <SunIcon className="h-6 w-6 text-yellow-400" />
      ) : (
        <MoonIcon className="h-6 w-6 text-blue-gray-900 dark:text-gray-100" />
      )}
    </button>
  );
}
