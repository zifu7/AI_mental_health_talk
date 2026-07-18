import { ref, onBeforeUnmount } from 'vue'

export function useIntersectionObserver(callback, options = {}) {
  const targetRef = ref(null)
  let observer = null

  const startObserve = () => {
    if (!targetRef.value) return
    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        callback(entry.isIntersecting, entry)
      })
    }, {
      threshold: 0.1,   // 10% 露出即触发，可按需调整
      ...options
    })
    observer.observe(targetRef.value)
  }

  const stopObserve = () => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  onBeforeUnmount(stopObserve)

  return { targetRef, startObserve, stopObserve }
}