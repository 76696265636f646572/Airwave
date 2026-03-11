import { computed, onUnmounted, ref, watch } from "vue";

import { usePlaybackState } from "./usePlaybackState";

/**
 * Shared local playback over a single audio element. Call from the component that owns the element (e.g. App.vue).
 * @param {import('vue').Ref<HTMLAudioElement | null>} audioRef
 */
export function useLocalPlayback(audioRef) {
  const { playbackState } = usePlaybackState();
  const wantsLocalPlayback = ref(false);

  const isLocalPlaybackActive = computed(() => wantsLocalPlayback.value);

  async function startLocalPlayback() {
    if (!audioRef.value || !playbackState.value.stream_url) return;

    wantsLocalPlayback.value = true;
    audioRef.value.src = playbackState.value.stream_url;

    try {
      await audioRef.value.play();
    } catch {
      stopLocalPlayback();
    }
  }

  function stopLocalPlayback() {
    if (!audioRef.value) return;

    wantsLocalPlayback.value = false;

    audioRef.value.pause();
    audioRef.value.removeAttribute("src");
    audioRef.value.load();
  }

  watch(
    () => playbackState.value.stream_url,
    async (newUrl) => {
      if (!newUrl) {
        stopLocalPlayback();
        return;
      }

      if (!wantsLocalPlayback.value || !audioRef.value) return;

      audioRef.value.src = newUrl;

      try {
        await audioRef.value.play();
      } catch {
        stopLocalPlayback();
      }
    }
  );

  onUnmounted(() => {
    stopLocalPlayback();
  });

  return {
    startLocalPlayback,
    stopLocalPlayback,
    isLocalPlaybackActive,
  };
}
