<template>
  <div class="w-full">
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
      <AutoComplete 
        v-model="selectedKeywords"
        multiple
        :suggestions="filteredKeywords"
        @complete="searchKeywords"
        placeholder="Add keyword..."
        class="w-9"
      />
      <PButton
        @click="keywordSearch"
        severity="warning"
        label="Graph Keyword Search"
        icon="pi pi-share-alt"
        icon-pos="left"
        class="mx-2 w-1"
      />
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
  }, 

  emits: [
    'submitQuery', 
    'advancedSearchClick',
    'graphKeywordQuery', 
  ], 
  data() {
    return {
      userQuery: null, 
      selectedKeywords: [],
      filteredKeywords: null, 
    }
  }, 
  methods: {
    searchKeywords(event) {
      setTimeout(() => {
        if (!event.query.trim().length) {
          this.filteredKeywords = [...this.keywords];
        } else {
          this.filteredKeywords = this.keywords.filter((keyword) => {
            return keyword.toLowerCase().startsWith(event.query.toLowerCase());
          });
        }
      }, 250);
    }, 
    keywordSearch() {
      // search graph based on selected keywords
      this.$emit('graphKeywordQuery', this.selectedKeywords);
    }, 
  }, 
  watch: {
    homeViewQuery(newQuery) {
      this.userQuery = newQuery; 
    }, 
    selectedKeywords: {
      handler() {
        this.userQuery = this.selectedKeywords.join(' ');
      }, 
      deep: true, 
    }, 
  }
}

</script>