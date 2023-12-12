
<template>
  <div v-if="documentsPresent">
  <SelectButton 
    v-model="typeSelected" 
    :options="typeOptions" 
    aria-labelledby="basic" 
    :allow-empty="false"
    class="w-full block float-left" 
  />
  <DataView 
    :value="listDocuments" 
    paginator :rows="10" 
    class="w-full overflow-y-auto h-full"
  >
    <template #list="slotProps">
      <div class="col-12">
        <div class="flex flex-column xl:flex-row xl:align-items-start p-4 gap-4">
          <div class="flex flex-column sm:flex-row justify-content-between align-items-center xl:align-items-start flex-1 gap-4">
            <div 
              v-if="slotProps.data[0] == 'publication'" 
              class="block w-full"
            >
              <PublicationComponent 
                class="element-card" 
                :content="slotProps.data[1]" 
              />
            </div>
            <div v-else-if="slotProps.data[0] == 'web_document'">
              <WebDocumentComponent 
                class="element-card" 
                :content="slotProps.data[1]" 
              />
            </div>
            <div v-else-if="slotProps.data[0] == 'stac_collection'">
              <STACCollectionComponent 
                :content="slotProps.data[1]" 
                :globalSTACItems="stacItems"
                @submitStacItemQuery="submitStacItemQueryHandler" 
                @downloadSTACNotebook="downloadSTACNotebookHandler"
                class="element-card" 
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
    <p>No documents present. Please enter query above</p>
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
    includeSTACCollections: Boolean, 
    includePubs: Boolean, 
    includeSTACItems: Boolean, 
    includeWebDocuments: Boolean, 
  }, 
  data () {
    return {
      typeSelected: 'STAC Collections', 
      typeOptions: ['Web Documents', 'Publications', 'STAC Collections'], 
    }
  }, 

  computed: {
    listDocuments() {
      // parse all document types in single document list and sort by score value
      // filter out types that are not selected
      const documentList = [];
      if (this.typeSelected.includes('STAC Collections')) {
        for (const element of this.documents.stac_collections) {
          documentList.push(['stac_collection', element]);
        }
      }
      if (this.typeSelected.includes('Web Documents')) {
        for (const element of this.documents.web_documents) {
          documentList.push(['web_document', element]);
        }
      }
      if (this.typeSelected.includes('Publications')) { 
        for (const element of this.documents.publications) {
          documentList.push(['publication', element]);
        }
      }
      // TODO include STAC items / Social media

      // sort list and limit view
      //const limitDoc = 10; // show only 10 documents for now#
      documentList.sort(function(a,b) {
          return parseFloat(b[1].score) - parseFloat(a[1].score)
      });
      // set documentsPresent variable
      
      return documentList;
    }, 
    documentsPresent() {
      return (this.listDocuments.length > 0);
    }
  }, 

  methods: {
    openLink(link) {
      console.log("open link...");
      console.log(link);
      window.open(link);
    }, 
    submitStacItemQueryHandler(args) {
      this.$emit('submitStacItemQuery', args);
    }, 
    downloadSTACNotebookHandler(args) {
      this.$emit('downloadSTACNotebook', args);
    }, 
  }, 
  }

</script>

