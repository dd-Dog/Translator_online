import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import History from '../views/History.vue'
import Glossary from '../views/Glossary.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/history',
    name: 'History',
    component: History
  },
  {
    path: '/glossary',
    name: 'Glossary',
    component: Glossary
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

