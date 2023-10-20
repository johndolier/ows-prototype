
<template>
  <Card class="element_card flex flex-column w-full">
    <template #title>
      <PButton v-html="content.title" :label="content.title" link @click="openLink(content.target_uri)">
      </PButton>
    </template>
    <template #content>
      <p class="overflow-y-auto w-full" v-html="content.snippet"></p>
      <div class="">
        <span class="w-full">
          <Tag class="mx-2" value="Web Document" severity="warning">
          </Tag>
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
