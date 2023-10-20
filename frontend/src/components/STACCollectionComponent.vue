<template>
  <Card class="flex flex-column align-items-center sm:align-items-start gap-3 text-xs">
    <template #title>
      <!--TODO make title link (details view)-->
      <div class="flex text-base">
        {{ content.title }}
      </div> 
    </template>
    <template #content>
      <div class="inline-block w-8 my-2 mx-3">
        <!--<span class="inline-block align-left w-8">-->
        <Tag class="mx-2" value="STAC Collection" severity="warning">
        </Tag>
        <!-- TODO style keywords - make them clickable -->
        <span v-for="keyword in content.keywords" :key="keyword" class="mx-1">
          <Tag class="" :value="keyword" >
          </Tag>
        </span>
        <p align="left" class="inline-block overflow-y-auto " v-html="content.description"></p>
        <!--</span>-->
      </div>
      <div class="inline-block w-3 mx-auto">
        <PButton 
          label="Request STAC items" @click="submitStacItemQuery" size="small" severity="danger"
          :loading="stacItemsLoading"
          class="my-2">
        </PButton>
        <img class="thumbnail-img" 
          :src="content.assets.thumbnail.href"
        />
      </div>
      <div v-if="stacItemsPresent">
        <PButton label="Show items" @click="showItemsClick" size="small" 
          :icon="showItems ? 'pi pi-angle-double-down' : 'pi pi-angle-double-right' " >
        </PButton>
        <DataView v-if="showItems" :value="stacItemList" :layout="'grid'" :rows="12"
          :paginator="true" class="h-full">
          <template #grid="slotProps">
            <div class="col-12 p-2 w-3">
              <div class="p-2 border-1 surface-border surface-card border-round">
                <img v-if="slotProps.data.img_link" 
                  class="stac-item-img" :src="slotProps.data.img_link" 
                />
                <div v-else>
                  No image available
                </div>
              </div>
            </div>
          </template>
        </DataView>
      </div>
    </template>
  </Card>
</template>


<script>

import Card from 'primevue/card';
import DataView from 'primevue/dataview';
import Tag from 'primevue/tag';

export default {

  components: {
    Card,
    Tag,
    DataView
    }, 
  props: {
    content: Object, 
    stacItems: Object, 
  }, 
  data() {
    return {
      showItems: false,
    }
  }, 

  computed: {
    stacItemList() {
      if (!this.stacItemsPresent) {
        return [];
      }
      for (const entry of this.stacItems[this.content._id]) {
        if (entry.selected) {
          return entry['stac_items'];
        }
      }
      return [];
    }, 
    stacItemsLoading() {
      if (!(this.content._id in this.stacItems)) {
        // no entry with stac collection id
        return false;
      }
      for (const entry of this.stacItems[this.content._id]) {
        // return true if there is at least one entry where 'loading' is true
        if (entry.loading) {
          return true;
        }
      }
      return false;
    }, 
    stacItemsPresent() {
      // TODO adapt function to be correct!
      if (!(this.content._id in this.stacItems)) {
        return false;
      }
      const numEntries = this.stacItems[this.content._id].length;
      if (numEntries <= 0) {
        // no entries -> dont show stac items
        return false;
      }
      else if (numEntries >= 2) {
        // at least two entries -> always show stac items
        return true;
      }
      else {
        // exactly one entry -> check if entry is loading
        return !this.stacItems[this.content._id][0].loading;
      }
    }
  }, 

  methods: {
    submitStacItemQuery() {
      this.$emit('submitStacItemQuery', this.content._id);
    }, 
    showItemsClick() {
      this.showItems = !this.showItems;
    }, 
  }, 
}

</script>

