const DEFAULT_API_BASE_URL = "https://profpilot.onrender.com";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL || DEFAULT_API_BASE_URL;
