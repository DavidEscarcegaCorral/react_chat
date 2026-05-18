import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Card, Input, Button } from '@material-tailwind/react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const validateUsername = (name: string): string | null => {
    if (!name.trim()) return 'El usuario no puede estar vacio';
    if (name.trim().length < 3) return 'El usuario debe tener al menos 3 caracteres';
    if (name.trim().length > 20) return 'El usuario no puede tener mas de 20 caracteres';
    if (!/^[a-zA-Z0-9]+$/.test(name)) return 'Solo letras y numeros';
    return null;
  };

  const validatePassword = (pass: string): string | null => {
    if (!pass) return 'La contrasena no puede estar vacia';
    if (pass.length < 6) return 'La contrasena debe tener al menos 6 caracteres';
    return null;
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    const usernameError = validateUsername(username);
    if (usernameError) {
      setError(usernameError);
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (isRegisterMode) {
      if (password !== confirmPassword) {
        setError('Las contrasenas no coinciden');
        return;
      }
    }

    setLoading(true);

    try {
      if (isRegisterMode) {
        await register(username.trim(), password);
        setIsRegisterMode(false);
        setError('');
        alert('Registro exitoso. Ahora puedes iniciar sesion.');
      } else {
        const trimmed = username.trim();
        await login(trimmed, password);
        const adminUser = import.meta.env.VITE_ADMIN_USERNAME || 'admin';
        navigate(trimmed === adminUser ? '/server' : '/chat');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error de conexion';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative grid min-h-[100vh] w-screen p-8">
      <div className="flex flex-col-reverse items-center justify-between gap-4 self-start md:flex-row">
        <Card className="h-max w-max flex-row items-center border border-blue-gray-50 py-4 px-5 shadow-lg shadow-blue-gray-900/5">
          <img src="/itson.png" alt="Itson Logo" className="mr-6 h-10" />
          <code className="text-blue-gray-900">
            Redes <strong>8:30 Martes/Jueves</strong>
          </code>
        </Card>
        <Card className="h-max w-max border border-blue-gray-50 font-semibold text-blue-gray-900 shadow-lg shadow-blue-gray-900/5">
          <div className="py-4 pl-4 pr-5">Carlos Alberto Gonzalez Vega</div>
        </Card>
      </div>

      <div className="flex-col gap-2 pt-32 pb-40 text-center">
        <Typography variant="h1" color="blue-gray" className="text-6xl">
          {isRegisterMode ? 'Crear Cuenta' : 'ING-CHAT'}
        </Typography>
        <Typography variant="lead" color="blue-gray" className="opacity-70 text-xl mt-2">
          {isRegisterMode
            ? 'Ingresa un nombre de usuario y contrasena para registrarte'
            : 'Ingresa tu nombre y contraseña para identificarte'}
        </Typography>

        <form onSubmit={handleSubmit} className="mt-8">
          <div className="flex flex-col gap-4 w-80 mx-auto">
            <Input
              label="Usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              maxLength={20}
              disabled={loading}
            />
            <Input
              type="password"
              label="Contrasena"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            {isRegisterMode && (
              <Input
                type="password"
                label="Confirmar Contrasena"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
              />
            )}
          </div>

          {error && <div className="mt-4 text-red-600 text-sm">{error}</div>}

          <div className="mx-auto mt-6 flex flex-col gap-3">
            <Button type="submit" className="w-48" disabled={loading}>
              {loading ? 'Cargando...' : isRegisterMode ? 'Registrarse' : 'Iniciar Sesion'}
            </Button>
            <Button
              type="button"
              variant="text"
              onClick={() => {
                setIsRegisterMode(!isRegisterMode);
                setError('');
                setConfirmPassword('');
              }}
              disabled={loading}
            >
              {isRegisterMode ? 'Ya tienes cuenta? Inicia sesion' : 'No tienes cuenta? Registrate'}
            </Button>
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 gap-4 self-end md:grid-cols-2 lg:grid-cols-4">
        <Card
          shadow={false}
          className="animate-pulse-slow border border-blue-gray-50 py-4 px-5 shadow-xl shadow-transparent"
        >
          <Typography variant="h5" color="blue-gray" className="mb-3 flex items-center gap-3">
            Autenticacion Segura
          </Typography>
          <Typography color="blue-gray" className="font-normal opacity-70">
            Sistema de login con verificacion de credenciales y gestion de sesiones seguras.
          </Typography>
        </Card>
        <Card
          shadow={false}
          className="delay-100 animate-pulse-slow border border-blue-gray-50 py-4 px-5 shadow-xl shadow-transparent"
        >
          <Typography variant="h5" color="blue-gray" className="mb-3 flex items-center gap-3">
            Cifrado RSA
          </Typography>
          <Typography color="blue-gray" className="font-normal opacity-70">
            Comunicacion protegida con criptografia asimetrica RSA-2048.
          </Typography>
        </Card>
        <Card
          shadow={false}
          className="delay-300 animate-pulse-slow border border-blue-gray-50 py-4 px-5 shadow-xl shadow-transparent"
        >
          <Typography variant="h5" color="blue-gray" className="mb-3 flex items-center gap-3">
            Registro de Eventos
          </Typography>
          <Typography color="blue-gray" className="font-normal opacity-70">
            Bitacora completa de actividades del sistema con logs detallados.
          </Typography>
        </Card>
        <Card
          shadow={false}
          className="delay-500 animate-pulse-slow border border-blue-gray-50 py-4 px-5 shadow-xl shadow-transparent"
        >
          <Typography variant="h5" color="blue-gray" className="mb-3 flex items-center gap-3">
            Contrasenas Seguras
          </Typography>
          <Typography color="blue-gray" className="font-normal opacity-70">
            Almacenamiento de contrasenas con hash bcrypt para maxima seguridad.
          </Typography>
        </Card>
      </div>
    </div>
  );
}
