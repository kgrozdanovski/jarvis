import { computed } from 'vue';
import { useHead, useRoute, useSeoMeta } from '#imports';

const siteName = 'Jarvis';
const siteUrl = 'http://localhost:3000';
const siteDescription =
  'Jarvis is a local-network home AI assistant interface.';
const siteKeywords =
  'home ai assistant, local network assistant, private ai assistant, home automation assistant';
const ogImageUrl = `${siteUrl}/images/meta/og-image.png`;
const siteTitle = `${siteName} | Local Home AI Assistant`;

type RouteHeadMeta = {
  name?: string;
  property?: string;
  content?: string;
};

type RouteHead = {
  title?: string;
  meta?: RouteHeadMeta[];
};

const nonEmptyString = (value: unknown) =>
  typeof value === 'string' && value.trim().length > 0 ? value : undefined;

const routeUrl = (path: string) => `${siteUrl}${path === '/' ? '' : path}`;

/**
 * Single source of truth for all SEO meta tags.
 * Call from every layout to set defaults. Page-level useSeoMeta() calls can
 * still override individual fields; otherwise definePageMeta({ title }) and
 * definePageMeta({ description }) are used as route-level defaults.
 */
export const useDefaultSeo = () => {
  const route = useRoute();

  const routeHead = computed(() => route.meta.head as RouteHead | undefined);
  const title = computed(
    () => nonEmptyString(route.meta.title) ?? nonEmptyString(routeHead.value?.title) ?? siteTitle
  );
  const description = computed(
    () => nonEmptyString(route.meta.description) ?? siteDescription
  );
  const canonicalUrl = computed(() => routeUrl(route.path));

  useSeoMeta({
    title,
    description,
    ogTitle: title,
    ogDescription: description,
    ogType: 'website',
    ogUrl: canonicalUrl,
    ogSiteName: siteName,
    ogImage: ogImageUrl,
    twitterCard: 'summary_large_image',
    twitterTitle: title,
    twitterDescription: description,
    twitterImage: ogImageUrl,
  });

  useHead(() => ({
    link: [{ rel: 'canonical', href: canonicalUrl.value, key: 'canonical' }],
    meta: routeHead.value?.meta ?? []
  }));
};

export const buildSoftwareLdJson = () => ({
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: siteName,
  applicationCategory: 'UtilitiesApplication',
  operatingSystem: 'Web',
  description: siteDescription,
  image: ogImageUrl,
  url: siteUrl,
  offers: {
    '@type': 'Offer',
    availability: 'https://schema.org/InStock',
    priceCurrency: 'USD',
    price: '0'
  },
  featureList: [
    'Local-network assistant access',
    'Account-based authentication',
    'Home assistant workspace without payment workflows'
  ],
  publisher: {
    '@type': 'Organization',
    name: siteName,
    url: siteUrl
  }
});

export { siteName, siteUrl, siteDescription, siteKeywords, siteTitle, ogImageUrl };
