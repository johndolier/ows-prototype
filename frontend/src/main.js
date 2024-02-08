

import './assets/main.css'

import 'primeflex/primeflex.css'
// set default theme
// import "primevue/resources/themes/lara-light-indigo/theme.css";
import "primevue/resources/themes/lara-dark-purple/theme.css"
import 'primeicons/primeicons.css';
import '@vuepic/vue-datepicker/dist/main.css';


import { createApp } from 'vue'
import axios from 'axios'


import App from './App.vue'

const app = createApp(App)

// add vue datepicker component
import VueDatePicker from '@vuepic/vue-datepicker';
app.component('VueDatePicker', VueDatePicker);

// add primevue
import PrimeVue from 'primevue/config'
app.use(PrimeVue)

// add primevue components
import SelectButton from 'primevue/selectbutton';
import InputText from 'primevue/inputtext';
// import MultiSelect from 'primevue/multiselect';
import Button from 'primevue/button';
import SplitButton from 'primevue/splitbutton';

//import Splitter from 'primevue/splitter';
//import SplitterPanel from 'primevue/splitterpanel';
import OverlayPanel from 'primevue/overlaypanel';
import DataView from 'primevue/dataview';
import Dialog from 'primevue/dialog';
import Message from 'primevue/message';
import Toast from 'primevue/toast';
import Sidebar from 'primevue/sidebar';
import ConfirmDialog from 'primevue/confirmdialog';
import AutoComplete from 'primevue/autocomplete';
import Tag from 'primevue/tag';
import InputNumber from 'primevue/inputnumber';

app.component('SelectButton', SelectButton);
app.component('InputText', InputText);
app.component('PButton', Button);
app.component('SplitButton', SplitButton);
app.component('OverlayPanel', OverlayPanel);
app.component('DataView', DataView);
app.component('PDialog', Dialog);
app.component('PMessage', Message);
app.component('PToast', Toast);
app.component('PSidebar', Sidebar);
app.component('ConfirmDialog', ConfirmDialog);
app.component('AutoComplete', AutoComplete);
app.component('PTag', Tag);
app.component('InputNumber', InputNumber);

// add ToastService (Primevue) for notifications
// https://primevue.org/toast/
import ToastService from 'primevue/toastservice'; 
app.use(ToastService);
// add Confirmation Service 
// https://primevue.org/confirmdialog/
import ConfirmationService from 'primevue/confirmationservice';
app.use(ConfirmationService);

// add Tooltip
// https://primevue.org/tooltip/
import Tooltip from 'primevue/tooltip';
app.directive('tooltip', Tooltip);

// add DynamicDialog
// import DialogService from 'primevue/dialogservice';
// app.use(DialogService);


// `withCredentials` indicates whether or not cross-site Access-Control requests
// should be made using credentials (disable if FastAPI backend specified wildcard ('*') in CORS policy)
// enable if FastAPI backend specified list of URLs in CORS policy
axios.defaults.withCredentials = false;

// -> NOTE: setting BACKEND URL is now done dynamically in HomeView.vue (by setting variable in 'OWS-PROTOTYPE/frontend/.env')
// FastAPI backend
// const BACKEND_URL = "http://localhost:5000/"
// console.log(process.env.VUE_APP_BACKEND_URL);
// console.log("this is it");
// axios.defaults.baseURL = process.env.VUE_APP_BACKEND_URL; 


// disabled router; if enabled, uncomment these lines
// import router from './router'
// app.use(router);

// inject utils 
import HelperClass from './utils';
const Utils = new HelperClass();
app.provide('Utils', Utils);

app.mount('#app');

