
<!-- 
  DISABLED ROUTER VIEW; IF ENABLED, USE THIS TEMPLATE INSTEAD  
<template>
  <router-view/>
</template> -->

<template>
  <HomeView />
</template>

<script>
import HomeView from './views/HomeView.vue';

export default {
  components: {
    HomeView, 
  }, 
}
</script>
