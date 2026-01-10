/// <reference types="vite/client" />

/**
 * Development-aware logger that only logs in development mode.
 * Errors are always logged for debugging in production.
 */
const isDev = import.meta.env.DEV

export const logger = {
  log: (...args: unknown[]) => isDev && console.log(...args),
  warn: (...args: unknown[]) => isDev && console.warn(...args),
  error: (...args: unknown[]) => console.error(...args), // Always log errors
  debug: (...args: unknown[]) => isDev && console.debug(...args),
  info: (...args: unknown[]) => isDev && console.info(...args),
}
