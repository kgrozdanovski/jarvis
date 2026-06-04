export default defineNuxtPlugin(() => {
  return {
    provide: {
      loadGis: () =>
        new Promise<void>((resolve, reject) => {
          if ((window as any).google?.accounts?.id) return resolve();
          const s = document.createElement("script");
          s.src = "https://accounts.google.com/gsi/client";
          s.async = true;
          s.defer = true;
          s.onload = () => resolve();
          s.onerror = () => reject(new Error("Failed to load GIS"));
          document.head.appendChild(s);
        }),
    },
  };
});
