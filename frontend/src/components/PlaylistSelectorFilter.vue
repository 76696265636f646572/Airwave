<template>
  <div class="flex items-center gap-2 px-2 py-1.5">
    <UIcon name="i-lucide-search" class="size-4 shrink-0 text-muted" />
    <input
      :model-value="modelValue"
      type="text"
      :placeholder="placeholder"
      class="min-w-0 flex-1 rounded-md border-0 bg-transparent px-2 py-1 text-sm placeholder-neutral-500 focus:outline-none focus:ring-0"
      @update:model-value="$emit('update:modelValue', $event)"
      @click.stop
      @keydown.stop
      @keyup.stop
      @keypress.stop
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  placeholder: {
    type: String,
    default: "Find a playlist",
  },
});
defineEmits(["update:modelValue"]);
</script>
