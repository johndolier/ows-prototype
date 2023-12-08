

import './assets/main.css'

import 'primeflex/primeflex.css'
import "primevue/resources/themes/lara-light-indigo/theme.css";
import 'primeicons/primeicons.css';
import '@vuepic/vue-datepicker/dist/main.css';


import { createApp } from 'vue'
import axios from 'axios'


import App from './App.vue'
import router from './router'

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
import MultiSelect from 'primevue/multiselect';
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

app.component('SelectButton', SelectButton);
app.component('InputText', InputText);
app.component('MultiSelect', MultiSelect);
app.component('PButton', Button);
app.component('SplitButton', SplitButton);
//app.component('SplitterParent', Splitter);
//app.component('SplitterPanel', SplitterPanel);
app.component('OverlayPanel', OverlayPanel);
app.component('DataView', DataView);
app.component('PDialog', Dialog);
app.component('PMessage', Message);
app.component('PToast', Toast);
app.component('PSidebar', Sidebar);
app.component('ConfirmDialog', ConfirmDialog);


// add ToastService (Primevue) for notifications
// https://primevue.org/toast/
import ToastService from 'primevue/toastservice'; 
app.use(ToastService);
// add Confirmation Service 
// https://primevue.org/confirmdialog/
import ConfirmationService from 'primevue/confirmationservice';
app.use(ConfirmationService);


axios.defaults.withCredentials = true;
// FastAPI backend
const BACKEND_URL = "http://localhost:5000/"
axios.defaults.baseURL = BACKEND_URL; 
app.use(router);

// inject utils 
import HelperClass from './utils';
const Utils = new HelperClass();
app.provide('Utils', Utils);

app.mount('#app');

