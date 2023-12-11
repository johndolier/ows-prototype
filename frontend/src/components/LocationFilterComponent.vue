<template>
  <div class="w-full">
    <SelectButton 
      v-model="modeSelected" 
      :options="modeOptions" 
      aria-labelledby="basic"
      @click="modeButtonClicked" 
      class="w-full block float-left" 
    />
    <OverlayPanel ref="op">
      <div v-if="modeSelected=='Coordinates'">
        <p class="font-italic">Select coordinates (coming soon)</p>
      </div>
      <div v-else-if="modeSelected=='Location'">
        <InputText 
          v-model="locationInputText" 
          v-on:keyup.enter="submitLocationQuery" 
          type="text" 
          size="small" 
          placeholder="Search location..." 
          class="inline"
        />
        <PButton 
          icon="pi pi-search" 
          size="small" 
          @click="submitQuery"
          class="p-2 text-lg"
        />
      </div>
    </OverlayPanel>
    <div v-if="locationSelected">
      <!--- TODO DISPLAY SELECTED COORDINATES/LOCATION -->
    </div>
  </div>
</template>


<script>


export default {

  name: "LocationFilterComponent", 

  components: {},  
  emits: ['selectMapCoordinates'], 
  data () {
    return {
      modeSelected: [], 
      modeOptions: ['Coordinates', 'Location', 'Map'], 

      locationSelected: null,
    }
  }, 


  methods: {
    modeButtonClicked(event) {
      //console.log(this.modeSelected);
      if (this.modeSelected == 'Map') {
        // TODO call function to select area in MapComponent
        //console.log("TODO");
        //this.$refs.op.hide(event);
        //return;
        console.log("add toast");
        this.$emit('selectMapCoordinates');
        this.$refs.op.hide();
        return;
      } 
      this.$refs.op.show(event);
    }, 
  }

}

</script>
