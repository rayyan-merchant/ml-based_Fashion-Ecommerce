import { articles, sections, categories } from '../api/api';
import recommendationAPI from '../api/recommendationAPI';

export const productsService = {
  list: ({ skip = 0, limit = 24, section = '', category = '', search = '', sort = 'popular' } = {}) =>
    articles.getCatalog({ skip, limit, section, category, search, sort }),
  get: (productId) => articles.getById(productId),
  search: ({ query, skip = 0, limit = 50 }) => articles.searchCatalog(query, skip, limit),
  listBySection: ({ section, limit = 24, offset = 0 }) =>
    articles.getCatalog({ section, limit, skip: offset }),
  listByCategory: ({ section, category, sort = 'popular', limit = 24, offset = 0 }) =>
    articles.getCatalog({ section, category, sort, limit, skip: offset }),
  filters: ({ section, category }) => sections.getFilterOptions(section, category),
  create: (payload) => articles.create(payload),
  update: (productId, payload) => articles.update(productId, payload),
  remove: (productId) => articles.delete(productId),
  similar: (productId, limit = 8) => recommendationAPI.getSimilarItems(productId, limit),
  categories: () => categories.getAll()
};

export default productsService;
