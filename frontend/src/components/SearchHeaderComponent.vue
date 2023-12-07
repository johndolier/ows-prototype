<template>
  <div class="w-full">
    <div>
      <span :class="queryIsLoading ? 'p-input-icon-right w-9' : 'p-input-icon-left w-9'">
        <i :class="queryIsLoading ? 'pi pi-spin pi-spinner' : 'pi pi-search'"></i>
        <InputText 
          v-model="userQuery" v-on:keyup.enter="this.$emit('submitQuery', this.userQuery)" 
          type="text" size="medium" :placeholder="startText ? startText : 'Search'" class="inline w-full">
        </InputText>
      </span>
      <PButton 
        label="Submit" @click="this.$emit('submitQuery', this.userQuery)" size="small" rounded class="inline w-1 mx-2 text-sm">
      </PButton>
    </div>
    <div class="center-x">
      <PButton 
        :icon="showAdvancedSearch ? 'pi pi-angle-double-down' : 'pi pi-angle-double-left' " 
        size="small" @click="this.$emit('advancedSearchClick')" label="Show advanced options" icon-pos="left"
        rounded text class="ml-2 text-xs">
      </PButton>
    </div>
  </div>
</template>


<script>


export default {
  name: 'SearchHeaderComponent', 

  props: {
    queryIsLoading: Boolean, 
    showAdvancedSearch: Boolean, 
    startText: String, 
  }, 

  emits: [
    'submitQuery', 
    'advancedSearchClick', 
  ], 
  data() {
    return {
      userQuery: null, 
    }
  }, 
}

</script>