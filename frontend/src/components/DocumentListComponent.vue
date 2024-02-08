
<template>
  <div>
    <SelectButton 
      v-if="allowSelection"
      v-model="typeSelected" 
      :options="typeOptions" 
      aria-labelledby="basic" 
      :allow-empty="false"
      class="w-full my-2" 
    />
    <div v-if="isTopResultsList"
      class="w-full"
    >
      <h3 class="inline-block text-white">
        {{ topResultString }}
      </h3>
      <PButton
        class="inline-block right-button"
        icon="pi pi-times-circle"
        severity="danger"
        link
        size="large"
        @click="this.$emit('closeDocumentList', this.typeSelected)"
      />
    </div>

    <div v-if="documentsPresent"> 
    <DataView
      :value="listDocuments" 
      :paginator="!isTopResultsList"
      :rows="10" 
      class="w-full overflow-y-auto"
    >
      <template #list="slotProps">
        <div class="col-12">
          <div class="flex flex-column document-element surface-border">
            <div class="flex flex-column flex-1">
              <div 
                v-if="slotProps.data[0] == 'publication'" 
                class="block w-full"
              >
                <PublicationComponent 
                  class="element-card" 
                  :content="slotProps.data[1]" 
                  :normal-style="!isTopResultsList"
                  @keyword-clicked="keywordClicked"
                  @author-clicked="authorClicked"
                />
              </div>
              <div v-else-if="slotProps.data[0] == 'web_document'">
                <WebDocumentComponent 
                  class="element-card" 
                  :content="slotProps.data[1]" 
                  @show-geodata="showGeodata"
                />
              </div>
              <div v-else-if="slotProps.data[0] == 'stac_collection'">
                <STACCollectionComponent 
                  class="element-card" 
                  :content="slotProps.data[1]" 
                  :globalSTACItems="stacItems"
                  :normal-style="!isTopResultsList"
                  @submitStacItemQuery="submitStacItemQueryHandler" 
                  @downloadSTACNotebook="downloadSTACNotebookHandler"
                  @stacItemClicked="stacItemClicked"
                  @showSTACItemsOnMap="showSTACItemsOnMap"
                  @showSpatialExtent="showSpatialExtent"
                  @keyword-clicked="keywordClicked"
                />
              </div>
              <div v-else-if="slotProps.data[0] == 'stac_item'">
                <STACItemComponent 
                  :content="slotProps.data[1]" 
                  class="element-card" 
                />
              </div>
            </div>
          </div>
        </div>
      </template>
    </DataView>
    </div>
    <div v-else>
      <p>{{foundNoQueryString}}</p>
    </div>
  </div>
</template>


<script>

import PublicationComponent from './PublicationComponent.vue';
import STACCollectionComponent from './STACCollectionComponent.vue';
import STACItemComponent from './STACItemComponent.vue';
import WebDocumentComponent from './WebDocumentComponent.vue';

export default {
  name: "DocumentListComponent", 
  components: {
    PublicationComponent, 
    STACCollectionComponent, 
    STACItemComponent, 
    WebDocumentComponent
  }, 
  props: {
    documents: Object,
    stacItems: Object,  
    initialDocumentType: String, 
    isTopResultsList: Boolean, // indicates whether this type of DocumentList only shows a specific set of "Top results", rather than having full functionality
    searchQuery: String, // indicates the search query that was used to generate the set of documents (relevant for isTopResultsList=true)
  }, 

  emits: [
    'submitStacItemQuery', 
    'downloadSTACNotebook',
    'closeDocumentList', 
    'stacItemClicked', 
    'showSTACItemsOnMap', 
    'showSpatialExtent', 
    'keywordClicked', 
    'showGeodata', 
    'authorClicked', 
  ], 

  data () {
    return {
      typeSelected: 'STAC Collections', 
      typeOptions: ['Web Documents', 'Publications', 'STAC Collections'], 
    }
  }, 

  computed: {
    allowSelection() {
      // selection is disabled when only showing top results
      return !this.isTopResultsList;
    }, 
    topResultString() {
      if (this.searchQuery == null) {
        return "Top " + this.typeSelected + " results";
      }
      return "Top " + this.typeSelected + " for '" + this.searchQuery + "'";
    }, 
    foundNoQueryString() {
      if (this.searchQuery == null) {
        return "No documents found. Please specify a query above";
      }
      return "No documents found :(";
    }, 
    listDocuments() {
      // parse all document types in single document list and sort by score value
      const documentList = [];
      if (this.typeSelected == 'STAC Collections') {
        for (const element of this.documents.stac_collections) {
          documentList.push(['stac_collection', element]);
        }
      }
      if (this.typeSelected == 'Web Documents') {
        for (const element of this.documents.web_documents) {
          documentList.push(['web_document', element]);
        }
      }
      if (this.typeSelected == 'Publications') { 
        for (const element of this.documents.publications) {
          documentList.push(['publication', element]);
        }
      }
      // TODO include Social media

      // sort list and limit view
      //const limitDoc = 10; // show only 10 documents for now
      documentList.sort(function(a,b) {
          return parseFloat(b[1].score) - parseFloat(a[1].score)
      });

      // limit document number if isTopResultsList is enabled
      const limit = 5;
      if (this.isTopResultsList && documentList.length > limit) {
        return documentList.slice(0,limit);
      }
      // otherwise, return whole list
      return documentList;
    }, 
    documentsPresent() {
      return (this.listDocuments.length > 0);
    }
  }, 

  methods: {
    submitStacItemQueryHandler(args) {
      this.$emit('submitStacItemQuery', args);
    }, 
    downloadSTACNotebookHandler(args) {
      this.$emit('downloadSTACNotebook', args);
    }, 
    stacItemClicked(stacCollectionID, requestUID, stacItemID) {
      this.$emit('stacItemClicked', stacCollectionID, requestUID, stacItemID);
    },
    showSTACItemsOnMap(stacCollectionID, requestUID) {
      this.$emit('showSTACItemsOnMap', stacCollectionID, requestUID);
    }, 
    showSpatialExtent(spatialExtent) {
      this.$emit('showSpatialExtent', spatialExtent);
    }, 
    keywordClicked(keyword) {
      this.$emit('keywordClicked', keyword);
    }, 
    showGeodata(location) {
      this.$emit('showGeodata', location);
    }, 
    authorClicked(author) {
      this.$emit('authorClicked', author);
    }, 
  }, 
  watch: {
    typeSelected() {
      if (!this.typeOptions.includes(this.typeSelected)) {
        // unknown type was specified
        console.log("warning - unknown type specified in DocumentList: " + this.typeSelected);
        // default typeSelected
        this.typeSelected = 'STAC Collections'; 
      }
    }, 
  }, 

  mounted() {
    // init typeSelected with initial document type specified in parent component (if specified)
    if (this.initialDocumentType != null) {
      this.typeSelected = this.initialDocumentType;
    }
  }
}

</script>

<style>

.document-element {
  border: 1px solid;
  border-radius: 5px;
  gap: 1.0rem !important;

}

</style>

