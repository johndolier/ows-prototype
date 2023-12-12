
<template>
  <Card class="element-card flex flex-column w-full">
    <template #title>
      <PButton 
        v-if="content.is_html" 
        v-html="content.title" 
        :label="content.title" 
        link 
        @click="openLink(content.url)" 
      />
      <PButton 
        v-else 
        :label="content.title" 
        link 
        @click="openLink(content.url)"
      >
        {{ content.title }}
      </PButton>
    </template>
    <template #content>
      <p 
        v-if="content.is_html" 
        class="overflow-y-auto w-full" 
        v-html="content.text"
      >
      </p>
      <p v-else class="overflow-y-auto w-full">
        {{ content.text }}
      </p>
      <div class="">
        <span class="w-full">
          <Tag 
            class="mx-2" 
            value="Web Document" 
            severity="warning"
          />
        </span>
      </div>
    </template>
  </Card>     
</template>

<script>

import Card from 'primevue/card';
import Tag from 'primevue/tag';

export default {

  name: "WebDocumentComponent", 
  
  components: {
    Card, 
    Tag, 
  }, 
  props: {
    content: Object, 
  }, 
}

</script>
