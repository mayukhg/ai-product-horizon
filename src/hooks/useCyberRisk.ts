import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "@/services/api";

export function useTriage() {
  return useQuery({
    queryKey: ["cyberrisk", "triage"],
    queryFn: () => api.getTriage(),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useAgentTrajectory(runId = "7f4c-92a1") {
  return useQuery({
    queryKey: ["cyberrisk", "trajectory", runId],
    queryFn: () => api.getAgentTrajectory(runId),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useModelRouting() {
  return useQuery({
    queryKey: ["cyberrisk", "model-routes"],
    queryFn: () => api.getModelRoutes(),
    retry: 1,
    staleTime: 60_000,
  });
}

export function useEvalMetrics() {
  return useQuery({
    queryKey: ["cyberrisk", "evals"],
    queryFn: () => api.getEvalMetrics(),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useRemediateApprove() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.approveRemediation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cyberrisk", "triage"] });
    },
  });
}

export function isBackendOffline(error: unknown) {
  return error instanceof ApiError || error instanceof TypeError;
}
