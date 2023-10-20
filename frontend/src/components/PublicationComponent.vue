<template>
  <Card class="element_card flex flex-column align-items-center sm:align-items-start gap-3">
    <template #title> 
      {{ content.title }}
    </template>
    <template #content>
      <p class="overflow-y-auto max-h-12rem w-full">
        {{ content.abstract }}
      </p>
      <div class="w-full block">
        <span class="inline w-full">
          <Tag class="mx-2" value="Publication" severity="warning">
          </Tag>
          <!-- TODO style keywords - make them clickable -->
          <span v-for="keyword in content.keywords" :key="keyword" class="mx-1">
          <Tag class="" :value="keyword">
          </Tag>
          </span>
          <!-- TODO display EO objects -->
        </span>
      </div>
    </template>
  </Card>
</template>


<script>

import Card from 'primevue/card';
import Tag from 'primevue/tag';

export default {

  components: {
    Card, 
    Tag, 
  }, 
  props: {
    content: Object, 
  }, 
}

</script>

