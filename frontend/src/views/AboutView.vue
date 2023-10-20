<template>
  <div class="about">
    <h1>This is an about page</h1>
  </div>
  <div id="app">
    <!-- trigger event if enter is pressed -->
    <input type="text" v-model="searchText" v-on:keyup.enter="exampleReuqest" placeholder="Search...">
    <button type="button" v-on:click="exampleReuqest">Button</button>
    <div v-if="firstQuery">
      <div> Results will show here, after you submitted your query</div>
    </div>
    <div v-else>
      <div v-if="waitingForQuery">Loading...</div>
      <div v-else>
        <div>Result show here: </div>
        <div>{{ results }}</div>
      </div>
    </div>
  </div>
</template>


<script>
import axios from 'axios';

  export default {
    data() {
      return {
        searchText: "", 
        waitingForQuery: false,  
        firstQuery: true, 
        results: ""
      }
    }, 

    methods: {
      exampleReuqest() {
        this.waitingForQuery = true;
        this.firstQuery = false;
        const request = {};
        request.params = {
          query: this.searchText
        }
        axios.get('/reverse', request)
        .then((res) => {
          this.results = res.data;
          this.waitingForQuery = false;
        })
        .catch((error) => {
          console.error(error);
        });
      }
    }
  }
</script>

