<template>
  <div class="w-full">
    <PToast 
      position="top-center" 
      group="tc" 
    />
    <div class="my-1">
      <span :class="queryIsLoading ? 'p-input-icon-right w-9' : 'p-input-icon-left w-9'">
        <i :class="queryIsLoading ? 'pi pi-spin pi-spinner' : 'pi pi-search'"></i>
        <InputText 
          v-model="userQuery" 
          v-on:keyup.enter="this.$emit('submitQuery', this.userQuery)" 
          type="text" 
          size="medium" 
          :placeholder="placeholder ? placeholder : 'Search'" 
          class="inline w-full" 
        />
      </span>
      <PButton 
        label="Submit" 
        icon="pi pi-search"
        icon-pos="left" 
        size="large"
        class="px-4 py-2 mx-2 w-1" 
        @click="this.$emit('submitQuery', this.userQuery)" 
      />
    </div>
    <div v-if="showAdvancedSearch" class="my-1">
      <div class="left-block">
        <div class="float-left filter-label font-bold m-2">
          <!-- <i class="pi pi-filter mx-1"></i> -->
          <label>Advanced Search:</label>
        </div>
        <AutoComplete 
          v-model="selectedKeywords"
          option-label="name"
          multiple
          :suggestions="filteredKeywords"
          @complete="searchKeywords"
          placeholder="Search for keywords..."
          class="w-full"
        />
        <AutoComplete 
          v-model="selectedAuthors"
          option-label="name"
          multiple
          :suggestions="filteredAuthors"
          @complete="searchAuthors"
          placeholder="Search for authors..."
          class="w-full"
        />
        <AutoComplete 
          v-model="selectedEONodes"
          option-label="name"
          multiple
          :suggestions="filteredEONodes"
          @complete="searchEONodes"
          placeholder="Search for EO Missions and Instruments..."
          class="w-full"
        />
      </div>
      <div class="right-block">
        <PButton
          @click="applyFilter"
          severity="info"
          label="Apply Filter"
          icon="pi pi-filter"
          icon-pos="left"
          size="large"
          class="mx-2 h-4rem"
        />
        <PButton
          @click="graphSearch"
          severity="warning"
          label="Graph Search"
          icon="pi pi-share-alt"
          icon-pos="left"
          size="large"
          class="mx-2 h-4rem"
        />
      </div>
    </div>
    <div v-if="showAdvancedSearchButton" class="center-x">
      <PButton 
        :icon="showAdvancedSearch ? 'pi pi-angle-double-up' : 'pi pi-angle-double-left' " 
        icon-pos="left"
        size="" 
        label="Advanced Search" 
        rounded 
        text 
        class="ml-2 text-xs" 
        @click="this.$emit('advancedSearchClick')" 
      />
    </div>
  </div>
</template>


<script>


export default {
  
  name: 'SearchHeaderComponent', 

  props: {
    queryIsLoading: Boolean, 
    showAdvancedSearch: Boolean, 
    showAdvancedSearchButton: Boolean,
    placeholder: String, 
    homeViewQuery: String, 
    keywords: Array, 
    authors: Array, 
    eoNodes: Array, 
  }, 

  emits: [
    'submitQuery', 
    'advancedSearchClick',
    'graphQuery', 
    'applyFilter', 
  ], 
  data() {
    return {
      userQuery: null, 
      selectedKeywords: [],
      filteredKeywords: null, 
      selectedAuthors: [], 
      filteredAuthors: null, 
      selectedEONodes: [], 
      filteredEONodes: null,
    }
  },

  methods: {
    searchKeywords(event) {
      setTimeout(() => {
        if (!event.query.trim().length) {
          this.filteredKeywords = [...this.keywords];
        } else {
          this.filteredKeywords = this.keywords.filter((keyword) => {
            return keyword.name.toLowerCase().startsWith(event.query.toLowerCase());
          });
        }
      }, 250);
    }, 
    searchAuthors(event) {
      setTimeout(() => {
        if (!event.query.trim().length) {
          this.filteredAuthors = [...this.authors];
        } else {
          this.filteredAuthors = this.authors.filter((author) => {
            return author.name.toLowerCase().startsWith(event.query.toLowerCase());
          });
        }
      }, 250);
    }, 
    searchEONodes(event) {
      setTimeout(() => {
        if (!event.query.trim().length) {
          this.filteredEONodes = [...this.eoNodes];
        } else {
          this.filteredEONodes = this.eoNodes.filter((eoNode) => {
            return eoNode.name.toLowerCase().startsWith(event.query.toLowerCase());
          });
        }
      }, 250);
    }, 
    graphSearch() {
      // search graph based on selected keywords
      if (this.selectedKeywords.length == 0 && this.selectedAuthors.length == 0 && this.selectedEONodes.length == 0) {
        this.$toast.add({
          severity: 'error', 
          summary: 'No Input', 
          detail: 'Please enter at least one keyword for the graph search', 
          life: 5000, 
          group: 'tc'
        });
        return;
      }
      this.$emit('graphQuery', this.selectedKeywords, this.selectedAuthors, this.selectedEONodes);
    }, 
    applyFilter() {
      this.$emit('applyFilter', this.selectedKeywords, this.selectedAuthors, this.selectedEONodes);
    }, 
  }, 
  watch: {
    homeViewQuery(newQuery) {
      this.userQuery = newQuery; 
    }, 
    // selectedKeywords: {
    //   handler() {
    //     this.userQuery = this.selectedKeywords.map(function(keyword) {
    //       return keyword.name;
    //     }).join(' ');

    //     // trigger filter
    //     this.applyFilter();
    //   }, 
    //   deep: true, 
    // }, 
    // selectedAuthors: {
    //   handler() {
    //     this.applyFilter();
    //   }, 
    //   deep: true, 
    // }, 
    // selectedEONodes: {
    //   handler() {
    //     this.applyFilter();
    //   }, 
    //   deep: true, 
    // }
  }
}

</script>


<style scoped>

.left-block {
  width: 50%;
  display: inline-block;
}

.right-block {
  display: inline-block;
}

.filter-label{
  color: white;
}

</style>