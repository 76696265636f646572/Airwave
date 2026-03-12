<template>
  <div>
    <h2 class="text-2xl font-bold">Cookies</h2>
    <p class="mt-1 text-sm text-muted">
      Configure cookies for providers to access age-restricted, region-locked, or logged-in-only content.
      Paste Netscape-format cookie content or a file path. Values are stored securely and never exposed.
    </p>

    <div v-if="loading" class="mt-6 text-sm text-muted">Loading...</div>
    <div v-else-if="errorMessage" class="mt-6 text-sm text-red-400">{{ errorMessage }}</div>

    <div v-else class="mt-6 space-y-6">
      <div
        v-for="provider in providers"
        :key="provider.id"
        class="rounded-lg border border-neutral-700 p-4 surface-panel"
      >
        <div class="font-medium">{{ provider.label }}</div>
        <p class="mt-1 text-sm text-muted">{{ provider.description }}</p>

        <div v-if="provider.configured" class="mt-4">
          <div class="flex items-center gap-2 text-sm text-emerald-500">
            <span>Cookie configured</span>
          </div>
          <div class="mt-2 flex gap-2">
            <UButton variant="soft" color="neutral" size="sm" label="Replace" @click="startEdit(provider)" />
            <UButton variant="ghost" color="neutral" size="sm" label="Reset" @click="confirmReset(provider)" />
          </div>
        </div>

        <div v-else class="mt-4">
          <label :for="`cookies-${provider.id}`" class="block text-sm font-medium">Cookie value</label>
          <textarea
            :id="`cookies-${provider.id}`"
            v-model="provider.inputValue"
            class="mt-2 h-32 w-full rounded-md border px-3 py-2 text-sm font-mono surface-input"
            placeholder="Paste Netscape cookie content or enter a file path..."
            spellcheck="false"
          />
          <UButton
            class="mt-2"
            size="sm"
            :loading="saving === provider.id"
            :disabled="!provider.inputValue?.trim()"
            label="Save"
            @click="saveProvider(provider)"
          />
        </div>

        <div v-if="editingProvider?.id === provider.id" class="mt-4 rounded border border-neutral-600 p-4">
          <label :for="`cookies-edit-${provider.id}`" class="block text-sm font-medium">New cookie value</label>
          <textarea
            :id="`cookies-edit-${provider.id}`"
            v-model="provider.inputValue"
            class="mt-2 h-32 w-full rounded-md border px-3 py-2 text-sm font-mono surface-input"
            placeholder="Paste Netscape cookie content or enter a file path..."
            spellcheck="false"
          />
          <div class="mt-2 flex gap-2">
            <UButton
              size="sm"
              :loading="saving === provider.id"
              :disabled="!provider.inputValue?.trim()"
              label="Save"
              @click="saveProvider(provider)"
            />
            <UButton variant="ghost" color="neutral" size="sm" label="Cancel" @click="cancelEdit(provider)" />
          </div>
        </div>
      </div>
    </div>

    <UModal v-model:open="resetModalOpen" :ui="{ width: 'max-w-sm' }">
      <template #content>
        <div class="p-4">
          <h3 class="text-lg font-semibold">Reset cookies</h3>
          <p class="mt-2 text-sm text-muted">
            Remove the cookie configuration for {{ pendingReset?.label }}? This cannot be undone.
          </p>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" color="neutral" @click="resetModalOpen = false">Cancel</UButton>
            <UButton color="primary" :loading="saving === pendingReset?.id" @click="doReset">Reset</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchJson } from "../../composables/useApi";

const PROVIDER_DEFS = [
  { id: "youtube", label: "YouTube", description: "For youtube.com and youtu.be URLs." },
  // Add more providers here later, e.g.:
  // { id: "soundcloud", label: "SoundCloud", description: "For soundcloud.com URLs." },
];

const providers = ref(
  PROVIDER_DEFS.map((p) => ({
    ...p,
    configured: false,
    inputValue: "",
  }))
);

const loading = ref(true);
const errorMessage = ref("");
const saving = ref("");
const editingProvider = ref(null);
const resetModalOpen = ref(false);
const pendingReset = ref(null);

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const data = await fetchJson("/api/settings/cookies");
    const configured = data.providers || {};
    for (const p of providers.value) {
      p.configured = !!configured[p.id];
      p.inputValue = "";
    }
  } catch (e) {
    errorMessage.value = e?.message || "Failed to load cookie settings.";
  } finally {
    loading.value = false;
  }
}

function startEdit(provider) {
  editingProvider.value = provider;
  provider.inputValue = "";
}

function cancelEdit(provider) {
  editingProvider.value = null;
  provider.inputValue = "";
}

function confirmReset(provider) {
  pendingReset.value = provider;
  resetModalOpen.value = true;
}

async function saveProvider(provider) {
  const value = provider.inputValue?.trim();
  if (!value) return;
  saving.value = provider.id;
  errorMessage.value = "";
  try {
    await fetch("/api/settings/cookies", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: provider.id, value }),
    });
    provider.configured = true;
    provider.inputValue = "";
    editingProvider.value = null;
  } catch (e) {
    errorMessage.value = e?.message || `Failed to save ${provider.label} cookies.`;
  } finally {
    saving.value = "";
  }
}

async function doReset() {
  if (!pendingReset.value) return;
  const provider = pendingReset.value;
  saving.value = provider.id;
  errorMessage.value = "";
  try {
    await fetchJson(`/api/settings/cookies/${encodeURIComponent(provider.id)}`, {
      method: "DELETE",
    });
    provider.configured = false;
    provider.inputValue = "";
    resetModalOpen.value = false;
    pendingReset.value = null;
  } catch (e) {
    errorMessage.value = e?.message || `Failed to reset ${provider.label} cookies.`;
  } finally {
    saving.value = "";
  }
}

onMounted(load);
</script>
