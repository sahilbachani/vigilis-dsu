import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { useLocation } from "wouter";

interface User {
  id: number;
  username: string;
  role: string;
  token: string;
}

export function useLogin() {
  const [, setLocation] = useLocation();

  return useMutation({
    mutationFn: async (credentials: { username: string; password: string }) => {
      const response = await axios.post<User>(
        "http://localhost:8000/api/auth/login", // matches FastAPI
        credentials,
        { headers: { "Content-Type": "application/json" } }
        );

      return response.data;
    },
    onSuccess: (user) => {
      localStorage.setItem("vigilis_user", JSON.stringify(user));
      setLocation("/dashboard"); // redirect after login
    },
    onError: (error: any) => {
      // This will bubble up to Login.tsx onError
      throw error.response?.data || error;
    },
  });
}

export function useLogout() {
  const [, setLocation] = useLocation();
  return () => {
    localStorage.removeItem("vigilis_user");
    setLocation("/");
  };
}

export function useUser(): User | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("vigilis_user");
  if (!userStr) return null;

  try {
    const parsed = JSON.parse(userStr);
    if (parsed && parsed.token) return parsed;
    return null;
  } catch {
    return null;
  }
}
