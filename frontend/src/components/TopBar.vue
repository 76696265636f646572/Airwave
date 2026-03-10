<template>
  <header class="rounded-xl border border-neutral-700 p-3 surface-panel">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
      <h1 class="text-2xl font-bold leading-tight">MyTube Radio</h1>
      <div class="flex w-full flex-col gap-2 sm:ml-auto sm:w-auto sm:flex-row sm:flex-wrap sm:justify-end">
        <UButton
          type="button"
          color="neutral"
          variant="ghost"
          icon="i-lucide-house"
          class="self-start sm:self-auto"
          @click="router.push('/')"
        />
        <UButton
          type="button"
          color="neutral"
          variant="ghost"
          icon="i-lucide-settings"
          class="self-start sm:self-auto"
          @click="router.push('/settings')"
        />
        <input
          :value="searchText"
          type="search"
          placeholder="Search enabled sources"
          class="h-10 w-full min-w-0 rounded-md border px-3 text-sm sm:w-[320px] surface-input"
          @input="onSearchTextChange($event.target.value)"
          @keydown.enter.prevent="onSearch(router, route, searchText)"
        />
        <UButton
          type="button"
          color="primary"
          variant="solid"
          size="md"
          class="self-start sm:self-auto"
          @click="onSearch(router, route, searchText)"
        >
          Search
        </UButton>
      </div>
    </div>

    <form class="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center" @submit.prevent="runSelectedAction">
      <input
        v-model="urlInput"
        type="url"
        placeholder="Paste any supported video, playlist, or live stream URL"
        required
        class="h-10 w-full min-w-0 flex-1 rounded-md border px-3 text-sm surface-input"
      />
      <div class="flex w-full items-center gap-0 sm:w-auto">
        <UButton
          type="button"
          color="primary"
          variant="solid"
          size="md"
          class="flex-1 rounded-r-none sm:flex-none"
          @click="runSelectedAction"
        >
          {{ urlActionLabel }}
        </UButton>
        <UDropdownMenu :items="urlActionDropdownItems">
          <UButton
            type="button"
            color="neutral"
            variant="outline"
            size="md"
            icon="i-lucide-chevron-down"
            class="rounded-l-none border-l-0 px-2"
            aria-label="Other actions"
          />
        </UDropdownMenu>
      </div>
    </form>

  </header>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { canonicalCollectionUrl, classifyCollectionUrl, collectionActionLabels } from "../composables/collectionUrl";
import { useLibraryState } from "../composables/useLibraryState";
import { useUiState } from "../composables/useUiState";

const BASE_ACTIONS = {
  play: { id: "play", label: "Play" },
  addUrl: { id: "addUrl", label: "Add URL" },
};

const urlInput = ref("");
const selectedUrlAction = ref("play");
const router = useRouter();
const route = useRoute();
const { addUrl, playUrl, importPlaylistUrl, queue } = useLibraryState();
const { searchText, onSearchTextChange, onSearch } = useUiState();

const collectionInfo = computed(() => classifyCollectionUrl(urlInput.value));
const collectionLabels = computed(() => collectionActionLabels(collectionInfo.value));

/** Available actions for current URL type. */
const availableUrlActions = computed(() => {
  if (collectionInfo.value.isCollection) {
    return [
      BASE_ACTIONS.play,
      BASE_ACTIONS.addUrl,
      { id: "queueCollection", label: collectionLabels.value.queue },
      { id: "playCollection", label: collectionLabels.value.play },
      { id: "importCollection", label: collectionLabels.value.import },
    ];
  }
  return [BASE_ACTIONS.play, BASE_ACTIONS.addUrl];
});

/** Default action when queue has items: show queue action (Add URL / Queue collection); otherwise Play. */
const defaultUrlAction = computed(() => {
  const actions = availableUrlActions.value;
  const ids = actions.map((a) => a.id);
  if (queue.value.length > 0) {
    if (ids.includes("queueCollection")) return "queueCollection";
    if (ids.includes("addUrl")) return "addUrl";
  }
  return "play";
});

/** Keep selected action in the available list; when queue has items, prefer the queue action as default. */
watch(
  [availableUrlActions, defaultUrlAction],
  ([actions, defaultAction]) => {
    const ids = actions.map((a) => a.id);
    if (!ids.includes(selectedUrlAction.value)) {
      selectedUrlAction.value = defaultAction;
    } else if (selectedUrlAction.value === "play" && defaultAction !== "play") {
      selectedUrlAction.value = defaultAction;
    }
  },
  { immediate: true }
);

const urlActionLabel = computed(() => {
  const action = availableUrlActions.value.find((a) => a.id === selectedUrlAction.value);
  return action?.label ?? "Play";
});

const urlActionDropdownItems = computed(() =>
  availableUrlActions.value.map((action) => ({
    label: action.label,
    onSelect: () => {
      runAction(action.id);
      selectedUrlAction.value = action.id;
    },
  }))
);

function runAction(actionId) {
  switch (actionId) {
    case "play":
      emitPlayUrl();
      break;
    case "addUrl":
      emitAddUrl();
      break;
    case "queueCollection":
      emitQueueUrl();
      break;
    case "playCollection":
      emitPlayPlaylist();
      break;
    case "importCollection":
      emitImportPlaylist();
      break;
    default:
      emitPlayUrl();
  }
}

function runSelectedAction() {
  runAction(selectedUrlAction.value);
}

function getImportPlaylistUrl(url) {
  return canonicalCollectionUrl(url);
}

function consumeInputUrl() {
  const url = urlInput.value.trim();
  if (!url) return null;
  urlInput.value = "";
  return url;
}

function emitImportPlaylist() {
  const url = consumeInputUrl();
  if (!url) return;
  const importUrl = getImportPlaylistUrl(url);
  if (!importUrl) return;
  importPlaylistUrl(importUrl);
}

function emitQueueUrl() {
  const url = consumeInputUrl();
  if (!url) return;
  const urlToAdd = getImportPlaylistUrl(url) ?? url;
  addUrl(urlToAdd);
}

/** Queue the URL as a single item, even when collection actions are available. */
function emitAddUrl() {
  const url = consumeInputUrl();
  if (!url) return;
  addUrl(url);
}

/** Play the full collection URL when available. */
function emitPlayPlaylist() {
  const url = consumeInputUrl();
  if (!url) return;
  const playlistUrl = getImportPlaylistUrl(url) ?? url;
  playUrl(playlistUrl);
}

function emitPlayUrl() {
  const url = consumeInputUrl();
  if (!url) return;
  playUrl(url);
}
</script>
