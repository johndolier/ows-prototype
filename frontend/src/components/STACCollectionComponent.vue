<template>
  <Card class="flex flex-column align-items-center sm:align-items-start gap-3">
    <template #title>
      <!--TODO make title link (details view)-->
      <div class="flex text-base">
        {{ content.title }}
      </div> 
    </template>
    <template #content>
      <div class="w-8 mx-3 left-block">
        <Tag 
          class="mx-2" 
          value="STAC Collection" 
          severity="warning" 
        />
        <!-- TODO style keywords - make them clickable -->
        <span 
          v-for="keyword in content.keywords" :key="keyword" 
          class="mx-1">
          <Tag :value="keyword" />
        </span>
        <p ref="descriptionRef"
          align="left" 
          :class="showMore ? 'more-text' : 'less-text'"
          v-html="content.description">
        </p>
        <PButton 
          v-if="descriptionOverflow"
          :label="showMore ? 'Show less' : 'Show more'"
          link
          @click="showMoreClicked"
        />
      </div>
      <div class="w-3 right-block">
        <PButton 
          label="Request STAC items" 
          @click="submitStacItemQuery" 
          size="small" 
          severity="danger"
          :loading="stacItemsLoading"
          class="m-2" 
        />
        <PButton
          label="STAC Download Notebook" 
          @click="downloadSTACNotebook" 
          size="small" 
          severity="help" 
          class="m-2" 
        />
        <img class="thumbnail-img" 
          :src="content.assets.thumbnail.href"
        />
      </div>
      <div v-if="stacItemsPresent">
        <PButton 
          label="Show items" 
          @click="showItemsClick" 
          size="small" 
          :icon="showItems ? 'pi pi-angle-double-down' : 'pi pi-angle-double-right' " 
        />
        <DataView 
          v-if="showItems" 
          :value="currentlySelectedSTACItems" 
          :layout="'grid'" 
          :rows="12"
          :paginator="true" 
          class="h-full"
        >
          <template #grid="slotProps">
            <div class="col-12 p-2 w-3">
              <div class="p-2 border-1 surface-border surface-card border-round">
                <img 
                  v-if="slotProps.data.img_link" 
                  class="stac-item-img" 
                  :src="slotProps.data.img_link" 
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

  name: "STACCollectionComponent", 

  components: {
    Card,
    Tag,
    DataView
    }, 
  props: {
    content: Object, 
    globalSTACItems: Object, 
  }, 
  emits: ['submitStacItemQuery', 'downloadSTACNotebook'], 

  data() {
    return {
      showItems: false,
      showMore: false,
      descriptionOverflow: false, // is true when the description text overflows (computed at time of mount)
    }
  }, 

  computed: {
    stacItems() {
      // stacItems is a dictionary of STAC item requests performed on this STAC collection
      if (this.content._id in this.globalSTACItems) {
        return this.globalSTACItems[this.content._id];
      }
      else {
        return null;
      }
    },
    stacItemsLoading() {
      // returns true if any STAC items are loading
      if (this.stacItems !== null) {
        for (const entryUID in this.stacItems) {
          if (this.stacItems[entryUID].loading) {
            return true;
          }
        }
      }
      return false;
    }, 
    currentlySelectedResponse() {
      // returns the current response that is selected (if there is one)
      if (this.stacItems !== null) {
        for (const entryUID in this.stacItems) {
          if (this.stacItems[entryUID].selected) {
            return this.stacItems[entryUID];
          }
        }
      }
      return null;
    }, 
    currentlySelectedSTACItems() {
      // returns the STAC items that are currently selected
      if (this.currentlySelectedResponse !== null) {
        return this.currentlySelectedResponse.stac_items;
      }
      else {
        return [];
      }
    }, 
    stacItemsPresent() {
      // returns true if there are any STAC items selected
      if (this.currentlySelectedResponse !== null) {
        return true;
      }
      else {
        return false;
      }
    }
  }, 

  methods: {
    showMoreClicked() {
      this.showMore = !this.showMore;
    }, 
    submitStacItemQuery() {
      this.$emit('submitStacItemQuery', this.content._id);
    }, 
    showItemsClick() {
      this.showItems = !this.showItems;
    }, 
    downloadSTACNotebook() {
      this.$emit('downloadSTACNotebook', this.content._id);
    }, 
  }, 
  mounted() {
    // check if description text overflows the <p> element (with some margin)
    if (this.$refs.descriptionRef.scrollHeight > (this.$refs.descriptionRef.clientHeight + 5)) {
      this.descriptionOverflow = true;
    }
  }
}

</script>


<style scoped>

.thumbnail-img {
    width: 100%;
    height: auto;
    box-shadow: 2px;
    border-radius: 0.25rem;
}

.stac-item-img {
    width: 100%;
    height: auto;
    border-radius: 0.1rem;
    display: inline-block;
}


.left-block {
  width: 67%;
  vertical-align: top;
  display: inline-block;
}

.right-block {
  width: 33%;
  vertical-align: top;
  display: inline-block;
}

.less-text {
  /* display: block; */
  /* text-overflow: ellipsis; */
  /* word-wrap: break-word; */
  overflow: hidden;
  line-height: 1em;
  max-height: 20em;
}

.more-text {
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

</style>
