/**
 * Sistema de caché simple para optimizar llamadas a la API
 */

class SimpleCache {
  constructor(ttl = 60000) {
    // TTL por defecto: 60 segundos
    this.cache = new Map();
    this.ttl = ttl;
  }

  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
    });
  }

  get(key) {
    const item = this.cache.get(key);

    if (!item) return null;

    // Verificar si expiró
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  clear() {
    this.cache.clear();
  }

  delete(key) {
    this.cache.delete(key);
  }

  // Invalidar cache que contenga cierto patrón
  invalidatePattern(pattern) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

// Instancia global del caché
export const apiCache = new SimpleCache(30000); // 30 segundos

// Helper para generar keys de caché
export const getCacheKey = (url, params = {}) => {
  const paramString =
    Object.keys(params).length > 0 ? JSON.stringify(params) : "";
  return `${url}${paramString}`;
};

// Wrapper para axios con caché
export const cachedGet = async (axios, url, config = {}) => {
  const cacheKey = getCacheKey(url, config.params);

  // Intentar obtener del caché
  const cached = apiCache.get(cacheKey);
  if (cached) {
    console.log(`[Cache HIT] ${url}`);
    return { data: cached, fromCache: true };
  }

  // Si no está en caché, hacer la petición
  console.log(`[Cache MISS] ${url}`);
  const response = await axios.get(url, config);

  // Guardar en caché
  apiCache.set(cacheKey, response.data);

  return response;
};

// Invalidar caché después de mutaciones
export const invalidateCache = (pattern) => {
  apiCache.invalidatePattern(pattern);
};
