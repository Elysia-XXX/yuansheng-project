import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DatasetImportView from '../views/DatasetImportView.vue'
import DatasetSingleView from '../views/DatasetSingleView.vue'
import CustomerReviewsView from '../views/CustomerReviewsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/import',
      name: 'import',
      component: DatasetImportView,
    },
    {
      path: '/single',
      name: 'single',
      component: DatasetSingleView,
    },
    {
      path: '/reviews',
      name: 'reviews',
      component: CustomerReviewsView,
    },
  ],
})

export default router
