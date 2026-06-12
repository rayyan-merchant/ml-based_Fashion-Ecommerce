// TanStack Query is not installed in this CRA frontend yet. This lightweight
// placeholder documents the intended cache timings without changing runtime UI.
export const queryDefaults = {
  dashboard: 30000,
  adminTables: 60000,
  mlResults: 300000,
  segments: 600000,
  referenceData: 3600000
};
