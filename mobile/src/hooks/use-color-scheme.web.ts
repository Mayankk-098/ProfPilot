import { useColorScheme as useRNColorScheme } from 'react-native';

/**
 * Web color scheme hook.
 *
 * React Native already subscribes to the platform color-scheme preference,
 * so no hydration state update is needed here.
 */
export function useColorScheme() {
  return useRNColorScheme() ?? 'light';
}
