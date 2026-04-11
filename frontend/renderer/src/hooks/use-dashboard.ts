// frontend/src/hooks/use-dashboard.ts
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

// Fetch summary statistics for the dashboard
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboardStats"],
    queryFn: async () => {
      const res = await axios.get("http://localhost:8000/api/dashboard/stats");
      return res.data;
    },
  });
}

// Fetch real-time system status (polling every 5 seconds)
export function useSystemStatus() {
  return useQuery({
    queryKey: ["systemStatus"],
    queryFn: async () => {
      const res = await axios.get("http://localhost:8000/api/dashboard/status");
      return res.data;
    },
    refetchInterval: 5000, // Poll every 5 seconds
  });
}
