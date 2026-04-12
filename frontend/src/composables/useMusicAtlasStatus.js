import { ref } from "vue";

import { fetchJson } from "./useApi";

const musicAtlasEnabled = ref(false);
const musicAtlasStatusLoaded = ref(false);
let loadPromise = null;

/**
 * One-shot probe: GET /api/musicatlas/suggestions with dummy params.
 * When MusicAtlas is disabled, the API returns 200 with enabled: false (no upstream call).
 */
export async function ensureMusicAtlasStatusLoaded() {
  if (musicAtlasStatusLoaded.value) return;
  if (loadPromise) {
    await loadPromise;
    return;
  }
  loadPromise = (async () => {
    try {
      const params = new URLSearchParams({
        artist: "_airwave_probe",
        track: "_airwave_probe",
      });
      const body = await fetchJson(`/api/musicatlas/suggestions?${params.toString()}`);
      musicAtlasEnabled.value = !!body?.enabled;
    } catch {
      musicAtlasEnabled.value = false;
    } finally {
      musicAtlasStatusLoaded.value = true;
      loadPromise = null;
    }
  })();
  await loadPromise;
}

export function useMusicAtlasStatus() {
  return {
    musicAtlasEnabled,
    musicAtlasStatusLoaded,
    ensureMusicAtlasStatusLoaded,
  };
}
