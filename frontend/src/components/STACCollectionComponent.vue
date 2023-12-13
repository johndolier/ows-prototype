<template>
  <Card>
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
        <Tag 
          v-if="spatialExtentCoversGlobe"
          class="m-1"
          value="Global"
          severity="info"
          v-tooltip="'STAC Collection covers the whole globe'"
          icon="pi pi-globe"
        />
        

        <p ref="descriptionRef"
          align="left" 
          :class="{'more-text' : showMore, 'less-text' : (!showMore && normalStyle), 'no-text': (!showMore && !normalStyle)}"
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
        <PButton v-if="normalStyle"
          label="Request STAC items" 
          @click="submitStacItemQuery" 
          icon="pi pi-cloud-download"
          icon-pos="right"
          size="small" 
          severity="danger"
          :loading="stacItemsLoading"
          class="w-3 m-1" 
        />
        <PButton v-if="normalStyle"
          label="STAC Notebook Download" 
          @click="downloadSTACNotebook" 
          icon="pi pi-download"
          icon-pos="right"
          size="small" 
          severity="help" 
          class="w-4 m-1" 
        />
        <PButton v-if="normalStyle"
          label="Show Spatial Extent"
          size="small"
          severity="info"
          icon="pi pi-map"
          icon-pos="right"
          class="w-3 m-1"
          @click="showSpatialExtent"
        />
        <img class="thumbnail-img" 
          :src="content.assets.thumbnail.href"
        />
      </div>
      <div v-if="stacItemsPresent">
        <div class="overflow-hidden">
          <PButton 
              class="items-button"
              :label="'Show items (#' + currentlySelectedSTACItems.length + ')'" 
              @click="showItemsClick" 
              :icon="showItems ? 'pi pi-angle-double-down' : 'pi pi-angle-double-right' " 
            />
            <PButton
              class="map-button"
              label="Show STAC Items on Map"
              icon="pi pi-map"
              @click="showSTACItemsOnMap"
            />
        </div>
        <DataView 
          v-if="showItems" 
          :value="currentlySelectedSTACItems" 
          :layout="'grid'" 
          :rows="12"
          :paginator="currentlySelectedSTACItems.length > 12" 
          class="h-full"
        >
          <template #grid="slotProps">
            <div class="col-12 p-2 w-3">
              <div 
                class="p-2"
                :class="{'highlight-border' : (slotProps.data.id == currentlyHighlightedSTACItemID)}"
                >
                <img 
                  v-if="slotProps.data.img_link" 
                  class="stac-item-img" 
                  :src="slotProps.data.img_link"
                  @click="onImageClick(slotProps.data)"
                  @dblclick="showSTACItemsOnMap"
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
    normalStyle: Boolean, // this flag controls styling (can either be "normal" (true) or "small" style (false))
  }, 
  emits: [
    'submitStacItemQuery', 
    'downloadSTACNotebook', 
    'stacItemClicked', 
    'showSTACItemsOnMap', 
    'showSpatialExtent', 
  ], 

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
      if (this.content._key in this.globalSTACItems) {
        return this.globalSTACItems[this.content._key];
      }
      else {
        return null;
      }
    },
    stacItemsLoading() {
      // returns true if any STAC items are loading
      if (this.stacItems !== null) {
        for (const requestUID in this.stacItems) {
          if (this.stacItems[requestUID].loading) {
            return true;
          }
        }
      }
      return false;
    }, 
    currentlySelectedRequestUID() {
      // returns the current request item that is selected (if there is one)
      if (this.stacItems !== null) {
        for (const requestUID in this.stacItems) {
          if (this.stacItems[requestUID].selected) {
            return requestUID;
          }
        }
      }
      return null;
    }, 
    currentlySelectedRequest() {
      if (this.currentlySelectedRequestUID == null) {
        return null;
      }
      return this.stacItems[this.currentlySelectedRequestUID];
    }, 
    currentlyHighlightedSTACItemID() {
      // returns the ID of the currently highlighted STAC item
      if (this.currentlySelectedRequest !== null) {
        return this.currentlySelectedRequest.highlightID;
      }
      else {
        return null;
      }
    },
    currentlySelectedSTACItems() {
      // returns the STAC items that are currently selected
      // transforms the dictionary of STAC items into an array
      let stacItems = [];
      if (this.currentlySelectedRequest !== null) {
        for (const stacItemID in this.currentlySelectedRequest.stacItems) {
          stacItems.push(this.currentlySelectedRequest.stacItems[stacItemID]);
        }
      }
      return stacItems;
    }, 
    stacItemsPresent() {
      // returns true if there are any STAC items selected
      if (this.currentlySelectedRequest !== null) {
        return true;
      }
      else {
        return false;
      }
    }, 
    spatialExtentCoversGlobe() {
      // returns true if a bbox which covers whole globe is found in spatial extent variable of STAC collection
      for (const bbox of this.content.extent.spatial.bbox) {
        // check if bbox covers the whole map
        if (bbox.includes(180) && bbox.includes(-180) && bbox.includes(-90) && bbox.includes(90)) {
          return true;
        }
      }
      return false;
    },
  }, 

  methods: {
    showMoreClicked() {
      this.showMore = !this.showMore;
    }, 
    submitStacItemQuery() {
      this.$emit('submitStacItemQuery', this.content._key);
    }, 
    showItemsClick() {
      this.showItems = !this.showItems;
    }, 
    downloadSTACNotebook() {
      this.$emit('downloadSTACNotebook', this.content._key);
    }, 
    onImageClick(stacItem) {
      const stacCollectionID = stacItem.collection;
      const stacItemID = stacItem.id;
      const requestUID = stacItem.requestUID;
      this.$emit('stacItemClicked', stacCollectionID, requestUID, stacItemID);
    },
    showSTACItemsOnMap() {
      const requestUID = this.currentlySelectedRequestUID;
      const stacCollectionID = this.content._key;
      this.$emit('showSTACItemsOnMap', stacCollectionID, requestUID);
    }, 
    showSpatialExtent() {
      // iterate over spatial extent bboxes and send event to MapView (show them in map)
      let filteredBBoxList = [];
      for (const bbox of this.content.extent.spatial.bbox) {
        if (bbox.includes(180) && bbox.includes(-180) && bbox.includes(-90) && bbox.includes(90)) {
          continue;
        }
        filteredBBoxList.push(bbox);
      }
      this.$emit('showSpatialExtent', filteredBBoxList);
    }
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

.highlight-border {
  border-width: 2px !important;
  border-style: solid !important;
  border-color: #FF0000 !important;
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

.no-text {
  overflow: hidden;
  line-height: 1em;
  max-height: 3em;
}
.less-text {
  overflow: hidden;
  line-height: 1em;
  max-height: 10em;
}

.more-text {
  overflow: hidden;
  line-height: 1em;
  height: auto;
}

.map-button {
  float: right;
  padding: 5px;
  margin: 3px;
}

.items-button {
  float: left;
  padding: 5px;
  margin: 3px;
}


</style>
